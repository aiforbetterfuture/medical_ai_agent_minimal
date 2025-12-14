"""
멀티턴 컨텍스트 평가 지표 계산 모듈

2층 지표 (멀티턴 컨텍스트 전용):
- CUS (Context Utilization Score): required_slots를 답변에서 사용했는가?
- UR (Update Responsiveness): 새로 들어온 update_key가 답변에 반영되었는가?
- CCR (Context Contradiction Rate): 이전 턴 정보와 모순되는가?
"""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _norm(s: str) -> str:
    """텍스트 정규화 (소문자, 공백 제거)"""
    return (s or "").lower().strip()


def _resolve_nested(obj: Dict[str, Any], path: str) -> Any:
    """중첩된 딕셔너리 경로 해결 (예: "labs.hba1c")"""
    cur: Any = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _value_in_answer(value: Any, answer: str, use_synonyms: bool = True) -> bool:
    """
    답변에 값이 포함되어 있는지 확인 (동의어 지원)
    
    Args:
        value: 확인할 값 (숫자, 문자열, 리스트 등)
        answer: 답변 텍스트
        use_synonyms: 동의어 사전 사용 여부 (기본값: True)
    
    Returns:
        값이 답변에 포함되어 있으면 True
    """
    a = _norm(answer)
    if value is None:
        return False
    
    # 숫자: 정확한 숫자 문자열이 나타나는지 확인
    if isinstance(value, (int, float)):
        val_str = str(value)
        # 정확한 숫자 매칭 (예: "5.98" in "HbA1c 5.98%")
        if val_str in a:
            return True
        # 소수점 제거 버전도 확인 (예: "5.98" -> "598" in "HbA1c 598%")
        if "." in val_str:
            val_no_dot = val_str.replace(".", "")
            if val_no_dot in a:
                return True
        return False
    
    # 문자열: 부분 문자열 매칭
    v = _norm(str(value))
    if not v:
        return False
    
    # 기본 부분 문자열 매칭
    if v in a:
        return True
    
    # 동의어 사전 사용
    if use_synonyms:
        try:
            from .slot_synonyms import find_term_in_text
            return find_term_in_text(v, answer)
        except ImportError:
            # 동의어 모듈이 없으면 기본 매칭만 사용
            pass
    
    return False


def compute_cus(
    answer: str,
    required_slots: List[str],
    patient_profile: Dict[str, Any],
    slots_state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    CUS (Context Utilization Score) 계산
    
    질문이 요구하는 required_slots 중 답변이 실제로 반영했는가?
    
    Args:
        answer: 생성된 답변 텍스트
        required_slots: 질문이 요구하는 슬롯 리스트 (예: ["age", "sex", "conditions", "medications", "labs.hba1c"])
        patient_profile: 환자 프로필 (ground truth, patient_list_80.json에서)
        slots_state: 현재 슬롯 상태 (ProfileStore에서 추출)
    
    Returns:
        {
            "metric": "CUS",
            "score": 0.0~1.0,
            "hits": 사용한 슬롯 개수,
            "total": 전체 슬롯 개수,
            "used_detail": {slot: {"value": ..., "used": bool}}
        }
    """
    used = {}
    total = max(1, len(required_slots))
    hits = 0
    
    for slot in required_slots:
        # 슬롯 값 해결: slots_state 우선, 없으면 patient_profile
        val = _resolve_nested(slots_state, slot)
        if val is None:
            val = _resolve_nested(patient_profile, slot)
        
        # 슬롯별 사용 여부 확인
        ok = _slot_used(slot, val, answer)
        used[slot] = {"value": val, "used": ok}
        if ok:
            hits += 1
    
    return {
        "metric": "CUS",
        "score": hits / total,
        "hits": hits,
        "total": total,
        "used_detail": used,
    }


def _slot_used(slot: str, val: Any, answer: str) -> bool:
    """
    슬롯별 사용 여부 확인 (슬롯 타입별 휴리스틱)
    
    Args:
        slot: 슬롯 경로 (예: "age", "conditions", "labs.hba1c")
        val: 슬롯 값
        answer: 답변 텍스트
    
    Returns:
        슬롯이 답변에 사용되었으면 True
    """
    a = (answer or "").lower()
    
    if val is None:
        return False
    
    # 리스트 슬롯: conditions, symptoms, medications
    if isinstance(val, list):
        # 리스트의 어떤 요소라도 나타나면 사용된 것으로 간주
        for x in val:
            if isinstance(x, dict):
                # 딕셔너리인 경우 'name' 키 확인
                name = x.get('name') or x.get('value')
                if name and _value_in_answer(name, answer):
                    return True
            elif _value_in_answer(x, answer):
                return True
        return False
    
    # 나이 슬롯: "65세", "65 살", "65-year" 등 패턴 허용
    if slot.endswith("age") or slot == "age":
        if isinstance(val, (int, float, str)):
            m = str(val)
            if m.isdigit():
                # 정확한 숫자 매칭
                if m in a:
                    return True
                # "65세", "65 살", "65-year" 패턴
                if re.search(rf"\b{m}\s*(세|살|years?)\b", a):
                    return True
        return _value_in_answer(val, answer)
    
    # 성별 슬롯: "male/female/남성/여성" 등
    if slot.endswith("sex") or slot.endswith("gender") or slot == "sex" or slot == "gender":
        s = str(val).lower()
        # 남성
        if s in ["m", "male", "man", "남", "남성", "남자"]:
            return any(k in a for k in ["male", "man", "남성", "남자", "남"])
        # 여성
        if s in ["f", "female", "woman", "여", "여성", "여자"]:
            return any(k in a for k in ["female", "woman", "여성", "여자", "여"])
        return _value_in_answer(val, answer)
    
    # labs/vitals 슬롯: 중첩 경로 (예: "labs.hba1c")
    if "." in slot:
        # 중첩된 값은 숫자나 문자열로 처리
        if isinstance(val, (int, float)):
            return _value_in_answer(val, answer)
        elif isinstance(val, dict):
            # 딕셔너리인 경우 'value' 또는 'name' 확인
            val_str = str(val.get('value') or val.get('name') or val)
            return _value_in_answer(val_str, answer)
        else:
            return _value_in_answer(val, answer)
    
    # 기본: 직접 부분 문자열 매칭
    return _value_in_answer(val, answer)


def compute_ur(
    answer: str,
    update_key: Optional[str],
    turn_updates: Dict[str, Any],
    question_text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    UR (Update Responsiveness) 계산
    
    특정 turn에 새로 입력된 update_key가 답변에 우선 반영되었는가?
    
    Args:
        answer: 생성된 답변 텍스트
        update_key: 질문은행에서 정의한 업데이트 키 (예: "labs", "vitals", "medications")
        turn_updates: 이번 턴에 새로 들어온 정보 (slots_state에서 추출)
        question_text: 질문 텍스트 (선택적, update_key가 "labs"나 "vitals"인 경우 구체적인 이름 추출용)
    
    Returns:
        {
            "metric": "UR",
            "applicable": bool (update_key가 있는지),
            "score": 0.0 또는 1.0 (반영되었으면 1.0),
            "update_key": update_key,
            "update_value": 업데이트 값,
            "reflected": bool
        }
    """
    if not update_key:
        return {
            "metric": "UR",
            "applicable": False,
            "score": None,
            "update_key": None,
            "update_value": None,
            "notes": "no update_key in question bank",
        }
    
    # update_key가 "labs"나 "vitals"인 경우, turn_updates에서 해당 카테고리의 모든 업데이트 확인
    if update_key in ["labs", "vitals", "medications", "symptoms"]:
        updates_in_category = turn_updates.get(update_key, {})
        if not updates_in_category:
            return {
                "metric": "UR",
                "applicable": False,
                "score": None,
                "update_key": update_key,
                "update_value": None,
                "notes": "no update found for this category",
            }
        
        # 카테고리 내의 모든 업데이트가 답변에 반영되었는지 확인
        reflected_count = 0
        total_count = 0
        reflected_items = []
        
        for item_name, item_data in updates_in_category.items():
            total_count += 1
            # item_data가 딕셔너리인 경우 'value' 또는 'name' 확인
            if isinstance(item_data, dict):
                val = item_data.get('value') or item_data.get('name')
            else:
                val = item_data
            
            if _value_in_answer(val, answer):
                reflected_count += 1
                reflected_items.append(item_name)
        
        # 카테고리 내의 모든 업데이트가 반영되었으면 1.0, 일부만 반영되었으면 비율
        score = reflected_count / total_count if total_count > 0 else 0.0
        
        return {
            "metric": "UR",
            "applicable": True,
            "score": score,
            "update_key": update_key,
            "update_value": updates_in_category,
            "reflected": reflected_count > 0,
            "reflected_items": reflected_items,
            "total_items": total_count,
        }
    
    # 중첩된 경로 (예: "labs.hba1c")는 기존 로직 사용
    val = _resolve_nested(turn_updates, update_key)
    if val is None:
        return {
            "metric": "UR",
            "applicable": False,
            "score": None,
            "update_key": update_key,
            "update_value": None,
            "notes": "no update found for this key",
        }
    
    a = (answer or "").lower()
    reflected = False
    
    # 숫자: 정확한 숫자 문자열이 나타나는지 확인
    if isinstance(val, (int, float)):
        val_str = str(val)
        # 정확한 숫자 매칭
        if val_str in a:
            reflected = True
        # 소수점 제거 버전도 확인 (예: "5.98" -> "598")
        elif "." in val_str:
            val_no_dot = val_str.replace(".", "")
            if val_no_dot in a:
                reflected = True
    # 딕셔너리: 'value' 또는 'name' 키 확인
    elif isinstance(val, dict):
        val_str = str(val.get('value') or val.get('name') or val)
        reflected = _value_in_answer(val_str, answer)
    # 문자열: 부분 문자열 매칭
    else:
        v = str(val).lower().strip()
        if v and v in a:
            reflected = True
    
    return {
        "metric": "UR",
        "applicable": True,
        "score": 1.0 if reflected else 0.0,
        "update_key": update_key,
        "update_value": val,
        "reflected": reflected,
    }


def ccr_rule_checks(
    answer: str,
    slots_state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    CCR (Context Contradiction Rate) 계산 (룰 기반)
    
    답변이 이전 턴까지 축적된 환자 정보(슬롯)와 모순되는가?
    
    현재는 명백한 모순만 체크 (의학적 지식 기반 모순은 LLM Judge 필요)
    
    Args:
        answer: 생성된 답변 텍스트
        slots_state: 현재 슬롯 상태 (이전 턴까지 축적된 정보)
    
    Returns:
        {
            "metric": "CCR_rule_obvious",
            "has_contradiction": bool,
            "contradictions": [모순 항목 리스트],
            "score": 1.0 (모순 있음) 또는 0.0 (모순 없음)
        }
    """
    a = (answer or "").lower()
    contrad: List[str] = []
    
    # 성별 모순 체크
    sex = slots_state.get("sex") or slots_state.get("gender")
    if sex:
        s = str(sex).lower()
        # 남성인데 임신 언급
        if s in ["m", "male", "남", "남성", "남자"]:
            if any(k in a for k in ["임신", "pregnant", "임신부", "임신 중"]):
                contrad.append("sex: male but pregnancy mentioned")
        # 여성인데 전립선 언급
        if s in ["f", "female", "여", "여성", "여자"]:
            if any(k in a for k in ["전립선", "prostate", "전립선암"]):
                contrad.append("sex: female but prostate mentioned")
    
    # 질환 모순 체크 (매우 단순한 룰)
    conditions = slots_state.get("conditions") or []
    if isinstance(conditions, list):
        # 당뇨가 있는데 "당뇨가 아니다"라고 부정
        has_diabetes = any(
            "당뇨" in str(c) or "diabetes" in str(c).lower() 
            for c in conditions
            if isinstance(c, (str, dict))
        )
        if has_diabetes:
            if any(neg in a for neg in ["당뇨가 아닙", "당뇨는 없", "no diabetes", "not diabetic", "당뇨 아님"]):
                contrad.append("conditions: diabetes present but answer denies it")
    
    # 약물 모순 체크 (매우 단순한 룰)
    medications = slots_state.get("medications") or []
    if isinstance(medications, list):
        # 메트포르민 복용 중인데 "메트포르민을 복용하지 않는다"고 부정
        has_metformin = any(
            "메트포르민" in str(m) or "metformin" in str(m).lower()
            for m in medications
            if isinstance(m, (str, dict))
        )
        if has_metformin:
            if any(neg in a for neg in ["메트포르민을 복용하지 않", "metformin을 안 먹", "not taking metformin"]):
                contrad.append("medications: metformin present but answer denies it")
    
    return {
        "metric": "CCR_rule_obvious",
        "has_contradiction": len(contrad) > 0,
        "contradictions": contrad,
        "score": 1.0 if len(contrad) > 0 else 0.0,  # CCR은 1=모순 있음
    }


def ccr_llm_payload(
    question: str,
    answer: str,
    slots_state: Dict[str, Any],
    turn_updates: Dict[str, Any],
) -> Dict[str, Any]:
    """
    CCR LLM Judge 페이로드 생성
    
    의학적 모순 판정을 위한 LLM Judge 호출용 페이로드
    
    Args:
        question: 사용자 질문
        answer: 생성된 답변
        slots_state: 현재 슬롯 상태
        turn_updates: 이번 턴 업데이트
    
    Returns:
        LLM Judge 호출용 페이로드
    """
    return {
        "system": (
            "You are a strict medical consistency evaluator. "
            "Determine whether the answer contradicts the patient's known context. "
            "Return ONLY valid JSON matching the schema."
        ),
        "user": f"""[QUESTION]
{question}

[ANSWER]
{answer}

[KNOWN_CONTEXT_SLOTS]
{slots_state}

[TURN_UPDATES]
{turn_updates}

[JSON_SCHEMA]
{{
  "has_contradiction": "boolean",
  "contradiction_items": [
    {{
      "slot": "string",
      "expected": "string",
      "answer_fragment": "string",
      "severity": "low|medium|high"
    }}
  ],
  "notes": "string"
}}
""",
        "temperature": 0.0,
    }


def extract_slots_state_from_profile_store(profile_store: Any) -> Dict[str, Any]:
    """
    ProfileStore에서 슬롯 상태 추출
    
    Args:
        profile_store: ProfileStore 인스턴스
    
    Returns:
        슬롯 상태 딕셔너리
        {
            "demographics": {"age": 65, "gender": "남성"},
            "conditions": [{"name": "당뇨병", ...}],
            "medications": [{"name": "메트포르민", ...}],
            "symptoms": [...],
            "vitals": [...],
            "labs": [...]
        }
    """
    if profile_store is None:
        return {}
    
    try:
        slots = {
            "demographics": dict(profile_store.ltm.demographics) if hasattr(profile_store, 'ltm') else {},
            "conditions": [],
            "medications": [],
            "symptoms": [],
            "vitals": [],
            "labs": [],
        }
        
        if hasattr(profile_store, 'ltm'):
            # Conditions
            for cond in profile_store.ltm.conditions:
                slots["conditions"].append({
                    "name": cond.name,
                    "cui": cond.cui if hasattr(cond, 'cui') else None,
                })
            
            # Medications
            for med in profile_store.ltm.meds:
                slots["medications"].append({
                    "name": med.name,
                    "cui": med.cui if hasattr(med, 'cui') else None,
                    "dose": med.dose if hasattr(med, 'dose') else None,
                })
            
            # Symptoms
            for symp in profile_store.ltm.symptoms:
                slots["symptoms"].append({
                    "name": symp.name,
                    "negated": symp.negated if hasattr(symp, 'negated') else False,
                    "cui": symp.cui if hasattr(symp, 'cui') else None,
                })
            
            # Vitals
            for vital in profile_store.ltm.vitals:
                slots["vitals"].append({
                    "name": vital.name,
                    "value": vital.value if hasattr(vital, 'value') else None,
                    "unit": vital.unit if hasattr(vital, 'unit') else None,
                })
            
            # Labs
            for lab in profile_store.ltm.labs:
                slots["labs"].append({
                    "name": lab.name,
                    "value": lab.value if hasattr(lab, 'value') else None,
                    "unit": lab.unit if hasattr(lab, 'unit') else None,
                })
        
        return slots
    except Exception as e:
        logger.warning(f"ProfileStore에서 슬롯 상태 추출 실패: {e}")
        return {}


def extract_turn_updates(
    current_slots: Dict[str, Any],
    previous_slots: Dict[str, Any],
) -> Dict[str, Any]:
    """
    이번 턴에 새로 추가된 업데이트 추출
    
    Args:
        current_slots: 현재 턴 슬롯 상태
        previous_slots: 이전 턴 슬롯 상태
    
    Returns:
        이번 턴에 새로 추가된 업데이트
        {
            "labs": {"hba1c": {"value": 5.98, "unit": "%"}},
            "vitals": {"sbp": {"value": 140, "unit": "mmHg"}},
            ...
        }
    """
    updates = {}
    
    # Labs 업데이트
    current_labs = {lab.get('name', '').lower(): lab for lab in current_slots.get('labs', [])}
    previous_labs = {lab.get('name', '').lower(): lab for lab in previous_slots.get('labs', [])}
    
    for lab_name, lab_data in current_labs.items():
        if lab_name not in previous_labs:
            # 새로 추가된 lab
            if 'labs' not in updates:
                updates['labs'] = {}
            updates['labs'][lab_name] = lab_data
    
    # Vitals 업데이트
    current_vitals = {vital.get('name', '').lower(): vital for vital in current_slots.get('vitals', [])}
    previous_vitals = {vital.get('name', '').lower(): vital for vital in previous_slots.get('vitals', [])}
    
    for vital_name, vital_data in current_vitals.items():
        if vital_name not in previous_vitals:
            # 새로 추가된 vital
            if 'vitals' not in updates:
                updates['vitals'] = {}
            updates['vitals'][vital_name] = vital_data
    
    # Symptoms 업데이트
    current_symptoms = {symp.get('name', '').lower(): symp for symp in current_slots.get('symptoms', [])}
    previous_symptoms = {symp.get('name', '').lower(): symp for symp in previous_slots.get('symptoms', [])}
    
    for symp_name, symp_data in current_symptoms.items():
        if symp_name not in previous_symptoms:
            # 새로 추가된 symptom
            if 'symptoms' not in updates:
                updates['symptoms'] = {}
            updates['symptoms'][symp_name] = symp_data
    
    return updates

