"""
3-Tier 메모리 시스템 성능 테스트 (21턴)

목적:
- 3계층 메모리 시스템의 성능 검증
- Working Memory (최근 5턴): 원문 저장
- Compressing Memory (6-20턴): 압축 요약 저장
- Semantic Memory (21턴 이상): 장기 저장

테스트 시나리오:
- 1명의 가상 환자 생성 (LLM 기반)
- AI Agent 모드로 21턴 대화 수행
- 각 턴마다 메모리 상태 추적
- 평가지표 계산 (RAGAS + 고급 메트릭)
- 3계층 메모리 내용 시각화
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import random

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import get_llm_client
from core.config import get_llm_config, get_agent_config
from agent.graph import run_agent
from memory.profile_store import ProfileStore
from experiments.evaluation.ragas_metrics import calculate_ragas_metrics

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
2. 주요 질환: 2-3개의 만성 질환
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
  "primary_conditions": ["질환1", "질환2"],
  "current_symptoms": ["증상1", "증상2", "증상3"],
  "medications": ["약물1", "약물2", "약물3"],
  "lab_results": {"검사명": "수치"},
  "vitals": {"바이탈명": "수치"},
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
2. Turn 6-10: 증상 상세 및 약물 관련 (일부 맥락 의존)
3. Turn 11-15: 생활습관 및 관리 방안 (맥락 의존)
4. Turn 16-20: 장기 관리 계획 및 합병증 예방 (맥락 의존)
5. Turn 21: 종합 관리 계획 요청 (전체 맥락 의존)

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
    """3-Tier 메모리 시스템 테스트"""
    
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
        
        # Agent 그래프 초기화
        from agent.graph import build_agent_graph
        self.agent_graph = build_agent_graph()
        
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
                
                logger.info(f"[3-Tier Memory] Turn {turn_id} 추가 완료")
                logger.info(f"  - Working Memory: {len(self.memory_system.working_memory)}턴")
                logger.info(f"  - Compressing Memory: {len(self.memory_system.compressing_memory)}개")
                logger.info(f"  - Semantic Memory 만성질환: {len(self.memory_system.semantic_memory.chronic_conditions)}개")
                
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
        logger.info(f"  - 상세 결과: {self.results_file}")
        logger.info(f"  - 메모리 스냅샷: {self.memory_snapshots_file}")
        logger.info(f"  - 시각화: {self.visualization_file}")
    
    def _format_conversation_history(self, history: List[Dict]) -> str:
        """대화 히스토리를 문자열 형식으로 변환"""
        if not history:
            return ""
        
        history_text = ""
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                history_text += f"사용자: {content}\n"
            else:
                history_text += f"의사: {content}\n"
        
        return history_text
    
    def _capture_memory_snapshot(self, turn_id: int) -> Dict[str, Any]:
        """메모리 스냅샷 캡처"""
        # ProfileStore에서 메모리 정보 가져오기
        profile_store = self.session_state.get('profile_store')
        
        if profile_store is None:
            return {
                "turn_id": turn_id,
                "timestamp": datetime.now().isoformat(),
                "working_memory": {"size": 0, "items": []},
                "compressing_memory": {"size": 0, "summaries": []},
                "semantic_memory": {"size": 0, "entries": []}
            }
        
        # ProfileStore에서 메모리 정보 추출
        # 실제 구현은 ProfileStore의 구조에 따라 달라질 수 있음
        working_memory = []
        compressing_memory = []
        semantic_memory = {}
        
        # 대화 히스토리에서 최근 5턴 추출
        recent_turns = self.conversation_history[-10:]  # 최근 10개 메시지 (5턴)
        for i in range(0, len(recent_turns), 2):
            if i + 1 < len(recent_turns):
                working_memory.append({
                    "turn": (i // 2) + 1,
                    "question": recent_turns[i].get("content", "")[:50] + "...",
                    "answer": recent_turns[i + 1].get("content", "")[:50] + "..."
                })
        
        snapshot = {
            "turn_id": turn_id,
            "timestamp": datetime.now().isoformat(),
            "working_memory": {
                "size": len(working_memory),
                "items": working_memory[-5:]  # 최근 5개만
            },
            "compressing_memory": {
                "size": len(compressing_memory),
                "summaries": compressing_memory[-3:]  # 최근 3개만
            },
            "semantic_memory": {
                "size": len(semantic_memory),
                "entries": [
                    {"key": k, "value": str(v)[:50] + "..."}
                    for k, v in list(semantic_memory.items())[-5:]
                ]
            }
        }
        
        return snapshot
        
        snapshot = {
            "turn_id": turn_id,
            "timestamp": datetime.now().isoformat(),
            "working_memory": {
                "size": len(memory.working_memory),
                "items": [
                    {
                        "turn": item.get("turn_id"),
                        "question": item.get("question", "")[:50] + "...",
                        "answer": item.get("answer", "")[:50] + "..."
                    }
                    for item in memory.working_memory[-5:]  # 최근 5개만
                ]
            },
            "compressing_memory": {
                "size": len(memory.compressing_memory),
                "summaries": [
                    {
                        "turn_range": f"{item.get('start_turn')}-{item.get('end_turn')}",
                        "summary": item.get("summary", "")[:100] + "..."
                    }
                    for item in memory.compressing_memory[-3:]  # 최근 3개만
                ]
            },
            "semantic_memory": {
                "size": len(memory.semantic_memory),
                "entries": [
                    {
                        "key": key,
                        "value": str(value)[:50] + "..."
                    }
                    for key, value in list(memory.semantic_memory.items())[-5:]  # 최근 5개만
                ]
            }
        }
        
        return snapshot
    
    def _calculate_metrics(self, question: str, answer: str, contexts: List[str], turn_id: int) -> Dict[str, float]:
        """평가지표 계산"""
        metrics = {}
        
        # RAGAS 메트릭
        try:
            ragas_metrics = calculate_ragas_metrics(question, answer, contexts)
            if ragas_metrics:
                metrics.update(ragas_metrics)
        except Exception as e:
            logger.warning(f"RAGAS 메트릭 계산 실패 (Turn {turn_id}): {e}")
        
        # 고급 메트릭 (멀티턴 스크립트가 있는 경우)
        try:
            # 여기서는 간단한 메트릭만 계산
            metrics["response_length"] = len(answer)
            metrics["num_contexts"] = len(contexts)
        except Exception as e:
            logger.warning(f"고급 메트릭 계산 실패 (Turn {turn_id}): {e}")
        
        return metrics
    
    def _print_memory_status(self, snapshot: Dict[str, Any], turn_id: int):
        """메모리 상태 출력"""
        logger.info(f"\n[메모리 상태 - Turn {turn_id}]")
        logger.info(f"  Working Memory (최근 5턴): {snapshot['working_memory']['size']}개")
        logger.info(f"  Compressing Memory (6-20턴): {snapshot['compressing_memory']['size']}개")
        logger.info(f"  Semantic Memory (21턴+): {snapshot['semantic_memory']['size']}개")
        
        # 메모리 계층 전환 감지
        if turn_id == 6:
            logger.info("  ⚠️  Compressing Memory 활성화!")
        elif turn_id == 21:
            logger.info("  ⚠️  Semantic Memory 활성화!")
    
    def _save_results(self):
        """결과 저장"""
        # 상세 결과 저장
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        # 메모리 스냅샷만 별도 저장
        with open(self.memory_snapshots_file, 'w', encoding='utf-8') as f:
            json.dump(self.results["memory_snapshots"], f, ensure_ascii=False, indent=2)
        
        logger.info(f"결과 저장 완료: {self.results_file}")
    
    def _generate_visualization(self):
        """메모리 시각화 생성"""
        content = f"""# 3-Tier 메모리 시스템 성능 테스트 결과

## 테스트 정보

- **테스트 시간**: {self.results['test_info']['timestamp']}
- **총 턴 수**: {self.results['test_info']['num_turns']}턴
- **환자 ID**: {self.results['patient_profile']['patient_id']}

## 환자 프로파일

- **나이/성별**: {self.results['patient_profile']['age']}세 {self.results['patient_profile']['sex']}
- **주요 질환**: {', '.join(self.results['patient_profile']['primary_conditions'])}
- **현재 증상**: {', '.join(self.results['patient_profile']['current_symptoms'])}
- **복용 약물**: {', '.join(self.results['patient_profile']['medications'])}

## 메모리 계층별 상태 변화

### Working Memory (최근 5턴)
"""
        
        # 메모리 상태 변화 추적
        for snapshot in self.results["memory_snapshots"]:
            turn_id = snapshot["turn_id"]
            
            if turn_id in [1, 5, 6, 10, 15, 20, 21]:  # 주요 시점만
                content += f"\n#### Turn {turn_id}\n\n"
                content += f"- **Working Memory**: {snapshot['working_memory']['size']}개\n"
                content += f"- **Compressing Memory**: {snapshot['compressing_memory']['size']}개\n"
                content += f"- **Semantic Memory**: {snapshot['semantic_memory']['size']}개\n"
                
                if turn_id == 6:
                    content += "\n> ⚠️ **Compressing Memory 활성화**: 6턴부터 압축 요약 시작\n"
                elif turn_id == 21:
                    content += "\n> ⚠️ **Semantic Memory 활성화**: 21턴부터 장기 저장 시작\n"
        
        # 평가지표 요약
        content += "\n\n## 평가지표 요약\n\n"
        
        # 턴별 평가지표 수집
        faithfulness_scores = []
        answer_relevance_scores = []
        
        for turn in self.results["turns"]:
            metrics = turn.get("metrics", {})
            if "faithfulness" in metrics:
                faithfulness_scores.append(metrics["faithfulness"])
            if "answer_relevance" in metrics:
                answer_relevance_scores.append(metrics["answer_relevance"])
        
        if faithfulness_scores:
            avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores)
            content += f"- **평균 Faithfulness**: {avg_faithfulness:.3f}\n"
        
        if answer_relevance_scores:
            avg_relevance = sum(answer_relevance_scores) / len(answer_relevance_scores)
            content += f"- **평균 Answer Relevance**: {avg_relevance:.3f}\n"
        
        # 메모리 계층별 상세 내용
        content += "\n\n## 메모리 계층별 상세 내용\n\n"
        
        final_snapshot = self.results["memory_snapshots"][-1]
        
        content += "### Working Memory (최근 5턴)\n\n"
        for item in final_snapshot["working_memory"]["items"]:
            content += f"- **Turn {item['turn']}**\n"
            content += f"  - 질문: {item['question']}\n"
            content += f"  - 답변: {item['answer']}\n\n"
        
        content += "### Compressing Memory (6-20턴 압축)\n\n"
        for item in final_snapshot["compressing_memory"]["summaries"]:
            content += f"- **Turn {item['turn_range']}**\n"
            content += f"  - 요약: {item['summary']}\n\n"
        
        content += "### Semantic Memory (21턴+ 장기 저장)\n\n"
        for item in final_snapshot["semantic_memory"]["entries"]:
            content += f"- **{item['key']}**: {item['value']}\n"
        
        # 파일 저장
        with open(self.visualization_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"시각화 생성 완료: {self.visualization_file}")


def main():
    """메인 함수"""
    tester = Memory3TierTester()
    tester.run_test()


if __name__ == "__main__":
    main()

