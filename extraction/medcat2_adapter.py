"""
MedCAT2 어댑터 (간소화)
- MedCAT2 모델 로드
- 엔티티 추출
- UMLS CUI 매핑
"""

import os
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# .env 파일 자동 로드
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)


def _parse_vitals_labs(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """한글/영문 뒤섞인 수치 파싱(혈압/A1c/FPG)"""
    t = text.lower()
    out = {"vitals": [], "labs": []}
    
    # 혈압 파싱: 140/90 또는 140/90 mmHg
    m = re.search(r"(\d{2,3})\s*/\s*(\d{2,3})\s*(mmhg)?", t)
    if m:
        sbp = float(m.group(1))
        dbp = float(m.group(2))
        if sbp < dbp:
            sbp, dbp = dbp, sbp
        out["vitals"].append({"name": "SBP", "value": sbp, "unit": "mmHg"})
        out["vitals"].append({"name": "DBP", "value": dbp, "unit": "mmHg"})
    
    # A1c 파싱
    m = re.search(r"(a1c|당화혈색소|hba1c)\s*[:는은]?\s*(\d+(?:\.\d+)?)\s*%", t, re.IGNORECASE)
    if m:
        out["labs"].append({"name": "A1c", "value": float(m.group(2)), "unit": "%"})
    
    # 공복혈당 파싱
    m = re.search(r"(fpg|공복혈당|혈당)\s*[: ]?(\d+(?:\.\d+)?)\s*(mg/dl|mg)?", t)
    if m:
        out["labs"].append({"name": "FPG", "value": float(m.group(2)), "unit": "mg/dL"})
    
    return out


class MedCAT2Adapter:
    """
    MEDCAT2 어댑터 클래스
    
    환경 변수:
        MEDCAT2_MODEL_PATH: 모델 팩 파일 경로 (필수)
    """
    
    _instance = None
    _model = None
    
    def __new__(cls, model_path: Optional[str] = None):
        """싱글톤 패턴"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, model_path: Optional[str] = None):
        """초기화 (싱글톤이므로 한 번만 실행)"""
        if self._model is not None:
            return  # 이미 로드됨
        
        self.model_path = model_path or os.getenv("MEDCAT2_MODEL_PATH")
        
        if not self.model_path:
            print("[WARNING] MEDCAT2_MODEL_PATH가 설정되지 않았습니다. MedCAT2 추출을 건너뜁니다.")
            self._model = None
            return
        
        if not os.path.exists(self.model_path):
            print(f"[WARNING] MEDCAT2 모델 파일을 찾을 수 없습니다: {self.model_path}")
            self._model = None
            return
        
        self._load_model()
    
    def _load_model(self):
        """MEDCAT2 모델 로드"""
        try:
            from medcat.cat import CAT
            self._model = CAT.load_model_pack(self.model_path)
            print(f"[MedCAT2] 모델 로드 완료: {self.model_path}")
        except ImportError:
            print("[WARNING] medcat 패키지가 설치되지 않았습니다. MedCAT2 추출을 건너뜁니다.")
            self._model = None
        except Exception as e:
            print(f"[WARNING] MEDCAT2 모델 로드 실패: {e}")
            self._model = None
    
    def extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        텍스트에서 의료 엔티티 추출
        
        Args:
            text: 분석할 텍스트
        
        Returns:
            {
                "conditions": [{"name": "...", "cui": "...", "confidence": 0.9}],
                "symptoms": [...],
                "medications": [...],
                "vitals": [...],
                "labs": [...]
            }
        """
        if not text or not text.strip():
            return {
                "conditions": [],
                "symptoms": [],
                "medications": [],
                "vitals": [],
                "labs": []
            }
        
        result = {
            "conditions": [],
            "symptoms": [],
            "medications": [],
            "vitals": [],
            "labs": []
        }
        
        # MedCAT2 모델이 있으면 사용
        if self._model:
            try:
                entities = self._model.get_entities(text)
                
                for entity in entities.get('entities', {}).values():
                    cui = entity.get('cui', '')
                    name = entity.get('pretty_name', entity.get('source_value', ''))
                    confidence = entity.get('acc', 0.0)
                    tui = entity.get('tui', [])
                    
                    # TUI 기반 분류
                    if any(t in tui for t in ['T047', 'T048', 'T049']):  # 질환
                        result["conditions"].append({
                            "name": name,
                            "cui": cui,
                            "confidence": confidence,
                            "source": "medcat2"
                        })
                    elif any(t in tui for t in ['T184']):  # 증상
                        result["symptoms"].append({
                            "name": name,
                            "cui": cui,
                            "confidence": confidence,
                            "source": "medcat2"
                        })
                    elif any(t in tui for t in ['T121', 'T200']):  # 약물
                        result["medications"].append({
                            "name": name,
                            "cui": cui,
                            "confidence": confidence,
                            "source": "medcat2"
                        })
            except Exception as e:
                print(f"[WARNING] MedCAT2 추출 오류: {e}")
        
        # 수치 정보는 정규표현식으로 추출
        vitals_labs = _parse_vitals_labs(text)
        result["vitals"].extend(vitals_labs["vitals"])
        result["labs"].extend(vitals_labs["labs"])
        
        return result

