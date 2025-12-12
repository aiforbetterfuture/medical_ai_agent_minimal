"""
한국어 질의 번역 모듈 (확장판)

MEDCAT2는 영어 기반이므로, 한국어 질의를 영어로 번역하여 엔티티 추출 후
다시 한국어로 매핑하는 기능을 제공합니다.

번역 방법:
1. 사전 기반 번역 (의료 용어 정확도 높음)
2. Helsinki-NLP 신경망 번역 (일반 문장 번역)
3. 하이브리드 방식 (사전 + 신경망)
"""

from typing import Dict, List, Optional, Tuple
import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 확장된 의료 용어 사전 (한-영 매핑)
MEDICAL_TERM_DICT = {
    # ===== 질환 (Conditions) =====
    "당뇨병": "diabetes mellitus",
    "당뇨": "diabetes",
    "당뇨병 환자": "diabetes mellitus",
    "제2형 당뇨": "type 2 diabetes",
    "제1형 당뇨": "type 1 diabetes",
    "고혈압": "hypertension",
    "고혈압 환자": "hypertension",
    "본태성 고혈압": "essential hypertension",
    "이차성 고혈압": "secondary hypertension",
    "뇌졸중": "stroke",
    "중풍": "stroke",
    "뇌경색": "cerebral infarction",
    "뇌출혈": "cerebral hemorrhage",
    "뇌혈관 질환": "cerebrovascular disease",
    "고지혈증": "hyperlipidemia",
    "이상지질혈증": "dyslipidemia",
    "고콜레스테롤혈증": "hypercholesterolemia",
    "신부전": "kidney failure",
    "콩팥부전": "kidney failure",
    "신장부전": "kidney failure",
    "급성 신부전": "acute kidney injury",
    "만성콩팥병": "chronic kidney disease",
    "만성신장병": "chronic kidney disease",
    "천식": "asthma",
    "기관지 천식": "bronchial asthma",
    "폐렴": "pneumonia",
    "폐염": "pneumonia",
    "감기": "common cold",
    "독감": "influenza",
    "인플루엔자": "influenza",
    "심부전": "heart failure",
    "울혈성 심부전": "congestive heart failure",
    "관상동맥 질환": "coronary artery disease",
    "협심증": "angina",
    "심근경색": "myocardial infarction",
    "부정맥": "arrhythmia",
    "심방세동": "atrial fibrillation",
    "갑상선 기능 항진증": "hyperthyroidism",
    "갑상선 기능 저하증": "hypothyroidism",
    "갑상선염": "thyroiditis",
    "비만": "obesity",
    "통풍": "gout",
    "관절염": "arthritis",
    "류마티스 관절염": "rheumatoid arthritis",
    "골다공증": "osteoporosis",
    "골관절염": "osteoarthritis",
    "간경변": "liver cirrhosis",
    "간염": "hepatitis",
    "지방간": "fatty liver",
    "위염": "gastritis",
    "위궤양": "gastric ulcer",
    "대장염": "colitis",
    "크론병": "Crohn disease",
    "우울증": "depression",
    "불안장애": "anxiety disorder",
    "치매": "dementia",
    "알츠하이머": "Alzheimer disease",
    "파킨슨병": "Parkinson disease",
    "간질": "epilepsy",
    "발작": "seizure",
    "암": "cancer",
    "종양": "tumor",
    "악성 종양": "malignant tumor",
    "폐암": "lung cancer",
    "위암": "gastric cancer",
    "대장암": "colorectal cancer",
    "유방암": "breast cancer",
    "전립선암": "prostate cancer",
    "백혈병": "leukemia",
    "빈혈": "anemia",
    
    # ===== 증상 (Symptoms) =====
    "흉통": "chest pain",
    "가슴 통증": "chest pain",
    "가슴아픔": "chest pain",
    "호흡곤란": "dyspnea",
    "숨가쁨": "dyspnea",
    "호흡 곤란": "dyspnea",
    "숨참": "shortness of breath",
    "어지럼": "dizziness",
    "어지러움": "dizziness",
    "현기증": "vertigo",
    "두통": "headache",
    "편두통": "migraine",
    "속쓰림": "heartburn",
    "소화불량": "dyspepsia",
    "심계항진": "palpitation",
    "심장 두근거림": "palpitation",
    "두근거림": "palpitation",
    "부종": "edema",
    "부어오름": "edema",
    "붓기": "swelling",
    "다리 부종": "leg edema",
    "기침": "cough",
    "마른 기침": "dry cough",
    "가래": "sputum",
    "객담": "sputum",
    "발열": "fever",
    "열": "fever",
    "고열": "high fever",
    "오한": "chills",
    "메스꺼움": "nausea",
    "구역질": "nausea",
    "구토": "vomiting",
    "토함": "vomiting",
    "답답": "chest tightness",
    "가슴 답답": "chest tightness",
    "흉부 불편감": "chest discomfort",
    "복통": "abdominal pain",
    "배 아픔": "abdominal pain",
    "복부 통증": "abdominal pain",
    "설사": "diarrhea",
    "변비": "constipation",
    "혈변": "bloody stool",
    "소변 이상": "urinary abnormality",
    "빈뇨": "frequent urination",
    "야뇨": "nocturia",
    "피로": "fatigue",
    "피곤": "fatigue",
    "권태감": "malaise",
    "무기력": "lethargy",
    "식욕부진": "loss of appetite",
    "체중 감소": "weight loss",
    "체중 증가": "weight gain",
    "불면": "insomnia",
    "수면 장애": "sleep disorder",
    "발진": "rash",
    "두드러기": "urticaria",
    "가려움": "itching",
    "소양증": "pruritus",
    "관절통": "joint pain",
    "근육통": "muscle pain",
    "요통": "back pain",
    "허리 통증": "back pain",
    "목 통증": "neck pain",
    "시력 저하": "vision loss",
    "청력 저하": "hearing loss",
    "이명": "tinnitus",
    "코피": "nosebleed",
    "코막힘": "nasal congestion",
    "콧물": "runny nose",
    "인후통": "sore throat",
    "목 아픔": "sore throat",
    "삼킴 곤란": "dysphagia",
    
    # ===== 약물 (Medications) =====
    "메트포르민": "metformin",
    "메트폴민": "metformin",
    "인슐린": "insulin",
    "아스피린": "aspirin",
    "스타틴": "statin",
    "아토르바스타틴": "atorvastatin",
    "심바스타틴": "simvastatin",
    "로수바스타틴": "rosuvastatin",
    "암로디핀": "amlodipine",
    "노바스크": "amlodipine",
    "로사르탄": "losartan",
    "발사르탄": "valsartan",
    "텔미사르탄": "telmisartan",
    "에날라프릴": "enalapril",
    "리시노프릴": "lisinopril",
    "베타차단제": "beta blocker",
    "칼슘 차단제": "calcium channel blocker",
    "이뇨제": "diuretic",
    "푸로세마이드": "furosemide",
    "라식스": "furosemide",
    "하이드로클로로티아지드": "hydrochlorothiazide",
    "와파린": "warfarin",
    "헤파린": "heparin",
    "클로피도그렐": "clopidogrel",
    "플라빅스": "clopidogrel",
    "오메프라졸": "omeprazole",
    "판토프라졸": "pantoprazole",
    "항생제": "antibiotics",
    "아목시실린": "amoxicillin",
    "세팔로스포린": "cephalosporin",
    "진통제": "analgesic",
    "아세트아미노펜": "acetaminophen",
    "타이레놀": "acetaminophen",
    "이부프로펜": "ibuprofen",
    "스테로이드": "steroid",
    "프레드니솔론": "prednisolone",
    "항히스타민제": "antihistamine",
    "항우울제": "antidepressant",
    "수면제": "sleeping pill",
    "비타민": "vitamin",
    "철분제": "iron supplement",
    "칼슘제": "calcium supplement",
    
    # ===== 검사/수치 (Labs/Vitals) =====
    "혈압": "blood pressure",
    "수축기 혈압": "systolic blood pressure",
    "이완기 혈압": "diastolic blood pressure",
    "혈당": "blood glucose",
    "공복혈당": "fasting blood glucose",
    "식후혈당": "postprandial glucose",
    "당화혈색소": "HbA1c",
    "A1c": "HbA1c",
    "HbA1c": "HbA1c",
    "eGFR": "eGFR",
    "크레아티닌": "creatinine",
    "BUN": "blood urea nitrogen",
    "요소질소": "blood urea nitrogen",
    "콜레스테롤": "cholesterol",
    "총콜레스테롤": "total cholesterol",
    "LDL": "LDL cholesterol",
    "HDL": "HDL cholesterol",
    "중성지방": "triglycerides",
    "간수치": "liver enzymes",
    "AST": "AST",
    "ALT": "ALT",
    "빌리루빈": "bilirubin",
    "알부민": "albumin",
    "헤모글로빈": "hemoglobin",
    "적혈구": "red blood cell",
    "백혈구": "white blood cell",
    "혈소판": "platelet",
    "요검사": "urinalysis",
    "소변검사": "urinalysis",
    "단백뇨": "proteinuria",
    "혈뇨": "hematuria",
    "심전도": "electrocardiogram",
    "EKG": "electrocardiogram",
    "ECG": "electrocardiogram",
    "흉부 X선": "chest X-ray",
    "CT": "computed tomography",
    "MRI": "magnetic resonance imaging",
    "초음파": "ultrasound",
    "내시경": "endoscopy",
    "위내시경": "gastroscopy",
    "대장내시경": "colonoscopy",
    "체온": "body temperature",
    "맥박": "pulse",
    "심박수": "heart rate",
    "산소포화도": "oxygen saturation",
    "호흡수": "respiratory rate",
    "BMI": "body mass index",
    "체질량지수": "body mass index",
    
    # ===== 인구통계 (Demographics) =====
    "남성": "male",
    "남자": "male",
    "여성": "female",
    "여자": "female",
    "세": "years old",
    "살": "years old",
    "대": "s",  # 50대 -> 50s
    
    # ===== 기타 (Others) =====
    "임신": "pregnancy",
    "임산부": "pregnant",
    "임신 중": "pregnant",
    "수유": "breastfeeding",
    "수유 중": "breastfeeding",
    "흡연": "smoking",
    "담배": "smoking",
    "음주": "alcohol",
    "술": "alcohol",
    "알레르기": "allergy",
    "부작용": "side effect",
    "약물 알레르기": "drug allergy",
    "가족력": "family history",
    "과거력": "medical history",
    "병력": "medical history",
    "수술력": "surgical history",
    "환자": "patient",
    "복용": "taking",
    "복용 중": "currently taking",
}


class KoreanTranslator:
    """
    한국어 의료 질의 번역 클래스 (확장판)
    
    기능:
    1. 한국어 텍스트에서 의료 용어 추출 및 영어 번역 (사전 기반)
    2. Helsinki-NLP opus-mt 신경망 번역 (일반 문장)
    3. 하이브리드 번역 (사전 + 신경망)
    4. MEDCAT2 엔티티 추출 결과를 한국어로 매핑
    5. UTF-8 인코딩 처리
    """
    
    def __init__(
        self, 
        use_neural_translation: bool = False,
        use_llm_translation: bool = False
    ):
        """
        Args:
            use_neural_translation: Helsinki-NLP 신경망 번역 사용 여부
            use_llm_translation: LLM 기반 번역 사용 여부 (기본값: False)
        """
        self.use_neural_translation = use_neural_translation
        self.use_llm_translation = use_llm_translation
        self.term_dict = MEDICAL_TERM_DICT.copy()
        
        # 역사전 생성 (영-한)
        self.reverse_dict = {v.lower(): k for k, v in self.term_dict.items()}
        
        # 신경망 번역기 (지연 로딩)
        self._neural_translator = None
        
        # LLM 번역기 초기화 (선택적)
        self.llm_translator = None
        if use_llm_translation:
            try:
                # OpenAI 또는 다른 LLM API 사용
                # 여기서는 기본 구조만 제공
                pass
            except Exception as e:
                logger.warning(f"LLM 번역기 초기화 실패: {e}")
                self.use_llm_translation = False
    
    def _get_neural_translator(self):
        """신경망 번역기 지연 로딩"""
        if self._neural_translator is None and self.use_neural_translation:
            try:
                from extraction.neural_translator import NeuralTranslator
                self._neural_translator = NeuralTranslator(lazy_load=True)
                logger.info("[KoreanTranslator] 신경망 번역기 초기화")
            except Exception as e:
                logger.warning(f"[KoreanTranslator] 신경망 번역기 초기화 실패: {e}")
                self._neural_translator = None
        return self._neural_translator
    
    def translate_to_english(self, korean_text: str, use_neural: bool = None) -> str:
        """
        한국어 텍스트를 영어로 번역 (하이브리드 방식)
        
        번역 순서:
        1. 사전 기반 번역 (의료 용어 정확도 높음)
        2. 신경망 번역 (남은 한국어 처리)
        
        Args:
            korean_text: 한국어 텍스트
            use_neural: 신경망 번역 사용 여부 (None이면 self.use_neural_translation 사용)
        
        Returns:
            영어로 번역된 텍스트
        """
        if not korean_text or not korean_text.strip():
            return ""
        
        # UTF-8 인코딩 확인
        if isinstance(korean_text, bytes):
            korean_text = korean_text.decode('utf-8', errors='ignore')
        
        # 1. 사전 기반 번역 (의료 용어 먼저)
        english_text = korean_text
        
        # 의료 용어 치환 (긴 것부터 먼저)
        sorted_terms = sorted(self.term_dict.items(), key=lambda x: len(x[0]), reverse=True)
        
        for korean_term, english_term in sorted_terms:
            if korean_term in english_text:
                english_text = english_text.replace(korean_term, english_term)
        
        # 2. 신경망 번역 (아직 한국어가 남아있으면)
        use_neural_flag = use_neural if use_neural is not None else self.use_neural_translation
        
        if use_neural_flag:
            # 한국어가 아직 남아있는지 확인
            korean_remaining = sum(1 for c in english_text if '\uac00' <= c <= '\ud7a3')
            total_chars = len(english_text.replace(" ", ""))
            
            if total_chars > 0 and korean_remaining / total_chars > 0.2:
                # 20% 이상 한국어가 남아있으면 신경망 번역 적용
                neural = self._get_neural_translator()
                if neural and neural.is_available:
                    english_text = neural.translate_ko2en(english_text)
        
        # 3. LLM 번역 (선택적, 백업)
        if self.use_llm_translation and self.llm_translator:
            # TODO: LLM 기반 번역 구현
            pass
        
        return english_text
    
    def translate_to_korean(self, english_text: str, use_neural: bool = None) -> str:
        """
        영어 텍스트를 한국어로 번역
        
        번역 순서:
        1. 사전 기반 역번역 (의료 용어)
        2. 신경망 번역 (일반 문장)
        
        Args:
            english_text: 영어 텍스트
            use_neural: 신경망 번역 사용 여부
        
        Returns:
            한국어로 번역된 텍스트
        """
        if not english_text or not english_text.strip():
            return ""
        
        # 1. 사전 기반 역번역
        korean_text = english_text.lower()
        
        for eng, kor in self.reverse_dict.items():
            if eng in korean_text:
                korean_text = korean_text.replace(eng, kor)
        
        # 원래 대소문자 복원이 필요한 경우 원본 사용
        if korean_text == english_text.lower():
            korean_text = english_text
        
        # 2. 신경망 번역 (아직 영어가 많이 남아있으면)
        use_neural_flag = use_neural if use_neural is not None else self.use_neural_translation
        
        if use_neural_flag:
            # 한국어 비율 확인
            korean_chars = sum(1 for c in korean_text if '\uac00' <= c <= '\ud7a3')
            total_alpha = sum(1 for c in korean_text if c.isalpha())
            
            if total_alpha > 0 and korean_chars / total_alpha < 0.5:
                # 50% 미만 한국어면 신경망 번역 적용
                neural = self._get_neural_translator()
                if neural and neural.is_available:
                    korean_text = neural.translate_en2ko(korean_text)
        
        return korean_text
    
    def map_entities_to_korean(
        self,
        entities: List[Dict],
        original_text: str,
        english_text: str
    ) -> List[Dict]:
        """
        MEDCAT2에서 추출한 영어 엔티티를 한국어로 매핑
        
        Args:
            entities: MEDCAT2 엔티티 리스트
            original_text: 원본 한국어 텍스트
            english_text: 번역된 영어 텍스트
        
        Returns:
            한국어로 매핑된 엔티티 리스트
        """
        mapped_entities = []
        
        # 역사전 생성 (영-한)
        reverse_dict = {v: k for k, v in self.term_dict.items()}
        
        for ent in entities:
            # MEDCAT2 엔티티 형식: pretty_name, source_value, detected_name 등
            if not isinstance(ent, dict):
                continue
                
            # 여러 이름 필드에서 영어 이름 추출
            english_name = (
                ent.get("pretty_name", "") or 
                ent.get("detected_name", "") or 
                ent.get("source_value", "") or
                ent.get("name", "")
            ).lower()
            
            if not english_name:
                continue
            
            # 역사전에서 찾기
            korean_name = reverse_dict.get(english_name)
            
            # 정확히 일치하지 않으면 부분 매칭 시도
            if not korean_name:
                # 여러 단어로 구성된 경우 분리하여 매칭
                english_words = english_name.split()
                for eng_term, kor_term in reverse_dict.items():
                    eng_term_lower = eng_term.lower()
                    # 완전 일치
                    if eng_term_lower == english_name:
                        korean_name = kor_term
                        break
                    # 부분 포함 (단어 단위)
                    if any(eng_term_lower in word or word in eng_term_lower for word in english_words):
                        korean_name = kor_term
                        break
                    # 부분 문자열 매칭
                    if eng_term_lower in english_name or english_name in eng_term_lower:
                        korean_name = kor_term
                        break
            
            # 매핑된 엔티티 생성
            mapped_ent = ent.copy()
            if korean_name:
                mapped_ent["name_korean"] = korean_name
                mapped_ent["name"] = korean_name  # 기본 이름을 한국어로
            else:
                # 매핑 실패 시 영어 이름 유지
                mapped_ent["name_korean"] = english_name
                mapped_ent["name"] = english_name
            
            mapped_entities.append(mapped_ent)
        
        return mapped_entities
    
    def extract_with_translation(
        self,
        korean_text: str,
        medcat2_extractor
    ) -> Dict[str, List[Dict]]:
        """
        한국어 텍스트를 번역하여 MEDCAT2로 엔티티 추출 후 한국어로 매핑
        
        Args:
            korean_text: 한국어 텍스트
            medcat2_extractor: MEDCAT2Extractor 인스턴스
        
        Returns:
            한국어로 매핑된 엔티티 딕셔너리
        """
        # 영어로 번역
        english_text = self.translate_to_english(korean_text)
        
        if not english_text or not english_text.strip():
            return {
                "conditions": [],
                "symptoms": [],
                "labs": [],
                "vitals": []
            }
        
        # MEDCAT2로 엔티티 추출
        try:
            entities_result = medcat2_extractor.cat.get_entities(english_text)
            # entities는 딕셔너리 형태 {0: {...}, 1: {...}}
            entities_dict = entities_result.get("entities", {})
            # 딕셔너리 값을 리스트로 변환
            if isinstance(entities_dict, dict):
                entities = list(entities_dict.values())
            elif isinstance(entities_dict, list):
                entities = entities_dict
            else:
                entities = []
        except Exception as e:
            print(f"[WARNING] MEDCAT2 엔티티 추출 오류: {e}")
            import traceback
            traceback.print_exc()
            entities = []
        
        # 한국어로 매핑
        mapped_entities = self.map_entities_to_korean(
            entities,
            korean_text,
            english_text
        )
        
        # 슬롯 형식으로 변환
        result = {
            "conditions": [],
            "symptoms": [],
            "labs": [],
            "vitals": []
        }
        
        # 수치 정보 파싱 (한국어 텍스트에서도 작동)
        from .medcat2_adapter import _parse_vitals_labs
        vitals_labs = _parse_vitals_labs(korean_text)  # 원본 한국어 텍스트 사용
        result["vitals"].extend(vitals_labs["vitals"])
        result["labs"].extend(vitals_labs["labs"])
        
        for ent in mapped_entities:
            if not isinstance(ent, dict):
                continue
                
            cui = ent.get("cui", "")
            name = ent.get("name", "") or ent.get("pretty_name", "") or ent.get("name_korean", "")
            
            # 타입 정보 추출 (type_ids 또는 type 필드)
            type_ids = ent.get("type_ids", [])
            ent_type = ent.get("type", "")
            if not ent_type and type_ids:
                # type_ids가 있으면 기본적으로 질환으로 간주
                ent_type = "Disease or Syndrome"
            
            ent_type_lower = str(ent_type).lower()
            
            entity_data = {
                "name": name,
                "cui": cui,
                "text": ent.get("source_value", "") or ent.get("detected_name", ""),
                "confidence": ent.get("acc", 0.0) or ent.get("confidence", 0.0),
                "start": ent.get("start", 0),
                "end": ent.get("end", 0)
            }
            
            # 타입별 분류
            if "disease" in ent_type_lower or "disorder" in ent_type_lower or "syndrome" in ent_type_lower:
                result["conditions"].append(entity_data)
            elif "symptom" in ent_type_lower or "sign" in ent_type_lower:
                result["symptoms"].append(entity_data)
            elif "test" in ent_type_lower or "procedure" in ent_type_lower:
                result["labs"].append(entity_data)
            else:
                # 타입 불명시 기본적으로 질환으로 분류
                result["conditions"].append(entity_data)
        
        # 중복 제거
        from .medcat2_adapter import _dedup
        result["conditions"] = _dedup(result["conditions"], key=lambda x: (x.get("name"), x.get("cui")))
        result["symptoms"] = _dedup(result["symptoms"], key=lambda x: (x.get("name"), x.get("cui")))
        result["vitals"] = _dedup(result["vitals"], key=lambda x: (x.get("name"), x.get("value"), x.get("unit")))
        result["labs"] = _dedup(result["labs"], key=lambda x: (x.get("name"), x.get("value"), x.get("unit")))
        
        return result


# 편의 함수
def translate_korean_to_english(text: str) -> str:
    """한국어 텍스트를 영어로 번역"""
    translator = KoreanTranslator()
    return translator.translate_to_english(text)


def extract_entities_with_translation(
    korean_text: str,
    medcat2_extractor
) -> Dict[str, List[Dict]]:
    """한국어 텍스트에서 엔티티 추출 (번역 포함)"""
    translator = KoreanTranslator()
    return translator.extract_with_translation(korean_text, medcat2_extractor)

