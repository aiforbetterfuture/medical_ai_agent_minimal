"""
슬롯 매핑 동의어 사전

의학 용어 동의어를 관리하여 슬롯 매핑 정확도 향상
"""

from typing import Dict, List, Set

# 의학 용어 동의어 사전
MEDICAL_SYNONYMS: Dict[str, List[str]] = {
    # 당뇨병
    "당뇨병": ["diabetes", "diabetes mellitus", "당뇨", "제2형 당뇨병", "type 2 diabetes"],
    "diabetes": ["당뇨병", "당뇨", "diabetes mellitus", "제2형 당뇨병"],
    
    # 고혈압
    "고혈압": ["hypertension", "high blood pressure", "혈압 상승"],
    "hypertension": ["고혈압", "high blood pressure", "혈압 상승"],
    
    # 메트포르민
    "메트포르민": ["metformin", "글루코파지", "Glucophage"],
    "metformin": ["메트포르민", "글루코파지", "Glucophage"],
    
    # 인슐린
    "인슐린": ["insulin"],
    "insulin": ["인슐린"],
    
    # Simvastatin
    "심바스타틴": ["simvastatin", "심바스타틴", "Zocor"],
    "simvastatin": ["심바스타틴", "Zocor"],
    
    # Acetaminophen
    "아세트아미노펜": ["acetaminophen", "타이레놀", "Tylenol", "파라세타몰"],
    "acetaminophen": ["아세트아미노펜", "타이레놀", "Tylenol", "파라세타몰"],
    
    # HbA1c
    "hba1c": ["HbA1c", "당화혈색소", "hemoglobin A1c", "A1c"],
    "HbA1c": ["hba1c", "당화혈색소", "hemoglobin A1c", "A1c"],
    "당화혈색소": ["HbA1c", "hba1c", "hemoglobin A1c", "A1c"],
    
    # 혈압
    "혈압": ["blood pressure", "BP", "수축기 혈압", "이완기 혈압"],
    "blood pressure": ["혈압", "BP", "수축기 혈압", "이완기 혈압"],
    "SBP": ["수축기 혈압", "systolic blood pressure", "수축압"],
    "DBP": ["이완기 혈압", "diastolic blood pressure", "이완압"],
    
    # 가슴 통증/답답함
    "가슴 답답함": ["chest tightness", "chest discomfort", "가슴 통증", "chest pain"],
    "chest pain": ["가슴 통증", "가슴 답답함", "chest tightness", "chest discomfort"],
    "가슴 통증": ["chest pain", "가슴 답답함", "chest tightness", "chest discomfort"],
    
    # 두통
    "두통": ["headache", "두통증"],
    "headache": ["두통", "두통증"],
    
    # 어지러움
    "어지러움": ["dizziness", "현기증", "vertigo"],
    "dizziness": ["어지러움", "현기증", "vertigo"],
    
    # 성별
    "남성": ["male", "남", "남자", "man"],
    "male": ["남성", "남", "남자", "man"],
    "여성": ["female", "여", "여자", "woman"],
    "female": ["여성", "여", "여자", "woman"],
}


def normalize_term(term: str) -> str:
    """
    용어 정규화 (소문자, 공백 제거)
    
    Args:
        term: 정규화할 용어
    
    Returns:
        정규화된 용어
    """
    return term.lower().strip()


def get_synonyms(term: str) -> Set[str]:
    """
    용어의 동의어 집합 반환
    
    Args:
        term: 용어
    
    Returns:
        동의어 집합 (원래 용어 포함)
    """
    normalized = normalize_term(term)
    synonyms = {term, normalized}  # 원래 용어와 정규화된 용어 포함
    
    # 직접 매칭
    if normalized in MEDICAL_SYNONYMS:
        synonyms.update(MEDICAL_SYNONYMS[normalized])
    
    # 역방향 검색 (다른 용어의 동의어 리스트에 포함되어 있는지)
    for key, values in MEDICAL_SYNONYMS.items():
        if normalized in [normalize_term(v) for v in values]:
            synonyms.add(key)
            synonyms.update(values)
    
    return synonyms


def term_matches(term1: str, term2: str) -> bool:
    """
    두 용어가 동의어 관계인지 확인
    
    Args:
        term1: 첫 번째 용어
        term2: 두 번째 용어
    
    Returns:
        동의어 관계이면 True
    """
    synonyms1 = get_synonyms(term1)
    synonyms2 = get_synonyms(term2)
    
    # 교집합이 있으면 동의어
    return len(synonyms1.intersection(synonyms2)) > 0


def find_term_in_text(term: str, text: str) -> bool:
    """
    텍스트에 용어 또는 그 동의어가 포함되어 있는지 확인
    
    Args:
        term: 찾을 용어
        text: 검색할 텍스트
    
    Returns:
        용어 또는 동의어가 텍스트에 포함되어 있으면 True
    """
    text_lower = text.lower()
    synonyms = get_synonyms(term)
    
    for syn in synonyms:
        if normalize_term(syn) in text_lower:
            return True
    
    return False

