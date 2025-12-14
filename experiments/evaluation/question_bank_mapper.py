"""
질문은행 메타데이터 매핑 헬퍼

required_fields -> required_slots 변환
update_key 추출
"""

from typing import Dict, List, Optional, Any


# Placeholder -> Slot 경로 매핑
PLACEHOLDER_TO_SLOT_MAP = {
    "AGE": "demographics.age",
    "SEX_KO": "demographics.gender",
    "COND1_KO": "conditions",
    "COND2_KO": "conditions",
    "MED1_KO": "medications",
    "MED2_KO": "medications",
    "ALLERGY_KO": "allergies",
    "CC": "symptoms",
    "DUR": None,  # DUR은 슬롯이 아님 (시간 정보)
    "TRIGGER": None,  # TRIGGER는 슬롯이 아님 (상황 정보)
    "ADD_SYM": "symptoms",
    "VITAL_NAME": None,  # VITAL_NAME은 슬롯 경로가 아님
    "VITAL_VALUE": None,  # VITAL_VALUE는 슬롯 경로가 아님
    "VITAL_UNIT": None,  # VITAL_UNIT은 슬롯 경로가 아님
    "LAB_NAME": None,  # LAB_NAME은 슬롯 경로가 아님
    "LAB_VALUE": None,  # LAB_VALUE는 슬롯 경로가 아님
    "LAB_UNIT": None,  # LAB_UNIT은 슬롯 경로가 아님
    "OTC": "medications",  # OTC는 약물로 간주
    "NEW_INFO": "symptoms",  # NEW_INFO는 증상으로 간주
}


def map_required_fields_to_slots(required_fields: List[str]) -> List[str]:
    """
    required_fields를 required_slots로 변환
    
    Args:
        required_fields: 질문은행의 required_fields (예: ["AGE", "SEX_KO", "COND1_KO"])
    
    Returns:
        required_slots: 슬롯 경로 리스트 (예: ["demographics.age", "demographics.gender", "conditions"])
    """
    slots = []
    for field in required_fields:
        slot_path = PLACEHOLDER_TO_SLOT_MAP.get(field)
        if slot_path and slot_path not in slots:
            slots.append(slot_path)
    return slots


def extract_update_key(question_item: Dict[str, Any], turn_id: int, question_text: Optional[str] = None) -> Optional[str]:
    """
    질문 항목에서 update_key 추출 (구체적인 이름 추출 지원)
    
    Turn 3 (update_new_evidence)의 경우:
    - LAB_NAME이 있으면 "labs" 또는 "labs.hba1c" 반환
    - VITAL_NAME이 있으면 "vitals" 또는 "vitals.sbp" 반환
    
    Args:
        question_item: 질문은행 항목
        turn_id: 턴 번호
        question_text: 질문 텍스트 (선택적, 구체적인 이름 추출용)
    
    Returns:
        update_key (예: "labs", "labs.hba1c", "vitals", "vitals.sbp", "medications") 또는 None
    """
    # Turn 3은 update_new_evidence
    if turn_id == 3:
        required_fields = question_item.get("required_fields", [])
        
        # LAB_NAME이 있으면 labs 업데이트
        if "LAB_NAME" in required_fields:
            if question_text:
                # 구체적인 lab_name 추출 시도
                try:
                    from .extract_update_key_from_question import extract_specific_update_key
                    specific_key = extract_specific_update_key(question_text, "labs")
                    if specific_key:
                        return specific_key
                except ImportError:
                    pass
            return "labs"  # 구체적인 lab_name을 추출할 수 없으면 카테고리만 반환
        
        # VITAL_NAME이 있으면 vitals 업데이트
        if "VITAL_NAME" in required_fields:
            if question_text:
                # 구체적인 vital_name 추출 시도
                try:
                    from .extract_update_key_from_question import extract_specific_update_key
                    specific_key = extract_specific_update_key(question_text, "vitals")
                    if specific_key:
                        return specific_key
                except ImportError:
                    pass
            return "vitals"
    
    # Turn 4는 near_duplicate_plus_minor_addition (OTC 추가)
    if turn_id == 4:
        required_fields = question_item.get("required_fields", [])
        if "OTC" in required_fields:
            return "medications"  # OTC는 약물로 간주
    
    # Turn 5는 personalized_plan_and_safety_net (일반적으로 업데이트 없음)
    # Turn 1, 2는 업데이트 없음
    
    return None


def get_question_metadata(question_item: Dict[str, Any], question_text: Optional[str] = None) -> Dict[str, Any]:
    """
    질문 항목에서 평가에 필요한 메타데이터 추출
    
    Args:
        question_item: 질문은행 항목
        question_text: 질문 텍스트 (선택적, 구체적인 update_key 추출용)
    
    Returns:
        {
            "required_slots": ["demographics.age", "demographics.gender", ...],
            "update_key": "labs.hba1c" 또는 None,
            "turn_id": 1,
            "intent": "profile_ingestion",
        }
    """
    required_fields = question_item.get("required_fields", [])
    turn_id = question_item.get("turn_id", 1)
    
    return {
        "required_slots": map_required_fields_to_slots(required_fields),
        "update_key": extract_update_key(question_item, turn_id, question_text),
        "turn_id": turn_id,
        "intent": question_item.get("intent", ""),
    }

