"""
질문 텍스트에서 구체적인 update_key 추출

예: "HbA1c 결과가 5.98%로 나왔습니다" -> "labs.hba1c"
"""

import re
from typing import Optional, Dict, Any


# Lab 이름 매핑 (한국어 -> 영어)
LAB_NAME_MAP: Dict[str, str] = {
    "hba1c": "hba1c",
    "HbA1c": "hba1c",
    "당화혈색소": "hba1c",
    "혈당": "glucose",
    "glucose": "glucose",
    "공복혈당": "fpg",
    "FPG": "fpg",
    "fpg": "fpg",
    "혈색소": "hemoglobin",
    "hemoglobin": "hemoglobin",
    "크레아티닌": "creatinine",
    "creatinine": "creatinine",
    "콜레스테롤": "cholesterol",
    "cholesterol": "cholesterol",
}

# Vital 이름 매핑 (한국어 -> 영어)
VITAL_NAME_MAP: Dict[str, str] = {
    "혈압": "blood_pressure",
    "blood pressure": "blood_pressure",
    "수축기 혈압": "sbp",
    "SBP": "sbp",
    "이완기 혈압": "dbp",
    "DBP": "dbp",
    "심박수": "heart_rate",
    "heart rate": "heart_rate",
    "체온": "temperature",
    "temperature": "temperature",
    "호흡수": "respiratory_rate",
    "respiratory rate": "respiratory_rate",
}


def extract_lab_name_from_question(question_text: str) -> Optional[str]:
    """
    질문 텍스트에서 Lab 이름 추출
    
    Args:
        question_text: 질문 텍스트 (예: "HbA1c 결과가 5.98%로 나왔습니다")
    
    Returns:
        Lab 이름 (예: "hba1c") 또는 None
    """
    text_lower = question_text.lower()
    
    # Lab 이름 패턴 매칭
    for korean_name, english_name in LAB_NAME_MAP.items():
        if korean_name.lower() in text_lower or english_name.lower() in text_lower:
            return english_name
    
    # 정규식 패턴으로 추출 시도
    # "HbA1c", "hba1c", "당화혈색소" 등
    patterns = [
        r'\b([Hh][Bb][Aa]1[Cc])\b',
        r'\b(당화혈색소)\b',
        r'\b([Ff][Pp][Gg])\b',
        r'\b(공복혈당)\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, question_text, re.IGNORECASE)
        if match:
            matched_text = match.group(1).lower()
            # 매핑 확인
            if matched_text in LAB_NAME_MAP:
                return LAB_NAME_MAP[matched_text]
            # 직접 매핑
            if matched_text in ["hba1c", "fpg"]:
                return matched_text
    
    return None


def extract_vital_name_from_question(question_text: str) -> Optional[str]:
    """
    질문 텍스트에서 Vital 이름 추출
    
    Args:
        question_text: 질문 텍스트 (예: "혈압이 140/90 mmHg로 나왔습니다")
    
    Returns:
        Vital 이름 (예: "blood_pressure") 또는 None
    """
    text_lower = question_text.lower()
    
    # Vital 이름 패턴 매칭
    for korean_name, english_name in VITAL_NAME_MAP.items():
        if korean_name.lower() in text_lower or english_name.lower() in text_lower:
            return english_name
    
    # 정규식 패턴으로 추출 시도
    # "혈압", "SBP", "DBP" 등
    patterns = [
        r'\b(혈압)\b',
        r'\b([Ss][Bb][Pp])\b',
        r'\b([Dd][Bb][Pp])\b',
        r'\b(심박수)\b',
        r'\b(heart rate)\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, question_text, re.IGNORECASE)
        if match:
            matched_text = match.group(1).lower()
            # 매핑 확인
            if matched_text in VITAL_NAME_MAP:
                return VITAL_NAME_MAP[matched_text]
            # 직접 매핑
            if matched_text in ["sbp", "dbp"]:
                return matched_text
    
    return None


def extract_specific_update_key(question_text: str, update_key_category: str) -> Optional[str]:
    """
    질문 텍스트에서 구체적인 update_key 추출
    
    Args:
        question_text: 질문 텍스트
        update_key_category: 업데이트 키 카테고리 ("labs", "vitals", "medications", "symptoms")
    
    Returns:
        구체적인 update_key (예: "labs.hba1c", "vitals.sbp") 또는 None
    """
    if update_key_category == "labs":
        lab_name = extract_lab_name_from_question(question_text)
        if lab_name:
            return f"labs.{lab_name}"
    
    elif update_key_category == "vitals":
        vital_name = extract_vital_name_from_question(question_text)
        if vital_name:
            return f"vitals.{vital_name}"
    
    # medications, symptoms는 카테고리 레벨만 지원
    return None

