"""
멀티턴 실험 메인 실행 스크립트 (개선 버전)
LLM vs AI Agent 성능 비교를 위한 80명 x 5턴 실험 실행

주요 개선사항:
1. 기존 run_agent() 함수 활용 (스캐폴드 통합)
2. core.llm_client 사용 (LLM 모드)
3. ProfileStore, ResponseCache 통합
4. 대화 히스토리 올바른 형식으로 관리
"""

import json
import hashlib
import os
import sys
from pathlib import Path

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import yaml
import logging

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 로깅 설정 (import보다 먼저 설정하여 logger 사용 가능하게 함)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 기존 스캐폴드 임포트
from agent.graph import run_agent
from core.llm_client import get_llm_client
from core.config import get_llm_config, get_agent_config
from memory.profile_store import ProfileStore

# RAGAS 평가지표 계산
try:
    from experiments.evaluation.ragas_metrics import calculate_ragas_metrics_safe
    HAS_RAGAS_EVAL = True
except ImportError:
    HAS_RAGAS_EVAL = False
    logger.warning("RAGAS 평가 모듈을 임포트할 수 없습니다. 평가지표를 계산하지 않습니다.")

# 멀티턴 컨텍스트 평가지표 계산 (CUS, UR, CCR)
try:
    from experiments.evaluation.multiturn_context_metrics import (
        compute_cus,
        compute_ur,
        ccr_rule_checks
    )
    from experiments.evaluation.question_bank_mapper import get_question_metadata
    HAS_MULTITURN_METRICS = True
except ImportError:
    HAS_MULTITURN_METRICS = False
    logger.warning("멀티턴 컨텍스트 평가 모듈을 임포트할 수 없습니다. CUS/UR/CCR을 계산하지 않습니다.")

# 고급 평가 지표 (SFS, CSP, CUS 개선)
try:
    from experiments.evaluation.advanced_metrics import compute_advanced_metrics
    HAS_ADVANCED_METRICS = True
except ImportError:
    HAS_ADVANCED_METRICS = False
    logger.warning("고급 평가 지표 모듈을 로드할 수 없습니다. SFS, CSP, CUS_improved를 계산하지 않습니다.")

# 계층형 메모리 검증 모듈
try:
    from experiments.evaluation.memory_verification import MemoryVerifier
    HAS_MEMORY_VERIFICATION = True
except ImportError:
    HAS_MEMORY_VERIFICATION = False
    logger.warning("메모리 검증 모듈을 로드할 수 없습니다. 메모리 검증을 수행하지 않습니다.")


class MultiTurnExperimentRunner:
    """멀티턴 실험 실행기 (개선 버전)"""

    def __init__(self, config_path: str):
        """초기화"""
        self.config_path = config_path
        self.config = self._load_config()
        self.run_id = self.config['run']['run_id']
        self.runs_dir = Path(self.config['logging']['runs_dir'])

        # 실행 디렉토리 생성
        self.run_dir = self.runs_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # 로깅 파일 경로
        self.events_log_path = self.run_dir / "events.jsonl"
        self.node_trace_log_path = self.run_dir / "node_trace.jsonl"
        self.run_manifest_path = self.run_dir / "run_manifest.json"
        
        # 메모리 검증기 초기화 (Agent 모드에서만 사용)
        if HAS_MEMORY_VERIFICATION:
            self.memory_verifier = MemoryVerifier()
            self.memory_verification_enabled = self.config.get('evaluation', {}).get('memory_verification_enabled', False)
        else:
            self.memory_verifier = None
            self.memory_verification_enabled = False

        # 환자 리스트 및 질문 뱅크/스크립트 로드
        self.patients = self._load_patients()
        
        # 새로운 질문 생성 방식 사용 여부 확인
        self.use_multiturn_scripts = self.config.get('multiturn_scripts', {}).get('enabled', False)
        
        if self.use_multiturn_scripts:
            # 멀티턴 스크립트 파일 존재 여부 확인
            scripts_path = Path(self.config.get('multiturn_scripts', {}).get('scripts_path', 'data/multiturn_scripts/scripts_5turn.jsonl'))
            
            if not scripts_path.exists():
                logger.warning(f"멀티턴 스크립트 파일을 찾을 수 없습니다: {scripts_path}")
                logger.info("멀티턴 스크립트를 자동 생성합니다...")
                
                # 멀티턴 스크립트 자동 생성 시도
                try:
                    from extraction.synthea_slot_builder import SyntheaSlotBuilder
                    from extraction.synthea_script_generator import SyntheaScriptGenerator
                    import random
                    
                    profile_cards_dir = Path(self.config.get('data', {}).get('profile_cards_dir', 'data/patients/profile_cards'))
                    slot_builder_config_dir = Path(self.config.get('multiturn_scripts', {}).get('slot_builder_config_dir', 'config/synthea'))
                    max_patients = None  # 모든 환자에 대해 생성
                    seed = self.config.get('reproducibility', {}).get('global_seed', 42)
                    
                    # 시드 설정
                    random.seed(seed)
                    
                    # 스크립트 디렉토리 생성
                    scripts_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Slot Builder 및 Script Generator 초기화
                    slot_builder = SyntheaSlotBuilder(config_dir=slot_builder_config_dir)
                    script_generator = SyntheaScriptGenerator()
                    
                    # 프로파일 카드 로드
                    profile_cards = list(profile_cards_dir.glob('SYN_*.json'))
                    if max_patients:
                        profile_cards = profile_cards[:max_patients]
                    
                    # 스크립트 생성
                    scripts_written = 0
                    with open(scripts_path, 'w', encoding='utf-8') as f:
                        for profile_card_path in profile_cards:
                            try:
                                patient_id = profile_card_path.stem
                                profile_card = json.load(open(profile_card_path, 'r', encoding='utf-8'))
                                
                                # 슬롯 추출
                                slots = slot_builder.build_slots(profile_card)
                                
                                # 5턴 질문 생성
                                questions = script_generator.generate_5turn_script(slots)
                                
                                # questions는 List[str]이므로 문자열 리스트로 처리
                                script = {
                                    "patient_id": patient_id,
                                    "slots": slots,
                                    "turns": [
                                        {
                                            "turn_id": i + 1,
                                            "question_id": f"T{i+1}_Q01",
                                            "question_text": q if isinstance(q, str) else str(q),
                                            "expected_slots": {}
                                        }
                                        for i, q in enumerate(questions)
                                    ]
                                }
                                
                                f.write(json.dumps(script, ensure_ascii=False) + '\n')
                                scripts_written += 1
                            except Exception as e:
                                logger.warning(f"환자 {profile_card_path.name} 스크립트 생성 실패: {e}")
                                continue
                    
                    logger.info(f"멀티턴 스크립트 생성 완료: {scripts_written}명의 환자 스크립트 생성 ({scripts_path})")
                    
                    # 생성된 스크립트가 0개면 질문 뱅크 모드로 전환
                    if scripts_written == 0:
                        logger.warning("생성된 멀티턴 스크립트가 없습니다. 질문 뱅크 모드로 전환합니다.")
                        self.use_multiturn_scripts = False
                except Exception as e:
                    import traceback
                    logger.error(f"멀티턴 스크립트 자동 생성 실패: {e}")
                    logger.debug(traceback.format_exc())
                    logger.warning("질문 뱅크 모드로 전환합니다.")
                    self.use_multiturn_scripts = False
            
            if self.use_multiturn_scripts:
                # 자동 생성된 멀티턴 스크립트 로드
                try:
                    self.multiturn_scripts = self._load_multiturn_scripts()
                    if len(self.multiturn_scripts) == 0:
                        logger.warning("로드된 멀티턴 스크립트가 없습니다. 질문 뱅크 모드로 전환합니다.")
                        self.use_multiturn_scripts = False
                    else:
                        logger.info(f"멀티턴 스크립트 모드 활성화: {len(self.multiturn_scripts)}명의 환자 스크립트 로드")
                except Exception as e:
                    logger.error(f"멀티턴 스크립트 로드 실패: {e}")
                    logger.warning("질문 뱅크 모드로 전환합니다.")
                    self.use_multiturn_scripts = False
        
        if not self.use_multiturn_scripts:
            # 기존 질문 뱅크 로드
            self.question_bank = self._load_question_bank()
            logger.info(f"질문 뱅크 모드 활성화: {self.question_bank.get('version', 'unknown')}")

        # LLM 설정 로드 (기존 스캐폴드)
        self.llm_config = get_llm_config()
        self.agent_config = get_agent_config()

        # LLM 클라이언트 초기화 (LLM 모드용)
        self.llm_client = get_llm_client(
            provider=self.config['llm']['provider'],
            model=self.config['llm']['model'],
            temperature=self.config['llm']['temperature'],
            max_tokens=self.config['llm']['max_tokens']
        )

    def _load_config(self) -> Dict:
        """설정 파일 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"설정 파일을 찾을 수 없습니다: {self.config_path}")
            raise
        except PermissionError:
            logger.error(f"설정 파일 읽기 권한이 없습니다: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"YAML 파싱 오류: {e}")
            raise
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            raise

    def _load_patients(self) -> List[Dict]:
        """환자 리스트 로드"""
        patient_list_path = Path(self.config['data']['patient_list_path'])
        try:
            with open(patient_list_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'patients' not in data:
                raise ValueError(f"환자 리스트 형식 오류: 'patients' 키가 없습니다")
            return data['patients']
        except FileNotFoundError:
            logger.error(f"환자 리스트 파일을 찾을 수 없습니다: {patient_list_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            raise
        except Exception as e:
            logger.error(f"환자 리스트 로드 실패: {e}")
            raise

    def _load_question_bank(self) -> Dict:
        """질문 뱅크 로드"""
        question_bank_path = Path(self.config['question_bank']['path'])
        try:
            with open(question_bank_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'items' not in data:
                raise ValueError(f"질문 뱅크 형식 오류: 'items' 키가 없습니다")
            return data
        except FileNotFoundError:
            logger.error(f"질문 뱅크 파일을 찾을 수 없습니다: {question_bank_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            raise
        except Exception as e:
            logger.error(f"질문 뱅크 로드 실패: {e}")
            raise
    
    def _load_multiturn_scripts(self) -> Dict[str, Dict]:
        """멀티턴 스크립트 로드 (JSONL 형식)"""
        scripts_path = Path(self.config['multiturn_scripts']['scripts_path'])
        try:
            scripts_dict = {}
            with open(scripts_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        script = json.loads(line)
                        patient_id = script.get('patient_id', '')
                        if patient_id:
                            scripts_dict[patient_id] = script
            return scripts_dict
        except FileNotFoundError:
            logger.error(f"멀티턴 스크립트 파일을 찾을 수 없습니다: {scripts_path}")
            logger.error("먼저 experiments/generate_multiturn_scripts_from_fhir.py를 실행하여 스크립트를 생성하세요.")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            raise
        except Exception as e:
            logger.error(f"멀티턴 스크립트 로드 실패: {e}")
            raise

    def _load_profile_card(self, patient_id: str) -> Dict:
        """환자 프로파일 카드 로드"""
        profile_cards_dir = Path(self.config['data']['profile_cards_dir'])
        profile_path = profile_cards_dir / f"{patient_id}.json"

        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 프로파일 카드가 없으면 상위로 전파 (환자 스킵 처리)
            raise
        except json.JSONDecodeError as e:
            logger.error(f"프로파일 카드 JSON 파싱 오류 ({patient_id}): {e}")
            raise
        except Exception as e:
            logger.error(f"프로파일 카드 로드 실패 ({patient_id}): {e}")
            raise

    def _select_question(self, patient_id: str, turn_id: int) -> Dict:
        """
        질문 선택 (질문 뱅크 또는 멀티턴 스크립트)
        """
        if self.use_multiturn_scripts:
            # 멀티턴 스크립트에서 직접 질문 가져오기
            if patient_id in self.multiturn_scripts:
                script = self.multiturn_scripts[patient_id]
                turns = script.get('turns', [])
                for turn in turns:
                    if turn.get('turn_id') == turn_id:
                        return {
                            'id': f"{patient_id}_T{turn_id}",
                            'turn_id': turn_id,
                            'template_text': turn.get('question', ''),
                            'question': turn.get('question', '')  # 이미 채워진 질문
                        }
                # 해당 턴이 없으면 빈 질문
                logger.warning(f"턴 {turn_id} 질문을 찾을 수 없습니다: {patient_id}")
                return {
                    'id': f"{patient_id}_T{turn_id}",
                    'turn_id': turn_id,
                    'template_text': f"턴 {turn_id} 질문",
                    'question': f"턴 {turn_id} 질문"
                }
            else:
                logger.warning(f"환자 스크립트를 찾을 수 없습니다: {patient_id}")
                return {
                    'id': f"{patient_id}_T{turn_id}",
                    'turn_id': turn_id,
                    'template_text': f"환자 {patient_id} 턴 {turn_id} 질문",
                    'question': f"환자 {patient_id} 턴 {turn_id} 질문"
                }
        else:
            # 기존 질문 뱅크 방식
            selection_key = f"{patient_id}:{turn_id}"
            hash_digest = hashlib.sha256(selection_key.encode()).hexdigest()
            index = int(hash_digest, 16) % 15

            # 해당 턴의 질문들 필터링
            if not hasattr(self, 'question_bank'):
                logger.error("질문 뱅크가 로드되지 않았습니다. 멀티턴 스크립트 모드를 사용 중입니다.")
                return None
            
            turn_questions = [
                q for q in self.question_bank['items']
                if q['turn_id'] == turn_id
            ]

            if index >= len(turn_questions):
                index = index % len(turn_questions)

            return turn_questions[index]

    def _fill_placeholders(self, template_text: str, profile_card: Dict,
                          turn_id: int) -> str:
        """
        템플릿 플레이스홀더 채우기
        
        Synthea 프로필 카드 구조에 맞게 데이터 추출
        """
        question = template_text
        
        # Demographics 추출
        demographics = profile_card.get('demographics', {})
        clinical = profile_card.get('clinical_summary', {})
        korean_aliases = profile_card.get('notes_for_generation', {}).get('korean_aliases', {})
        turn_injection = profile_card.get('turn_injection_fields', {})

        # ============================================================
        # 기본 정보
        # ============================================================

        # 나이
        age = demographics.get('age_years', '?')
        question = question.replace('{AGE}', str(age))

        # 성별 (한국어 변환)
        sex_code = demographics.get('sex', 'M')
        sex_ko_map = korean_aliases.get('sex', {'M': '남성', 'F': '여성'})
        sex_ko = sex_ko_map.get(sex_code, sex_code)
        question = question.replace('{SEX_KO}', sex_ko)

        # ============================================================
        # 질환 (Conditions)
        # ============================================================
        conditions = clinical.get('conditions', [])

        if conditions and len(conditions) > 0:
            # 첫 번째 질환
            cond1_name = conditions[0].get('name', '질환1')
            # 한국어 별칭이 있으면 사용
            cond1_ko = korean_aliases.get('conditions', {}).get(cond1_name, cond1_name)
            question = question.replace('{COND1_KO}', cond1_ko)

            # 두 번째 질환
            if len(conditions) > 1:
                cond2_name = conditions[1].get('name', '질환2')
                cond2_ko = korean_aliases.get('conditions', {}).get(cond2_name, cond2_name)
                question = question.replace('{COND2_KO}', cond2_ko)
        else:
            # 질환이 없으면 기본값
            question = question.replace('{COND1_KO}', '기저질환')
            question = question.replace('{COND2_KO}', '다른질환')

        # ============================================================
        # 약물 (Medications)
        # ============================================================
        medications = clinical.get('medications', [])

        if medications and len(medications) > 0:
            # 첫 번째 약물 (전체 이름 사용)
            med1_name = medications[0].get('name', '약물1')
            question = question.replace('{MED1_KO}', med1_name)

            # 두 번째 약물
            if len(medications) > 1:
                med2_name = medications[1].get('name', '약물2')
                question = question.replace('{MED2_KO}', med2_name)
        else:
            # 약물이 없으면 기본값
            question = question.replace('{MED1_KO}', '복용약')
            question = question.replace('{MED2_KO}', '다른약')

        # ============================================================
        # 알레르기
        # ============================================================
        allergies = clinical.get('allergies', [])

        if allergies and len(allergies) > 0:
            # name 필드 우선, 없으면 substance 사용
            allergy_text = allergies[0].get('name') or allergies[0].get('substance', '알레르기')
            question = question.replace('{ALLERGY_KO}', allergy_text)
        else:
            question = question.replace('{ALLERGY_KO}', '특정 알레르기')

        # ============================================================
        # Chief Complaint & Duration
        # ============================================================
        chief_complaint_seed = clinical.get('chief_complaint_seed', {})

        cc = chief_complaint_seed.get('complaint', '증상')
        dur = chief_complaint_seed.get('duration', '며칠')
        trigger = chief_complaint_seed.get('context', '특정 상황')

        question = question.replace('{CC}', cc)
        question = question.replace('{DUR}', dur)
        question = question.replace('{TRIGGER}', trigger)

        # ============================================================
        # Vitals (최근 측정값) - 모든 턴에서 사용 가능
        # ============================================================
        vitals = clinical.get('vitals_recent', [])

        if vitals and len(vitals) > 0:
            # 첫 번째 vital (보통 혈압)
            vital = vitals[0]
            vital_name = vital.get('type', '혈압').replace('_', ' ')
            vital_value = str(vital.get('value', '140/90'))
            vital_unit = vital.get('unit', 'mmHg')

            question = question.replace('{VITAL_NAME}', vital_name)
            question = question.replace('{VITAL_VALUE}', vital_value)
            question = question.replace('{VITAL_UNIT}', vital_unit)
        else:
            # Turn 3의 경우 turn_injection_fields에서 가져오기 시도
            if turn_id == 3:
                t3_update = turn_injection.get('T3_update_event', {}).get('payload', {})
                vital = t3_update.get('vital', {})
                if vital:
                    vital_name = '혈압' if vital.get('type') == 'blood_pressure' else '심박수'
                    vital_value = str(vital.get('value', ''))
                    vital_unit = vital.get('unit', '')
                    question = question.replace('{VITAL_NAME}', vital_name)
                    question = question.replace('{VITAL_VALUE}', vital_value)
                    question = question.replace('{VITAL_UNIT}', vital_unit)
                else:
                    question = question.replace('{VITAL_NAME}', '혈압')
                    question = question.replace('{VITAL_VALUE}', '140/90')
                    question = question.replace('{VITAL_UNIT}', 'mmHg')
            else:
                question = question.replace('{VITAL_NAME}', '혈압')
                question = question.replace('{VITAL_VALUE}', '140/90')
                question = question.replace('{VITAL_UNIT}', 'mmHg')

        # ============================================================
        # Labs (최근 검사 결과) - 모든 턴에서 사용 가능
        # ============================================================
        labs = clinical.get('labs_recent', [])

        if labs and len(labs) > 0:
            # 첫 번째 lab (보통 HbA1c)
            lab = labs[0]
            lab_name = lab.get('name', '혈당')
            lab_value = str(lab.get('value', '180'))
            lab_unit = lab.get('unit', 'mg/dL')

            question = question.replace('{LAB_NAME}', lab_name)
            question = question.replace('{LAB_VALUE}', lab_value)
            question = question.replace('{LAB_UNIT}', lab_unit)
        else:
            question = question.replace('{LAB_NAME}', '혈당')
            question = question.replace('{LAB_VALUE}', '180')
            question = question.replace('{LAB_UNIT}', 'mg/dL')

        # ============================================================
        # 기타 플레이스홀더 (턴별 특수값)
        # ============================================================

        # T4 턴용: OTC 약물
        t4_addition = turn_injection.get('T4_minor_addition', {})
        otc_text = t4_addition.get('payload', '타이레놀')
        question = question.replace('{OTC}', otc_text)

        # T3 턴용: 새로운 증상
        t3_update = turn_injection.get('T3_update_event', {}).get('payload', {})
        symptom_change = t3_update.get('symptom_change', '새로운 증상')
        question = question.replace('{NEW_INFO}', symptom_change)

        # ADD_SYM (추가 증상) - chief complaint의 severity나 context 활용
        add_sym = chief_complaint_seed.get('severity', '추가 증상')
        question = question.replace('{ADD_SYM}', add_sym)

        return question

    def _format_conversation_history(self, history: List[Dict]) -> str:
        """
        대화 히스토리를 문자열로 변환 (기존 스캐폴드 형식)

        Args:
            history: [{"question": "...", "answer": "..."}, ...]

        Returns:
            "Q: ...\nA: ...\n\nQ: ...\nA: ..." 형식
        """
        formatted_parts = []
        for turn in history:
            formatted_parts.append(f"Q: {turn['question']}")
            formatted_parts.append(f"A: {turn['answer']}")
            formatted_parts.append("")  # 빈 줄

        return "\n".join(formatted_parts)

    def _run_llm_mode(self, question: str, patient_id: str, turn_id: int,
                     conversation_history: List[Dict]) -> Dict:
        """
        LLM 모드 실행 (core.llm_client 사용)
        """
        start_time = datetime.now(timezone.utc)

        # 시스템 프롬프트
        system_prompt = """당신은 의료 상담 AI입니다. 환자의 질문에 답변하되:
1. 확정 진단은 하지 않습니다
2. 근거 기반으로 설명합니다
3. 위험 신호가 있으면 반드시 언급합니다
4. 응급 상황이면 즉시 의료기관 방문을 권고합니다"""

        # 대화 히스토리 포함한 프롬프트 구성
        history_text = self._format_conversation_history(conversation_history)
        full_prompt = f"{history_text}\n\nQ: {question}" if history_text else question

        # LLM 호출
        try:
            answer = self.llm_client.generate(
                prompt=full_prompt,
                system_prompt=system_prompt
            )

            # 토큰 사용량 추정 (간단 계산)
            input_tokens = len(full_prompt.split()) * 1.3  # 대략 추정
            output_tokens = len(answer.split()) * 1.3
            usage = {
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens),
                "estimated_cost_usd": self._estimate_cost(int(input_tokens), int(output_tokens))
            }

        except Exception as e:
            import traceback
            error_msg = f"LLM API call failed: {e}"
            logger.error(error_msg, exc_info=True)
            print(f"\n[ERROR] LLM 모드 실행 실패:")
            print(f"  환자: {patient_id}, 턴: {turn_id}")
            print(f"  에러: {e}")
            print(f"  상세 정보:")
            traceback.print_exc()
            print()
            
            # API 할당량 초과나 인증 오류는 즉시 중단
            error_str = str(e).lower()
            if 'quota' in error_str or '429' in error_str or 'rate limit' in error_str:
                print(f"\n[CRITICAL] API 할당량 초과 또는 Rate Limit 도달!")
                print(f"  실험을 즉시 중단합니다.")
                raise RuntimeError(f"API 할당량 초과: {e}")
            elif '401' in error_str or 'unauthorized' in error_str or 'api key' in error_str:
                print(f"\n[CRITICAL] API 인증 실패!")
                print(f"  실험을 즉시 중단합니다.")
                raise RuntimeError(f"API 인증 실패: {e}")
            
            answer = "죄송합니다. 응답 생성 중 오류가 발생했습니다."
            usage = {"input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0}
        
        # LLM 모드에서도 RAGAS 메트릭 계산 시도 (contexts가 없어도 일부 메트릭 계산 가능)
        ragas_metrics = None
        if HAS_RAGAS_EVAL and self.config.get('evaluation', {}).get('per_turn_metrics'):
            # LLM 모드에서는 검색된 문서가 없으므로 빈 contexts로 계산
            # 안전한 래퍼 함수 사용으로 모든 예외가 처리되지만, 이중 안전장치 추가
            try:
                ragas_metrics = calculate_ragas_metrics_safe(
                    question=question,
                    answer=answer if 'answer' in locals() else "",
                    contexts=[],  # LLM 모드에서는 검색 없음
                    include_perplexity=True,  # Perplexity 포함
                    conversation_history=conversation_history  # Perplexity 계산용
                )
            except Exception as e:
                # calculate_ragas_metrics_safe는 이미 모든 예외를 처리하지만,
                # 혹시 모를 예외 상황에 대비한 이중 안전장치
                logger.warning(f"LLM 모드 RAGAS 메트릭 계산 중 오류 (실험 계속 진행): {e}")
                ragas_metrics = None  # 명시적으로 None 설정

        end_time = datetime.now(timezone.utc)

        return {
            "answer": answer if 'answer' in locals() else "죄송합니다. 응답 생성 중 오류가 발생했습니다.",
            "usage": usage if 'usage' in locals() else {"input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0},
            "timing_ms": {
                "total": int((end_time - start_time).total_seconds() * 1000)
            },
            "timestamps": {
                "started_at_utc": start_time.isoformat(),
                "ended_at_utc": end_time.isoformat()
            },
            "metadata": {},
            "ragas_metrics": ragas_metrics
        }

    def _run_agent_mode(self, question: str, patient_id: str, turn_id: int,
                       conversation_history: List[Dict],
                       session_state: Dict = None,
                       profile_store: ProfileStore = None) -> Dict:
        """
        Agent 모드 실행 (기존 run_agent 함수 활용)
        """
        start_time = datetime.now(timezone.utc)

        # 대화 히스토리 문자열 형식으로 변환
        history_text = self._format_conversation_history(conversation_history)

        # Feature flags 설정 (실험 config 반영)
        feature_overrides = self.config['agent'].get('feature_flags', {})

        # 세션 ID (환자별로 고유)
        session_id = f"{self.run_id}_{patient_id}"

        # 세션 상태 준비 (ProfileStore 재사용)
        if session_state is None:
            session_state = {}

        if profile_store is not None:
            session_state['profile_store'] = profile_store

        try:
            # 기존 run_agent 함수 사용
            final_state = run_agent(
                user_text=question,
                mode='ai_agent',
                conversation_history=history_text,
                session_state=session_state,
                feature_overrides=feature_overrides,
                return_state=True,  # 전체 상태 반환
                session_id=session_id,
                user_id=patient_id
            )

            # 답변 추출 (여러 소스 확인)
            answer = final_state.get('answer', '')
            cache_hit = final_state.get('cache_hit', False)
            cached_response = final_state.get('cached_response')
            skip_pipeline = final_state.get('skip_pipeline', False)
            
            # 캐시 히트인데 answer가 비어있는 경우
            if cache_hit and (not answer or not answer.strip()):
                if cached_response:
                    answer = cached_response
                    print(f"[INFO] 캐시 히트: 캐시된 응답 사용 ({len(answer)}자)")
                else:
                    print(f"\n[WARNING] 캐시 히트인데 캐시된 응답이 없습니다:")
                    print(f"  환자: {patient_id}, 턴: {turn_id}")
                    print(f"  final_state keys: {list(final_state.keys())[:20]}...")
                    print(f"  cache_hit: {cache_hit}")
                    print(f"  skip_pipeline: {skip_pipeline}")
                    print(f"  cached_response: {cached_response}")
                    print()
                    answer = "죄송합니다. 캐시된 응답을 찾을 수 없습니다."
            
            # 일반적인 경우 답변이 비어있는 경우
            elif not answer or not answer.strip():
                print(f"\n[WARNING] Agent 모드에서 답변이 비어있습니다:")
                print(f"  환자: {patient_id}, 턴: {turn_id}")
                print(f"  cache_hit: {cache_hit}")
                print(f"  skip_pipeline: {skip_pipeline}")
                print(f"  cached_response: {cached_response}")
                print(f"  final_state keys: {list(final_state.keys())[:20]}...")
                print()
                # 캐시된 응답이 있으면 사용
                if cached_response:
                    answer = cached_response
                    print(f"[INFO] 캐시된 응답 사용: {answer[:100]}...")
                else:
                    answer = "죄송합니다. 응답을 생성하지 못했습니다."

            # 슬롯 상태 추출 (멀티턴 컨텍스트 평가용)
            try:
                from experiments.evaluation.multiturn_context_metrics import (
                    extract_slots_state_from_profile_store,
                    extract_turn_updates
                )
            except ImportError:
                # 평가 모듈이 없으면 빈 딕셔너리 반환
                def extract_slots_state_from_profile_store(ps): return {}
                def extract_turn_updates(current, previous): return {}
            
            current_profile_store = final_state.get('profile_store')
            current_slots_state = extract_slots_state_from_profile_store(current_profile_store)
            
            # 이전 턴 슬롯 상태 (세션 상태에서 가져오기)
            previous_slots_state = session_state.get('previous_slots_state', {})
            
            # 턴 업데이트 계산
            turn_updates = extract_turn_updates(current_slots_state, previous_slots_state)
            
            # 검색된 문서 추출 (멀티턴 컨텍스트 평가용)
            retrieved_docs = final_state.get('retrieved_docs', [])
            # 문서에서 텍스트만 추출 (크기 제한)
            retrieved_docs_summary = []
            for doc in retrieved_docs[:10]:  # 최대 10개만 저장
                if isinstance(doc, dict):
                    doc_summary = {
                        "doc_id": doc.get("doc_id", ""),
                        "score": doc.get("score", 0.0),
                        "text_hash": doc.get("text_hash", ""),
                        "text_preview": doc.get("text", "")[:200] if doc.get("text") else "",  # 처음 200자만
                    }
                    retrieved_docs_summary.append(doc_summary)
            
            # 메타데이터 수집
            metadata = {
                "cache_hit": final_state.get('cache_hit', False),
                "quality_score": final_state.get('quality_score', 0.0),
                "iteration_count": final_state.get('iteration_count', 0),
                "retrieved_docs_count": len(retrieved_docs),
                "needs_retrieval": final_state.get('needs_retrieval', True),
                "dynamic_k": final_state.get('dynamic_k'),
                "query_complexity": final_state.get('query_complexity'),
                # 멀티턴 컨텍스트 평가용 필드 추가
                "slots_state": current_slots_state,
                "turn_updates": turn_updates,
                "retrieved_docs": retrieved_docs_summary,
                # 계층형 메모리 통계 (Agent 모드, hierarchical_memory_enabled일 때)
                "hierarchical_memory_stats": final_state.get('hierarchical_memory_stats'),
            }

            # 토큰 사용량 추정 (간단 계산)
            input_tokens = len(question.split()) * 1.3
            output_tokens = len(answer.split()) * 1.3
            usage = {
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens),
                "estimated_cost_usd": self._estimate_cost(int(input_tokens), int(output_tokens))
            }

            # ProfileStore 및 Hierarchical Memory 업데이트된 상태 반환 (다음 턴에서 재사용)
            updated_session_state = {
                'profile_store': final_state.get('profile_store'),
                'hierarchical_memory': final_state.get('hierarchical_memory')  # 메모리 검증용
            }
            
            # RAGAS 평가지표 계산 (설정에 따라)
            ragas_metrics = None
            if HAS_RAGAS_EVAL and self.config.get('evaluation', {}).get('per_turn_metrics'):
                retrieved_docs = final_state.get('retrieved_docs', [])
                # 검색된 문서에서 텍스트 추출
                contexts = []
                for doc in retrieved_docs:
                    if isinstance(doc, dict):
                        # doc이 딕셔너리인 경우 'text' 키 확인
                        doc_text = doc.get('text', '') or doc.get('content', '')
                        if doc_text:
                            contexts.append(doc_text)
                    elif isinstance(doc, str):
                        contexts.append(doc)
                
                # RAGAS 메트릭 계산 (Perplexity 포함)
                # 안전한 래퍼 함수 사용으로 모든 예외가 처리되지만, 이중 안전장치 추가
                try:
                    ragas_metrics = calculate_ragas_metrics_safe(
                        question=question,
                        answer=answer,
                        contexts=contexts,
                        include_perplexity=True,  # Perplexity 포함
                        conversation_history=conversation_history  # Perplexity 계산용
                    )
                    if ragas_metrics:
                        logger.info(f"RAGAS 메트릭 계산 완료: {list(ragas_metrics.keys())}")
                    else:
                        logger.debug("RAGAS 메트릭 계산 결과가 비어있습니다.")
                except Exception as e:
                    # calculate_ragas_metrics_safe는 이미 모든 예외를 처리하지만,
                    # 혹시 모를 예외 상황에 대비한 이중 안전장치
                    logger.warning(f"RAGAS 메트릭 계산 중 예외 발생 (실험 계속 진행): {e}")
                    ragas_metrics = None  # 명시적으로 None 설정

        except Exception as e:
            import traceback
            error_msg = f"Agent execution failed: {e}"
            logger.error(error_msg, exc_info=True)
            print(f"\n[ERROR] Agent 모드 실행 실패:")
            print(f"  환자: {patient_id}, 턴: {turn_id}")
            print(f"  질문: {question[:100]}...")
            print(f"  에러: {e}")
            print(f"  상세 정보:")
            traceback.print_exc()
            print()
            
            # API 할당량 초과나 인증 오류는 즉시 중단
            error_str = str(e).lower()
            if 'quota' in error_str or '429' in error_str or 'rate limit' in error_str:
                print(f"\n[CRITICAL] API 할당량 초과 또는 Rate Limit 도달!")
                print(f"  실험을 즉시 중단합니다.")
                raise RuntimeError(f"API 할당량 초과: {e}")
            elif '401' in error_str or 'unauthorized' in error_str or 'api key' in error_str:
                print(f"\n[CRITICAL] API 인증 실패!")
                print(f"  실험을 즉시 중단합니다.")
                raise RuntimeError(f"API 인증 실패: {e}")
            
            answer = "죄송합니다. 응답 생성 중 오류가 발생했습니다."
            usage = {"input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0}
            metadata = {"error": str(e)}
            updated_session_state = session_state

        end_time = datetime.now(timezone.utc)

        # ragas_metrics 변수 초기화 (예외 발생 시 None)
        if 'ragas_metrics' not in locals():
            ragas_metrics = None
        
        return {
            "answer": answer,
            "usage": usage,
            "metadata": metadata,
            "timing_ms": {
                "total": int((end_time - start_time).total_seconds() * 1000)
            },
            "timestamps": {
                "started_at_utc": start_time.isoformat(),
                "ended_at_utc": end_time.isoformat()
            },
            "session_state": updated_session_state,
            "ragas_metrics": ragas_metrics
        }

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """비용 추정 (GPT-4o-mini 기준)"""
        # GPT-4o-mini: $0.150 / 1M input tokens, $0.600 / 1M output tokens
        input_cost = (input_tokens / 1_000_000) * 0.150
        output_cost = (output_tokens / 1_000_000) * 0.600
        return input_cost + output_cost

    def _log_event(self, event: Dict):
        """이벤트 로깅 (events.jsonl)"""
        try:
            with open(self.events_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"이벤트 로깅 실패: {e}")
            # 로깅 실패는 실험을 중단하지 않음 (경고만)
            print(f"[WARNING] 이벤트 로깅 실패: {e}")
        except Exception as e:
            logger.error(f"이벤트 로깅 예상치 못한 오류: {e}")
            print(f"[WARNING] 이벤트 로깅 실패: {e}")

    def _generate_run_manifest(self):
        """실행 매니페스트 생성"""
        manifest = {
            "schema_version": "run_manifest.v1",
            "run_id": self.run_id,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "timezone": self.config['run']['timezone'],
            "config": self.config,
            "git": self._get_git_info(),
            "data": {
                "patient_count": len(self.patients),
                "question_bank_version": self.question_bank.get('version', 'N/A') if hasattr(self, 'question_bank') else 'N/A',
                "use_multiturn_scripts": self.use_multiturn_scripts,
                "multiturn_scripts_count": len(self.multiturn_scripts) if hasattr(self, 'multiturn_scripts') else 0
            },
            "logging": {
                "events_jsonl_path": str(self.events_log_path),
                "node_trace_jsonl_path": str(self.node_trace_log_path),
                "run_manifest_path": str(self.run_manifest_path)
            }
        }

        try:
            with open(self.run_manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"매니페스트 파일 저장 실패: {e}")
            raise
        except Exception as e:
            logger.error(f"매니페스트 파일 저장 예상치 못한 오류: {e}")
            raise

    def _generate_resolved_config(self, max_patients: Optional[int], max_turns: int):
        """
        Resolved configuration 생성 (논문 재현성용)

        실험의 모든 설정을 snapshot으로 저장하여 완벽한 재현성 확보
        """
        resolved_config_path = self.run_dir / "resolved_config.json"

        git_info = self._get_git_info()

        resolved_config = {
            "schema_version": "resolved_config.v1",
            "run_id": self.run_id,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "git_info": {
                "branch": git_info.get("branch", "unknown"),
                "commit_hash": git_info.get("commit_hash", "unknown"),
                "is_dirty": git_info.get("dirty_worktree", True)
            },
            "config": {
                "llm": {
                    "provider": self.config['llm']['provider'],
                    "model": self.config['llm']['model'],
                    "temperature": self.config['llm']['temperature'],
                    "max_tokens": self.config['llm']['max_tokens']
                },
                "modes": {
                    "run_order": self.config['modes']['run_order']
                },
                "features": {
                    "active_retrieval_enabled": self.config.get('features', {}).get('active_retrieval_enabled', False),
                    "context_compression_enabled": self.config.get('features', {}).get('context_compression_enabled', False),
                    "hierarchical_memory_enabled": self.config.get('features', {}).get('hierarchical_memory_enabled', False),
                    "self_refine_enabled": self.config.get('features', {}).get('self_refine_enabled', False)
                },
                "data": {
                    "patient_list_path": self.config['data']['patient_list_path'],
                    "profile_cards_dir": self.config['data']['profile_cards_dir']
                },
                "question_bank": {
                    "path": self.config['question_bank']['path'],
                    "selection_method": "deterministic_sha256",
                    "version": self.question_bank.get('version', 'unknown') if hasattr(self, 'question_bank') else 'N/A'
                },
                "run": {
                    "timezone": self.config['run']['timezone']
                }
            },
            "experiment_params": {
                "max_patients": max_patients if max_patients is not None else len(self.patients),
                "max_turns": max_turns
            }
        }

        try:
            with open(resolved_config_path, 'w', encoding='utf-8') as f:
                json.dump(resolved_config, f, ensure_ascii=False, indent=2)
            logger.info(f"Resolved config saved to: {resolved_config_path}")
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Resolved config 저장 실패: {e}")
            raise
        except Exception as e:
            logger.error(f"Resolved config 저장 예상치 못한 오류: {e}")
            raise

    def _get_git_info(self) -> Dict:
        """Git 정보 가져오기"""
        try:
            import subprocess

            branch = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=project_root
            ).decode().strip()

            commit = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                cwd=project_root
            ).decode().strip()

            return {
                "branch": branch,
                "commit_hash": commit[:10],
                "dirty_worktree": False
            }
        except:
            return {
                "branch": "unknown",
                "commit_hash": "unknown",
                "dirty_worktree": True
            }

    def run_experiment(self, max_patients: Optional[int] = None,
                      max_turns: int = 5):
        """
        실험 실행

        Args:
            max_patients: 최대 환자 수 (None이면 전체)
            max_turns: 최대 턴 수
        """
        logger.info(f"Starting experiment: {self.run_id}")
        logger.info(f"Patients: {len(self.patients)}, Max turns: {max_turns}")

        # 매니페스트 및 설정 스냅샷 생성
        self._generate_run_manifest()
        self._generate_resolved_config(max_patients, max_turns)

        # 환자별 실행
        patients_to_run = self.patients[:max_patients] if max_patients else self.patients

        for patient_info in patients_to_run:
            patient_id = patient_info['patient_id']
            logger.info(f"Processing patient: {patient_id}")

            # 프로파일 카드 로드
            try:
                profile_card = self._load_profile_card(patient_id)
            except FileNotFoundError:
                logger.warning(f"Profile card not found for {patient_id}, skipping...")
                print(f"[WARNING] 프로파일 카드를 찾을 수 없습니다: {patient_id} (건너뜀)")
                continue
            except Exception as e:
                logger.error(f"프로파일 카드 로드 실패 ({patient_id}): {e}")
                print(f"[ERROR] 프로파일 카드 로드 실패: {patient_id} - {e}")
                # 프로파일 카드 로드 실패는 해당 환자만 스킵
                continue

            # 모드별 실행
            for mode in self.config['modes']['run_order']:
                logger.info(f"  Mode: {mode}")

                conversation_history = []
                session_state = {}  # Agent 모드용 세션 상태
                profile_store = None  # Agent 모드용 ProfileStore
                previous_slots_state = {}  # 이전 턴 슬롯 상태 (turn_updates 계산용)

                # 5턴 실행
                for turn_id in range(1, max_turns + 1):
                    # 메모리 관리: 대화 히스토리가 너무 길어지면 압축 (선택적)
                    if len(conversation_history) > 20:  # 20턴 이상이면 경고
                        logger.warning(f"대화 히스토리가 길어집니다 ({len(conversation_history)}턴). 메모리 사용량을 모니터링하세요.")
                    logger.info(f"    Turn {turn_id}")

                    # 질문 선택
                    question_template = self._select_question(patient_id, turn_id)
                    
                    # 멀티턴 스크립트 모드면 이미 채워진 질문 사용
                    if self.use_multiturn_scripts:
                        question_text = question_template.get('question', question_template.get('template_text', ''))
                    else:
                        # 기존 방식: 플레이스홀더 채우기
                        original_template = question_template['template_text']
                        if '{' in original_template and '}' in original_template:
                            logger.debug(f"플레이스홀더 발견: {original_template[:100]}...")
                        
                        question_text = self._fill_placeholders(
                            question_template['template_text'],
                            profile_card,
                            turn_id
                        )
                    
                    # 플레이스홀더가 남아있는지 확인 (디버깅)
                    remaining_placeholders = [p for p in ['{AGE}', '{SEX_KO}', '{COND1_KO}', '{MED1_KO}', '{CC}', '{DUR}', '{TRIGGER}', '{VITAL_NAME}', '{LAB_NAME}', '{ALLERGY_KO}'] if p in question_text]
                    if remaining_placeholders:
                        logger.warning(f"⚠️ 플레이스홀더가 채워지지 않았습니다: {remaining_placeholders}")
                        logger.warning(f"   원본 템플릿: {original_template[:150]}")
                        logger.warning(f"   채워진 질문: {question_text[:150]}")
                        logger.warning(f"   프로필 카드 키: {list(profile_card.keys())}")
                        if 'demographics' in profile_card:
                            logger.warning(f"   demographics 키: {list(profile_card['demographics'].keys())}")
                        if 'clinical_summary' in profile_card:
                            logger.warning(f"   clinical_summary 키: {list(profile_card['clinical_summary'].keys())}")

                    # 모드별 실행
                    if mode == 'llm':
                        result = self._run_llm_mode(
                            question_text, patient_id, turn_id, conversation_history
                        )
                    else:  # agent
                        result = self._run_agent_mode(
                            question_text, patient_id, turn_id, conversation_history,
                            session_state, profile_store
                        )

                        # 세션 상태 업데이트 (다음 턴에서 재사용)
                        session_state = result.get('session_state', {})
                        profile_store = session_state.get('profile_store')
                        
                        # ProfileStore None 체크 (안정성)
                        if profile_store is None and mode == 'agent':
                            # Agent 모드에서는 ProfileStore가 있어야 함
                            logger.warning(f"ProfileStore가 None입니다. 새로 생성합니다. (환자: {patient_id}, 턴: {turn_id})")
                            from memory.profile_store import ProfileStore
                            profile_store = ProfileStore()
                            session_state['profile_store'] = profile_store
                        
                        # 이전 턴 슬롯 상태 저장 (다음 턴에서 turn_updates 계산용)
                        if mode == 'agent' and result.get('metadata', {}).get('slots_state'):
                            previous_slots_state = result['metadata']['slots_state']
                            session_state['previous_slots_state'] = previous_slots_state

                    # RAGAS 메트릭 추출 (result에서 가져오기)
                    ragas_metrics = result.get('ragas_metrics')
                    
                    # 멀티턴 컨텍스트 메트릭 계산 (CUS, UR, CCR)
                    multiturn_metrics = {}
                    if HAS_MULTITURN_METRICS and self.config.get('evaluation', {}).get('multiturn_metrics'):
                        try:
                            # 질문 뱅크에서 메타데이터 추출
                            question_metadata = get_question_metadata(
                                question_template,
                                question_text=question_text
                            )
                            required_slots = question_metadata.get('required_slots', [])
                            update_key = question_metadata.get('update_key')
                            
                            # 환자 프로필 로드 (CUS 계산용)
                            patient_profile = profile_card
                            
                            # CUS 계산 (required_slots가 있을 때만)
                            if required_slots:
                                try:
                                    # LLM 모드: slots_state가 없으므로 patient_profile만 사용
                                    # Agent 모드: slots_state 우선, 없으면 patient_profile
                                    slots_state = {}
                                    if mode == 'agent':
                                        slots_state = result.get('metadata', {}).get('slots_state', {})
                                    
                                    cus_result = compute_cus(
                                        answer=result['answer'],
                                        required_slots=required_slots,
                                        patient_profile=patient_profile,
                                        slots_state=slots_state
                                    )
                                    multiturn_metrics['CUS'] = cus_result.get('score', 0.0)
                                    multiturn_metrics['CUS_detail'] = cus_result
                                except Exception as e:
                                    logger.warning(f"CUS 계산 중 오류 (실험 계속 진행): {e}")
                            
                            # UR 계산 (update_key가 있을 때만)
                            if update_key:
                                try:
                                    # LLM 모드: turn_updates가 없으므로 None 전달
                                    # Agent 모드: turn_updates 사용
                                    turn_updates = {}
                                    if mode == 'agent':
                                        turn_updates = result.get('metadata', {}).get('turn_updates', {})
                                    
                                    ur_result = compute_ur(
                                        answer=result['answer'],
                                        update_key=update_key,
                                        turn_updates=turn_updates,
                                        question_text=question_text
                                    )
                                    if ur_result.get('applicable'):
                                        multiturn_metrics['UR'] = ur_result.get('score', 0.0)
                                        multiturn_metrics['UR_detail'] = ur_result
                                except Exception as e:
                                    logger.warning(f"UR 계산 중 오류 (실험 계속 진행): {e}")
                            
                            # CCR 계산 (모든 턴에서 계산)
                            try:
                                # LLM 모드: slots_state가 없으므로 빈 딕셔너리 사용
                                # Agent 모드: slots_state 사용
                                slots_state = {}
                                if mode == 'agent':
                                    slots_state = result.get('metadata', {}).get('slots_state', {})
                                
                                ccr_result = ccr_rule_checks(
                                    answer=result['answer'],
                                    slots_state=slots_state
                                )
                                multiturn_metrics['CCR'] = ccr_result.get('score', 0.0)
                                multiturn_metrics['CCR_detail'] = ccr_result
                            except Exception as e:
                                logger.warning(f"CCR 계산 중 오류 (실험 계속 진행): {e}")
                                
                        except Exception as e:
                            logger.warning(f"멀티턴 컨텍스트 메트릭 계산 중 오류 (실험 계속 진행): {e}")
                    
                    # 메트릭 통합 (RAGAS + 멀티턴 컨텍스트)
                    all_metrics = {}
                    if ragas_metrics:
                        all_metrics.update(ragas_metrics)
                    if multiturn_metrics:
                        # CUS, UR, CCR 점수만 추가 (detail은 제외)
                        for key, value in multiturn_metrics.items():
                            if key.endswith('_detail'):
                                continue
                            # 점수만 추가 (0.0~1.0 범위)
                            if isinstance(value, (int, float)):
                                all_metrics[key] = float(value)
                            elif isinstance(value, dict) and 'score' in value:
                                all_metrics[key] = float(value['score'])
                    
                    # 슬롯 정보 가져오기 (멀티턴 스크립트 모드일 때)
                    slots_truth = None
                    if self.use_multiturn_scripts and patient_id in self.multiturn_scripts:
                        slots_truth = self.multiturn_scripts[patient_id].get('slots', {})
                    
                    # 고급 평가 지표 계산 (SFS, CSP, CUS_improved)
                    # slots_truth가 있을 때만 계산
                    advanced_metrics = {}
                    if HAS_ADVANCED_METRICS and slots_truth:
                        try:
                            advanced_results = compute_advanced_metrics(
                                answer=result['answer'],
                                question=question_text,
                                slots_truth=slots_truth,
                                turn_id=turn_id,
                                config_dir="config/eval"
                            )
                            
                            # SFS 점수 추가
                            if 'SFS' in advanced_results:
                                sfs_result = advanced_results['SFS']
                                all_metrics['SFS'] = sfs_result.get('score', 0.0)
                                advanced_metrics['SFS_detail'] = sfs_result
                            
                            # CSP 점수 추가 (낮을수록 좋음)
                            if 'CSP' in advanced_results:
                                csp_result = advanced_results['CSP']
                                all_metrics['CSP'] = csp_result.get('score', 0.0)
                                advanced_metrics['CSP_detail'] = csp_result
                            
                            # CUS_improved 점수 추가 (기존 CUS 대신 또는 추가로)
                            if 'CUS_improved' in advanced_results:
                                cus_improved_result = advanced_results['CUS_improved']
                                all_metrics['CUS_improved'] = cus_improved_result.get('score', 0.0)
                                advanced_metrics['CUS_improved_detail'] = cus_improved_result
                                
                                # 기존 CUS가 없으면 CUS_improved를 CUS로도 사용
                                if 'CUS' not in all_metrics:
                                    all_metrics['CUS'] = cus_improved_result.get('score', 0.0)
                            
                            # ASS 점수 추가
                            if 'ASS' in advanced_results:
                                ass_result = advanced_results['ASS']
                                all_metrics['ASS'] = ass_result.get('score', 0.0)
                                advanced_metrics['ASS_detail'] = ass_result
                                    
                        except Exception as e:
                            logger.warning(f"고급 평가 지표 계산 중 오류 (실험 계속 진행): {e}")
                            import traceback
                            logger.debug(traceback.format_exc())
                    
                    # 계층형 메모리 검증 (Agent 모드에서만, hierarchical_memory_enabled일 때)
                    memory_verification_result = None
                    if (mode == 'agent' and 
                        self.memory_verification_enabled and 
                        self.memory_verifier and
                        result.get('session_state', {}).get('hierarchical_memory')):
                        try:
                            hierarchical_memory = result['session_state']['hierarchical_memory']
                            
                            # 예상 만성 질환 추출 (프로필 카드에서)
                            expected_chronic_conditions = None
                            if profile_card:
                                conditions = profile_card.get('clinical_summary', {}).get('conditions', [])
                                if conditions:
                                    # 만성 질환 키워드 포함된 것만
                                    chronic_keywords = ['당뇨', '고혈압', '심장', '신장', '간', 'diabetes', 'hypertension']
                                    expected_chronic_conditions = [
                                        c.get('name', '') for c in conditions
                                        if any(kw in c.get('name', '').lower() for kw in chronic_keywords)
                                    ]
                            
                            # 모든 Tier 검증
                            memory_verification_result = self.memory_verifier.verify_all_tiers(
                                hierarchical_memory=hierarchical_memory,
                                current_turn=turn_id,
                                expected_chronic_conditions=expected_chronic_conditions
                            )
                            
                            logger.debug(
                                f"메모리 검증 완료 (환자: {patient_id}, 턴: {turn_id}): "
                                f"Tier1={memory_verification_result.working_memory_verified}, "
                                f"Tier2={memory_verification_result.compressed_memory_verified}, "
                                f"Tier3={memory_verification_result.semantic_memory_verified}"
                            )
                            
                        except Exception as e:
                            logger.warning(f"메모리 검증 중 오류 (실험 계속 진행): {e}")
                            memory_verification_result = None
                    
                    # 이벤트 로깅
                    event = {
                        "schema_version": "events_record.v1",
                        "run_id": self.run_id,
                        "mode": mode,
                        "patient_id": patient_id,
                        "turn_id": turn_id,
                        "question": {
                            "question_id": question_template['id'],
                            "text": question_text,
                            "template": question_template.get('template_text', question_text)
                        },
                        "answer": {
                            "text": result['answer'],
                            "hash_sha256": hashlib.sha256(
                                result['answer'].encode()
                            ).hexdigest()
                        },
                        "usage": result['usage'],
                        "metadata": result.get('metadata', {}),
                        "timing_ms": result['timing_ms'],
                        "timestamps": result['timestamps'],
                        "metrics": all_metrics if all_metrics else None,  # RAGAS + 멀티턴 컨텍스트 메트릭
                        "memory_verification": memory_verification_result.to_dict() if memory_verification_result else None,  # 메모리 검증 결과
                        "slots_truth": slots_truth  # 평가용 슬롯 정보
                    }

                    self._log_event(event)

                    # 대화 히스토리 업데이트
                    conversation_history.append({
                        "question": question_text,
                        "answer": result['answer']
                    })

                    # 터미널에 질의/응답 출력 (9번 파일용)
                    print("\n" + "="*80)
                    print(f"[{mode.upper()}] 환자: {patient_id} | 턴: {turn_id}")
                    print("-"*80)
                    print(f"질문:")
                    print(f"  {question_text}")
                    print("-"*80)
                    print(f"답변:")
                    # 답변을 여러 줄로 나누어 출력 (가독성 향상)
                    answer_lines = result['answer'].split('\n')
                    for line in answer_lines:
                        if line.strip():
                            print(f"  {line}")
                        else:
                            print()
                    print("-"*80)
                    print(f"응답 시간: {result['timing_ms']['total']}ms")
                    if result.get('metadata'):
                        metadata = result['metadata']
                        if metadata.get('retrieved_docs_count') is not None:
                            print(f"검색 문서 수: {metadata.get('retrieved_docs_count', 0)}개")
                        if metadata.get('cache_hit'):
                            print(f"캐시 히트: 예")
                    print("="*80 + "\n")

                    logger.info(f"      Completed in {result['timing_ms']['total']}ms")

        logger.info(f"Experiment completed: {self.run_id}")
        logger.info(f"Results saved to: {self.run_dir}")
        
        # 메모리 검증 결과 저장
        if self.memory_verification_enabled and self.memory_verifier and self.memory_verifier.verification_results:
            verification_summary = self.memory_verifier.get_summary()
            logger.info(f"메모리 검증 요약: {verification_summary}")
            
            # 검증 결과 파일로 저장
            verification_path = self.run_dir / "memory_verification.json"
            self.memory_verifier.save_verification_results(str(verification_path))
            logger.info(f"메모리 검증 결과 저장: {verification_path}")


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Run multi-turn LLM vs Agent experiment (Improved Version)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='experiments/config.yaml',
        help='Path to experiment config file'
    )
    parser.add_argument(
        '--max-patients',
        type=int,
        default=None,
        help='Maximum number of patients to run (default: all)'
    )
    parser.add_argument(
        '--max-turns',
        type=int,
        default=5,
        help='Maximum number of turns per patient (default: 5)'
    )

    args = parser.parse_args()

    # 실험 실행
    runner = MultiTurnExperimentRunner(args.config)
    runner.run_experiment(
        max_patients=args.max_patients,
        max_turns=args.max_turns
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[중단] 사용자에 의해 실험이 중단되었습니다.")
        sys.exit(130)
    except Exception as e:
        import traceback
        print(f"\n[치명적 오류] 실험 실행 중 예외 발생:")
        print(f"  에러 타입: {type(e).__name__}")
        print(f"  에러 메시지: {e}")
        print(f"\n상세 스택 트레이스:")
        traceback.print_exc()
        sys.exit(1)
