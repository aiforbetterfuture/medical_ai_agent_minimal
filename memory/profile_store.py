"""
프로필 저장소
- 슬롯 메모리 관리
- 시계열 가중치 적용
- 자동 승인 메커니즘
"""

import time
from typing import Dict, Any, List, Optional
from .schema import Profile, Condition, Symptom, ValueWithUnit, Medication


def _to_float(x) -> Optional[float]:
    """안전한 float 변환"""
    try:
        return float(x)
    except:
        return None


def _dedup(seq, key=lambda x: x):
    """리스트 중복 제거"""
    seen = set()
    out = []
    for s in seq:
        k = key(s)
        if k in seen:
            continue
        seen.add(k)
        out.append(s)
    return out


class ProfileStore:
    """
    프로필 저장소
    
    환자의 의학 정보를 구조화하여 저장하고 관리합니다.
    """
    
    def __init__(self):
        """초기화"""
        self.ltm: Profile = Profile()  # Long-term memory
    
    def update_slots(self, slots: Dict[str, Any]) -> None:
        """
        슬롯 정보 업데이트
        
        Args:
            slots: 추출된 슬롯 정보
        """
        timestamp = time.time()
        
        # 인구통계학적 정보
        if 'demographics' in slots:
            self.ltm.demographics.update(slots['demographics'])
        
        # 질환
        for cond_data in slots.get('conditions', []):
            condition = Condition(
                name=cond_data.get('name', ''),
                cui=cond_data.get('cui', ''),
                confirmed=True,
                timestamp=timestamp
            )
            self.ltm.conditions.append(condition)
        
        # 증상
        for symp_data in slots.get('symptoms', []):
            symptom = Symptom(
                name=symp_data.get('name', ''),
                negated=symp_data.get('negated', False),
                cui=symp_data.get('cui', ''),
                timestamp=timestamp
            )
            self.ltm.symptoms.append(symptom)
        
        # 수치 (vitals)
        for vital_data in slots.get('vitals', []):
            vital = ValueWithUnit(
                name=vital_data.get('name', ''),
                value=_to_float(vital_data.get('value', 0)) or 0.0,
                unit=vital_data.get('unit', ''),
                timestamp=timestamp
            )
            self.ltm.vitals.append(vital)
        
        # 수치 (labs)
        for lab_data in slots.get('labs', []):
            lab = ValueWithUnit(
                name=lab_data.get('name', ''),
                value=_to_float(lab_data.get('value', 0)) or 0.0,
                unit=lab_data.get('unit', ''),
                timestamp=timestamp
            )
            self.ltm.labs.append(lab)
        
        # 약물
        for med_data in slots.get('medications', []):
            medication = Medication(
                name=med_data.get('name', ''),
                cui=med_data.get('cui', ''),
                dose=med_data.get('dosage', None),
                timestamp=timestamp
            )
            self.ltm.meds.append(medication)
        
        # 중복 제거
        self._deduplicate()
    
    def _deduplicate(self):
        """중복 제거"""
        self.ltm.conditions = _dedup(self.ltm.conditions, key=lambda x: x.name)
        self.ltm.symptoms = _dedup(self.ltm.symptoms, key=lambda x: (x.name, x.negated))
        self.ltm.vitals = _dedup(self.ltm.vitals, key=lambda x: (x.name, x.value, x.unit))
        self.ltm.labs = _dedup(self.ltm.labs, key=lambda x: (x.name, x.value, x.unit))
        self.ltm.meds = _dedup(self.ltm.meds, key=lambda x: x.name)
    
    def apply_temporal_weights(self, decay_factor: float = 0.9) -> None:
        """
        시계열 가중치 적용
        
        최신 정보에 더 높은 가중치를 부여합니다.
        
        Args:
            decay_factor: 시간 감쇠 계수 (0~1)
        """
        current_time = time.time()
        
        # 최신 정보를 앞으로 정렬 (가장 최근이 첫 번째)
        self.ltm.vitals.sort(key=lambda x: x.timestamp or 0, reverse=True)
        self.ltm.labs.sort(key=lambda x: x.timestamp or 0, reverse=True)
    
    def get_profile_summary(self) -> str:
        """
        프로필 요약 생성 (최적화된 버전)
        
        Returns:
            프로필 요약 텍스트
        """
        cond = ", ".join({c.name for c in self.ltm.conditions if c.name}) or "(없음)"
        
        # 최신 수치 추출 (딕셔너리 인덱싱으로 최적화)
        vitals_dict = {}
        for v in reversed(self.ltm.vitals):
            name_upper = str(v.name).upper()
            if name_upper not in vitals_dict:
                vitals_dict[name_upper] = v
        
        sbp = vitals_dict.get("SBP")
        dbp = vitals_dict.get("DBP")
        bp = f"SBP {sbp.value:.0f}/{dbp.value:.0f} mmHg" if (sbp and dbp) else ""
        
        labs_dict = {}
        for l in reversed(self.ltm.labs):
            name_upper = str(l.name).upper()
            if name_upper not in labs_dict:
                labs_dict[name_upper] = l
        
        a1c = labs_dict.get("A1C")
        fpg = labs_dict.get("FPG")
        
        labs = []
        if bp:
            labs.append(bp)
        if fpg:
            labs.append(f"FPG {fpg.value:.0f} mg/dL")
        if a1c:
            labs.append(f"A1c {a1c.value:.1f}%")
        
        lab_txt = " · ".join(labs) if labs else "(최근 수치 없음)"
        
        # 인구통계학적 정보
        age = self.ltm.demographics.get('age', '')
        gender = self.ltm.demographics.get('gender', '')
        demo = f"{age}세 {gender}" if age and gender else ""
        
        return "\n".join([
            "### 환자 정보",
            f"- **인구통계:** {demo}" if demo else "",
            f"- **진단:** {cond}",
            f"- **최근 수치:** {lab_txt}",
        ])
    
    def dump_summary(self) -> str:
        """프로필 요약 (별칭)"""
        return self.get_profile_summary()

