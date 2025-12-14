"""
3-Tier 메모리 시스템 성능 테스트 (21턴) - V2

목적:
- 3계층 메모리 시스템의 성능 검증
- Working Memory (최근 5턴): 원문 저장
- Compressing Memory (6-20턴): LLM 압축 요약 저장
- Semantic Memory (21턴 이상): MedCAT 기반 만성질환 장기 저장

개선사항:
- HierarchicalMemorySystem 활성화 및 초기화
- Compressing Memory LLM 요약 강화
- Semantic Memory MedCAT 연동 및 만성질환 추출
- 메모리 스냅샷 및 시각화 개선
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import get_llm_client
from agent.graph import run_agent
from memory.profile_store import ProfileStore
from memory.hierarchical_memory import HierarchicalMemorySystem
from experiments.evaluation.ragas_metrics import calculate_ragas_metrics_safe
from experiments.evaluation.advanced_metrics import AdvancedMetricsCalculator

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VirtualPatientGenerator:
    """가상 환자 생성기 (LLM 기반)"""
    
    def __init__(self):
        # OpenAI 클라이언트 직접 생성
        import openai
        self.openai_client = openai.OpenAI()
    
    def generate_patient_profile(self) -> Dict[str, Any]:
        """가상 환자 프로파일 생성"""
        prompt = """
당신은 의료 시나리오 생성 전문가입니다. 
21턴의 멀티턴 대화가 가능한 복잡한 의료 상황을 가진 가상 환자 프로파일을 생성하세요.

환자 프로파일 요구사항:
1. 기본 정보: 나이, 성별, 직업
2. 주요 질환: 2-3개의 만성 질환 (고혈압, 당뇨병 등)
3. 현재 증상: 최근 악화된 증상들
4. 복용 약물: 3-5개
5. 검사 결과: 주요 바이탈/검사 수치
6. 생활 습관: 운동, 식단, 수면 등
7. 우려 사항: 환자가 걱정하는 점들

JSON 형식으로 출력하세요:
{
  "patient_id": "VIRTUAL_001",
  "age": 숫자,
  "sex": "남성" 또는 "여성",
  "occupation": "직업",
  "primary_conditions": ["고혈압", "당뇨병"],
  "current_symptoms": ["증상1", "증상2", "증상3"],
  "medications": ["약물1", "약물2", "약물3"],
  "lab_results": {"HbA1c": "7.2%", "혈압": "145/90"},
  "vitals": {"체온": "36.5", "맥박": "78"},
  "lifestyle": {"운동": "설명", "식단": "설명", "수면": "설명"},
  "concerns": ["우려사항1", "우려사항2"]
}
"""
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        
        profile_text = response.choices[0].message.content.strip()
        
        # JSON 추출
        if "```json" in profile_text:
            profile_text = profile_text.split("```json")[1].split("```")[0].strip()
        elif "```" in profile_text:
            profile_text = profile_text.split("```")[1].split("```")[0].strip()
        
        profile = json.loads(profile_text)
        logger.info(f"가상 환자 생성 완료: {profile['patient_id']}")
        
        return profile
    
    def generate_questions(self, profile: Dict[str, Any], num_turns: int = 21) -> List[str]:
        """환자 프로파일 기반 21턴 질문 생성"""
        prompt = f"""
당신은 의료 시나리오 생성 전문가입니다.
다음 환자 프로파일을 기반으로 {num_turns}개의 질문을 생성하세요.

환자 프로파일:
{json.dumps(profile, ensure_ascii=False, indent=2)}

질문 생성 규칙:
1. Turn 1-5: 기본 정보 및 현재 상태 파악 (명시적)
   예: "고혈압과 당뇨병이 있다고 들었는데, 현재 어떤 증상이 있나요?"
2. Turn 6-10: 증상 상세 및 약물 관련 (일부 맥락 의존)
   예: "복용 중인 약물의 부작용은 없나요?"
3. Turn 11-15: 생활습관 및 관리 방안 (맥락 의존)
   예: "식단 관리는 어떻게 하고 계신가요?"
4. Turn 16-20: 장기 관리 계획 및 합병증 예방 (맥락 의존)
   예: "합병증 예방을 위해 어떤 검사가 필요한가요?"
5. Turn 21: 종합 관리 계획 요청 (전체 맥락 의존)
   예: "지금까지 이야기한 내용을 바탕으로 종합적인 관리 계획을 알려주세요."

각 질문은 이전 대화의 맥락을 참조하되, 점진적으로 더 복잡한 주제로 진행되어야 합니다.

JSON 배열 형식으로 출력하세요:
[
  "질문1",
  "질문2",
  ...
  "질문21"
]
"""
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=3000
        )
        
        questions_text = response.choices[0].message.content.strip()
        
        # JSON 추출
        if "```json" in questions_text:
            questions_text = questions_text.split("```json")[1].split("```")[0].strip()
        elif "```" in questions_text:
            questions_text = questions_text.split("```")[1].split("```")[0].strip()
        
        questions = json.loads(questions_text)
        logger.info(f"{len(questions)}개의 질문 생성 완료")
        
        return questions


class Memory3TierTester:
    """3-Tier 메모리 시스템 테스터"""
    
    def __init__(self, output_dir: str = "runs/3tier_memory_test"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 타임스탬프
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 결과 저장 경로
        self.results_file = self.output_dir / f"test_results_{self.timestamp}.json"
        self.memory_snapshots_file = self.output_dir / f"memory_snapshots_{self.timestamp}.json"
        self.visualization_file = self.output_dir / f"memory_visualization_{self.timestamp}.md"
        
        # 가상 환자 생성기
        self.patient_generator = VirtualPatientGenerator()
        
        # LLM 클라이언트 생성 (압축용)
        self.llm_client = get_llm_client(
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=2000
        )
        
        # 3-Tier 메모리 시스템 초기화 (중요!)
        self.memory_system = None  # run_test에서 환자 ID로 초기화
        
        # ProfileStore 초기화
        self.profile_store = ProfileStore()
        
        # 대화 히스토리 저장
        self.conversation_history = []
        
        # 세션 상태
        self.session_state = {
            'profile_store': self.profile_store
        }
        
        # 결과 저장
        self.results = {
            "test_info": {
                "timestamp": self.timestamp,
                "num_turns": 21,
                "test_type": "3-tier_memory_performance"
            },
            "patient_profile": None,
            "turns": [],
            "memory_snapshots": [],
            "metrics_summary": {}
        }
        
        # 평가지표 계산기
        self.advanced_metrics_calculator = AdvancedMetricsCalculator()
    
    def run_test(self):
        """21턴 테스트 실행"""
        logger.info("=" * 80)
        logger.info("3-Tier 메모리 시스템 성능 테스트 시작 (21턴)")
        logger.info("=" * 80)
        
        # 1. 가상 환자 생성
        logger.info("\n[1/4] 가상 환자 프로파일 생성 중...")
        patient_profile = self.patient_generator.generate_patient_profile()
        self.results["patient_profile"] = patient_profile
        
        logger.info(f"\n생성된 환자 정보:")
        logger.info(f"  - ID: {patient_profile['patient_id']}")
        logger.info(f"  - 나이/성별: {patient_profile['age']}세 {patient_profile['sex']}")
        logger.info(f"  - 주요 질환: {', '.join(patient_profile['primary_conditions'])}")
        logger.info(f"  - 현재 증상: {', '.join(patient_profile['current_symptoms'][:3])}...")
        
        # 3-Tier 메모리 시스템 초기화 (환자 ID로)
        self.memory_system = HierarchicalMemorySystem(
            user_id=patient_profile['patient_id'],
            working_capacity=5,
            compression_threshold=5,
            llm_client=self.llm_client,
            medcat_adapter=None,  # MedCAT 어댑터는 나중에 추가
            feature_flags={
                'hierarchical_memory_enabled': True  # 중요: 활성화!
            }
        )
        
        logger.info("\n[3-Tier Memory] 메모리 시스템 초기화 완료")
        logger.info(f"  - Working Memory 용량: {self.memory_system.working_capacity}턴")
        logger.info(f"  - Compression 임계값: {self.memory_system.compression_threshold}턴")
        logger.info(f"  - 메모리 시스템 활성화: {self.memory_system.enabled}")
        
        # 2. 21턴 질문 생성
        logger.info("\n[2/4] 21턴 질문 생성 중...")
        questions = self.patient_generator.generate_questions(patient_profile, num_turns=21)
        
        # 3. 21턴 대화 수행
        logger.info("\n[3/4] 21턴 대화 수행 중...")
        for turn_id in range(1, 22):
            logger.info(f"\n{'='*80}")
            logger.info(f"Turn {turn_id}/21")
            logger.info(f"{'='*80}")
            
            question = questions[turn_id - 1]
            logger.info(f"\n질문: {question[:100]}...")
            
            # 에이전트 응답 생성
            try:
                # 대화 히스토리 문자열 형식으로 변환
                history_text = self._format_conversation_history(self.conversation_history)
                
                # 세션 ID
                session_id = f"test_{self.timestamp}"
                user_id = patient_profile['patient_id']
                
                # run_agent 함수 호출
                final_state = run_agent(
                    user_text=question,
                    mode='ai_agent',
                    conversation_history=history_text,
                    session_state=self.session_state,
                    feature_overrides={},
                    return_state=True,
                    session_id=session_id,
                    user_id=user_id
                )
                
                # 응답 추출
                answer = final_state.get('final_answer', '')
                contexts = final_state.get('retrieved_docs', [])
                extracted_slots = final_state.get('slot_out', {})
                
                # 3-Tier 메모리에 턴 추가 (중요!)
                self.memory_system.add_turn(
                    user_query=question,
                    agent_response=answer,
                    extracted_slots=extracted_slots
                )
                
                logger.info(f"\n[3-Tier Memory] Turn {turn_id} 추가 완료")
                logger.info(f"  - Working Memory: {len(self.memory_system.working_memory)}턴")
                logger.info(f"  - Compressing Memory: {len(self.memory_system.compressing_memory)}개")
                logger.info(f"  - Semantic Memory 만성질환: {len(self.memory_system.semantic_memory.chronic_conditions)}개")
                logger.info(f"  - Semantic Memory 만성약물: {len(self.memory_system.semantic_memory.chronic_medications)}개")
                
                # 대화 히스토리 업데이트
                self.conversation_history.append({
                    "role": "user",
                    "content": question
                })
                self.conversation_history.append({
                    "role": "assistant",
                    "content": answer
                })
                
                logger.info(f"답변: {answer[:100]}...")
                logger.info(f"검색된 문서 수: {len(contexts)}개")
                
                # 메모리 스냅샷 저장
                memory_snapshot = self._capture_memory_snapshot(turn_id)
                
                # 평가지표 계산
                metrics = self._calculate_metrics(question, answer, contexts, turn_id)
                
                # 턴 결과 저장
                turn_result = {
                    "turn_id": turn_id,
                    "question": question,
                    "answer": answer,
                    "contexts": contexts[:3],  # 상위 3개만 저장
                    "num_contexts": len(contexts),
                    "metrics": metrics,
                    "memory_snapshot": memory_snapshot
                }
                
                self.results["turns"].append(turn_result)
                self.results["memory_snapshots"].append(memory_snapshot)
                
                # 메모리 상태 출력
                self._print_memory_status(memory_snapshot, turn_id)
                
            except Exception as e:
                logger.error(f"Turn {turn_id} 처리 중 오류: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # 4. 결과 저장 및 시각화
        logger.info("\n[4/4] 결과 저장 및 시각화 생성 중...")
        self._save_results()
        self._generate_visualization()
        
        logger.info("\n" + "=" * 80)
        logger.info("3-Tier 메모리 시스템 성능 테스트 완료!")
        logger.info("=" * 80)
        logger.info(f"\n결과 파일:")
        logger.info(f"  - 테스트 결과: {self.results_file}")
        logger.info(f"  - 메모리 스냅샷: {self.memory_snapshots_file}")
        logger.info(f"  - 시각화: {self.visualization_file}")
    
    def _format_conversation_history(self, history: List[Dict]) -> str:
        """대화 히스토리를 문자열로 변환"""
        if not history:
            return ""
        
        lines = []
        for msg in history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'user':
                lines.append(f"User: {content}")
            else:
                lines.append(f"Assistant: {content}")
        
        return "\n".join(lines)
    
    def _capture_memory_snapshot(self, turn_id: int) -> Dict[str, Any]:
        """메모리 스냅샷 캡처"""
        snapshot = {
            "turn_id": turn_id,
            "timestamp": datetime.now().isoformat(),
            "working_memory": {
                "size": len(self.memory_system.working_memory),
                "turns": [
                    {
                        "turn_id": turn.turn_id,
                        "user_query": turn.user_query[:100] + "..." if len(turn.user_query) > 100 else turn.user_query,
                        "agent_response": turn.agent_response[:100] + "..." if len(turn.agent_response) > 100 else turn.agent_response,
                        "importance": turn.importance
                    }
                    for turn in self.memory_system.working_memory
                ]
            },
            "compressing_memory": {
                "size": len(self.memory_system.compressing_memory),
                "memories": [
                    {
                        "memory_id": mem.memory_id,
                        "summary": mem.summary[:200] + "..." if len(mem.summary) > 200 else mem.summary,
                        "turn_range": mem.turn_range,
                        "importance": mem.importance,
                        "key_medical_info": {
                            "conditions": len(mem.key_medical_info.get('conditions', [])),
                            "medications": len(mem.key_medical_info.get('medications', [])),
                            "symptoms": len(mem.key_medical_info.get('symptoms', [])),
                            "vitals": len(mem.key_medical_info.get('vitals', []))
                        }
                    }
                    for mem in self.memory_system.compressing_memory
                ]
            },
            "semantic_memory": {
                "chronic_conditions": [
                    {
                        "name": cond.get('name', ''),
                        "frequency": cond.get('frequency', 0),
                        "verified_by": cond.get('verified_by', '')
                    }
                    for cond in self.memory_system.semantic_memory.chronic_conditions
                ],
                "chronic_medications": [
                    {
                        "name": med.get('name', ''),
                        "frequency": med.get('frequency', 0)
                    }
                    for med in self.memory_system.semantic_memory.chronic_medications
                ],
                "allergies": [
                    {
                        "name": allergy.get('name', ''),
                        "severity": allergy.get('severity', 'unknown')
                    }
                    for allergy in self.memory_system.semantic_memory.allergies
                ],
                "health_patterns": self.memory_system.semantic_memory.health_patterns
            },
            "metrics": self.memory_system.get_metrics()
        }
        
        return snapshot
    
    def _calculate_metrics(self, question: str, answer: str, contexts: List[Dict], turn_id: int) -> Dict[str, Any]:
        """평가지표 계산"""
        metrics = {}
        
        # RAGAS 메트릭 (안전하게)
        try:
            ragas_metrics = calculate_ragas_metrics_safe(
                question=question,
                answer=answer,
                contexts=[ctx.get('text', '') for ctx in contexts]
            )
            metrics['ragas'] = ragas_metrics
        except Exception as e:
            logger.warning(f"RAGAS 메트릭 계산 실패: {e}")
            metrics['ragas'] = {}
        
        # 고급 메트릭 (멀티턴 맥락)
        try:
            if turn_id > 1:
                # 이전 턴들의 질문/답변
                prev_turns = self.results["turns"][-5:] if len(self.results["turns"]) >= 5 else self.results["turns"]
                prev_questions = [t["question"] for t in prev_turns]
                prev_answers = [t["answer"] for t in prev_turns]
                
                advanced_metrics = self.advanced_metrics_calculator.calculate_all_metrics(
                    query=question,
                    response=answer,
                    retrieved_docs=contexts,
                    conversation_history=prev_questions + prev_answers
                )
                metrics['advanced'] = advanced_metrics
        except Exception as e:
            logger.warning(f"고급 메트릭 계산 실패: {e}")
            metrics['advanced'] = {}
        
        return metrics
    
    def _print_memory_status(self, snapshot: Dict[str, Any], turn_id: int):
        """메모리 상태 출력"""
        logger.info(f"\n[메모리 상태 - Turn {turn_id}]")
        logger.info(f"  Working Memory: {snapshot['working_memory']['size']}턴")
        logger.info(f"  Compressing Memory: {snapshot['compressing_memory']['size']}개")
        logger.info(f"  Semantic Memory:")
        logger.info(f"    - 만성질환: {len(snapshot['semantic_memory']['chronic_conditions'])}개")
        logger.info(f"    - 만성약물: {len(snapshot['semantic_memory']['chronic_medications'])}개")
        logger.info(f"    - 알레르기: {len(snapshot['semantic_memory']['allergies'])}개")
    
    def _save_results(self):
        """결과 저장"""
        # 테스트 결과 저장
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"테스트 결과 저장 완료: {self.results_file}")
        
        # 메모리 스냅샷 저장
        with open(self.memory_snapshots_file, 'w', encoding='utf-8') as f:
            json.dump(self.results["memory_snapshots"], f, indent=2, ensure_ascii=False)
        
        logger.info(f"메모리 스냅샷 저장 완료: {self.memory_snapshots_file}")
        
        # 메모리 시스템 자체 저장
        memory_file = self.output_dir / f"memory_system_{self.timestamp}.json"
        self.memory_system.save_to_file(str(memory_file))
        logger.info(f"메모리 시스템 저장 완료: {memory_file}")
    
    def _generate_visualization(self):
        """시각화 생성"""
        lines = []
        lines.append("# 3-Tier 메모리 시스템 테스트 결과\n")
        lines.append(f"**테스트 ID:** {self.results['test_info']['test_id']}\n")
        lines.append(f"**타임스탬프:** {self.results['test_info']['timestamp']}\n")
        lines.append(f"**총 턴 수:** {self.results['test_info']['num_turns']}\n")
        
        # 환자 정보
        patient = self.results["patient_profile"]
        lines.append("\n## 가상 환자 정보\n")
        lines.append(f"- **ID:** {patient['patient_id']}\n")
        lines.append(f"- **나이/성별:** {patient['age']}세 {patient['sex']}\n")
        lines.append(f"- **주요 질환:** {', '.join(patient['primary_conditions'])}\n")
        lines.append(f"- **현재 증상:** {', '.join(patient['current_symptoms'])}\n")
        lines.append(f"- **복용 약물:** {', '.join(patient['medications'])}\n")
        
        # 메모리 상태 변화
        lines.append("\n## 메모리 상태 변화\n")
        lines.append("| Turn | Working | Compressing | Semantic (만성질환) | Semantic (만성약물) |\n")
        lines.append("|------|---------|-------------|---------------------|---------------------|\n")
        
        for snapshot in self.results["memory_snapshots"]:
            turn_id = snapshot["turn_id"]
            working_size = snapshot["working_memory"]["size"]
            compressing_size = snapshot["compressing_memory"]["size"]
            chronic_conds = len(snapshot["semantic_memory"]["chronic_conditions"])
            chronic_meds = len(snapshot["semantic_memory"]["chronic_medications"])
            lines.append(f"| {turn_id} | {working_size} | {compressing_size} | {chronic_conds} | {chronic_meds} |\n")
        
        # 최종 메모리 상태
        final_snapshot = self.results["memory_snapshots"][-1]
        lines.append("\n## 최종 메모리 상태\n")
        
        lines.append("\n### Working Memory (최근 5턴)\n")
        for turn in final_snapshot["working_memory"]["turns"]:
            lines.append(f"- **Turn {turn['turn_id']}** (중요도: {turn['importance']:.2f})\n")
            lines.append(f"  - 질문: {turn['user_query']}\n")
            lines.append(f"  - 답변: {turn['agent_response']}\n")
        
        lines.append("\n### Compressing Memory (압축된 과거)\n")
        for mem in final_snapshot["compressing_memory"]["memories"]:
            lines.append(f"- **Memory {mem['memory_id']}** (Turn {mem['turn_range'][0]}-{mem['turn_range'][1]}, 중요도: {mem['importance']:.2f})\n")
            lines.append(f"  - 요약: {mem['summary']}\n")
            lines.append(f"  - 핵심 정보: 질환 {mem['key_medical_info']['conditions']}개, 약물 {mem['key_medical_info']['medications']}개\n")
        
        lines.append("\n### Semantic Memory (장기 메모리)\n")
        lines.append("\n#### 만성 질환\n")
        for cond in final_snapshot["semantic_memory"]["chronic_conditions"]:
            lines.append(f"- **{cond['name']}** (언급 {cond['frequency']}회, 검증: {cond['verified_by']})\n")
        
        lines.append("\n#### 만성 약물\n")
        for med in final_snapshot["semantic_memory"]["chronic_medications"]:
            lines.append(f"- **{med['name']}** (언급 {med['frequency']}회)\n")
        
        lines.append("\n#### 알레르기\n")
        if final_snapshot["semantic_memory"]["allergies"]:
            for allergy in final_snapshot["semantic_memory"]["allergies"]:
                lines.append(f"- **{allergy['name']}** (심각도: {allergy['severity']})\n")
        else:
            lines.append("- 없음\n")
        
        lines.append("\n#### 건강 패턴\n")
        patterns = final_snapshot["semantic_memory"]["health_patterns"]
        if patterns:
            for key, value in patterns.items():
                lines.append(f"- **{key}:** {value}\n")
        else:
            lines.append("- 없음\n")
        
        # 메트릭 통계
        lines.append("\n## 메모리 시스템 메트릭\n")
        metrics = final_snapshot["metrics"]
        lines.append(f"- **총 턴 수:** {metrics['total_turns']}\n")
        lines.append(f"- **압축 수행 횟수:** {metrics['compressions_performed']}\n")
        lines.append(f"- **Semantic Memory 업데이트 횟수:** {metrics['semantic_updates']}\n")
        lines.append(f"- **평균 압축 시간:** {metrics['avg_compression_time_ms']:.2f}ms\n")
        lines.append(f"- **Working Memory 히트:** {metrics['working_memory_hits']}\n")
        lines.append(f"- **Compressing Memory 히트:** {metrics['compressing_memory_hits']}\n")
        lines.append(f"- **Semantic Memory 히트:** {metrics['semantic_memory_hits']}\n")
        
        # 파일 저장
        with open(self.visualization_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        logger.info(f"시각화 생성 완료: {self.visualization_file}")


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="3-Tier 메모리 시스템 성능 테스트 (21턴)")
    parser.add_argument('--output-dir', type=str, default='runs/3tier_memory_test',
                        help='결과 저장 디렉토리')
    
    args = parser.parse_args()
    
    # 테스터 생성 및 실행
    tester = Memory3TierTester(output_dir=args.output_dir)
    tester.run_test()


if __name__ == "__main__":
    main()

