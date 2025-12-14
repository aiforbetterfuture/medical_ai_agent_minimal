"""
멀티턴 실험 메인 실행 스크립트
LLM vs AI Agent 성능 비교를 위한 80명 x 5턴 실험 실행
"""

import json
import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import yaml
import logging

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent.graph import create_agent_graph
from openai import OpenAI


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiTurnExperimentRunner:
    """멀티턴 실험 실행기"""

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

        # 환자 리스트 및 질문 뱅크 로드
        self.patients = self._load_patients()
        self.question_bank = self._load_question_bank()

        # OpenAI 클라이언트 초기화
        self.client = OpenAI()

    def _load_config(self) -> Dict:
        """설정 파일 로드"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_patients(self) -> List[Dict]:
        """환자 리스트 로드"""
        patient_list_path = Path(self.config['data']['patient_list_path'])
        with open(patient_list_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['patients']

    def _load_question_bank(self) -> Dict:
        """질문 뱅크 로드"""
        question_bank_path = Path(self.config['question_bank']['path'])
        with open(question_bank_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_profile_card(self, patient_id: str) -> Dict:
        """환자 프로파일 카드 로드"""
        profile_cards_dir = Path(self.config['data']['profile_cards_dir'])
        profile_path = profile_cards_dir / f"{patient_id}.json"

        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _select_question(self, patient_id: str, turn_id: int) -> Dict:
        """
        Deterministic 질문 선택
        SHA256(patient_id + ':' + turn_id) % 15
        """
        selection_key = f"{patient_id}:{turn_id}"
        hash_digest = hashlib.sha256(selection_key.encode()).hexdigest()
        index = int(hash_digest, 16) % 15

        # 해당 턴의 질문들 필터링
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

    def _run_llm_mode(self, question: str, patient_id: str, turn_id: int,
                     conversation_history: List[Dict]) -> Dict:
        """LLM 모드 실행 (단순 OpenAI API 호출)"""
        start_time = datetime.now(timezone.utc)

        # 시스템 프롬프트
        system_prompt = """당신은 의료 상담 AI입니다. 환자의 질문에 답변하되:
1. 확정 진단은 하지 않습니다
2. 근거 기반으로 설명합니다
3. 위험 신호가 있으면 반드시 언급합니다
4. 응급 상황이면 즉시 의료기관 방문을 권고합니다"""

        # 대화 히스토리 구성
        messages = [{"role": "system", "content": system_prompt}]

        # 이전 턴 포함
        for hist in conversation_history:
            messages.append({"role": "user", "content": hist['question']})
            messages.append({"role": "assistant", "content": hist['answer']})

        # 현재 질문
        messages.append({"role": "user", "content": question})

        # API 호출
        try:
            response = self.client.chat.completions.create(
                model=self.config['llm']['model'],
                messages=messages,
                temperature=self.config['llm']['temperature'],
                max_tokens=self.config['llm']['max_tokens']
            )

            answer = response.choices[0].message.content
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "estimated_cost_usd": self._estimate_cost(
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens
                )
            }

        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            answer = "죄송합니다. 응답 생성 중 오류가 발생했습니다."
            usage = {"input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0}

        end_time = datetime.now(timezone.utc)

        return {
            "answer": answer,
            "usage": usage,
            "timing_ms": {
                "total": int((end_time - start_time).total_seconds() * 1000)
            },
            "timestamps": {
                "started_at_utc": start_time.isoformat(),
                "ended_at_utc": end_time.isoformat()
            }
        }

    def _run_agent_mode(self, question: str, patient_id: str, turn_id: int,
                       conversation_history: List[Dict]) -> Dict:
        """Agent 모드 실행 (LangGraph 기반)"""
        start_time = datetime.now(timezone.utc)

        # Agent 그래프 생성
        try:
            graph = create_agent_graph()

            # 초기 상태
            state = {
                "question": question,
                "patient_id": patient_id,
                "turn_id": turn_id,
                "conversation_history": conversation_history,
                "context": "",
                "answer": "",
                "metadata": {}
            }

            # 실행
            result = graph.invoke(state)

            answer = result.get("answer", "")
            metadata = result.get("metadata", {})

            usage = metadata.get("usage", {
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost_usd": 0
            })

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            answer = "죄송합니다. 응답 생성 중 오류가 발생했습니다."
            usage = {"input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0}
            metadata = {}

        end_time = datetime.now(timezone.utc)

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
            }
        }

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """비용 추정 (GPT-4o-mini 기준)"""
        # GPT-4o-mini: $0.150 / 1M input tokens, $0.600 / 1M output tokens
        input_cost = (input_tokens / 1_000_000) * 0.150
        output_cost = (output_tokens / 1_000_000) * 0.600
        return input_cost + output_cost

    def _log_event(self, event: Dict):
        """이벤트 로깅 (events.jsonl)"""
        with open(self.events_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')

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
                "question_bank_version": self.question_bank['version']
            },
            "logging": {
                "events_jsonl_path": str(self.events_log_path),
                "node_trace_jsonl_path": str(self.node_trace_log_path),
                "run_manifest_path": str(self.run_manifest_path)
            }
        }

        with open(self.run_manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

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

        # 매니페스트 생성
        self._generate_run_manifest()

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
                continue

            # 모드별 실행
            for mode in self.config['modes']['run_order']:
                logger.info(f"  Mode: {mode}")

                conversation_history = []

                # 5턴 실행
                for turn_id in range(1, max_turns + 1):
                    logger.info(f"    Turn {turn_id}")

                    # 질문 선택
                    question_template = self._select_question(patient_id, turn_id)
                    question_text = self._fill_placeholders(
                        question_template['template_text'],
                        profile_card,
                        turn_id
                    )

                    # 모드별 실행
                    if mode == 'llm':
                        result = self._run_llm_mode(
                            question_text, patient_id, turn_id, conversation_history
                        )
                    else:  # agent
                        result = self._run_agent_mode(
                            question_text, patient_id, turn_id, conversation_history
                        )

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
                            "template": question_template['template_text']
                        },
                        "answer": {
                            "text": result['answer'],
                            "hash_sha256": hashlib.sha256(
                                result['answer'].encode()
                            ).hexdigest()
                        },
                        "usage": result['usage'],
                        "timing_ms": result['timing_ms'],
                        "timestamps": result['timestamps']
                    }

                    self._log_event(event)

                    # 대화 히스토리 업데이트
                    conversation_history.append({
                        "question": question_text,
                        "answer": result['answer']
                    })

                    logger.info(f"      Completed in {result['timing_ms']['total']}ms")

        logger.info(f"Experiment completed: {self.run_id}")
        logger.info(f"Results saved to: {self.run_dir}")


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Run multi-turn LLM vs Agent experiment'
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
    main()
