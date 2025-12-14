"""
멀티턴 지표 계산 모듈
Context Utilization, Context Contradiction, Update Responsiveness 등
"""

import json
from typing import Dict, List, Any
from pathlib import Path
import re


class MultiTurnMetrics:
    """멀티턴 특화 지표 계산"""

    def __init__(self):
        pass

    def calculate_context_utilization(
        self,
        answer: str,
        required_context_slots: List[str],
        conversation_history: List[Dict]
    ) -> float:
        """
        Context Utilization Score (CUS)
        이전 턴의 주어진 환자 정보를 답변에서 활용했는지 측정

        Args:
            answer: 현재 턴의 답변
            required_context_slots: 사용해야 할 슬롯 (예: 약물, 질환)
            conversation_history: 이전 대화 히스토리

        Returns:
            0.0 ~ 1.0 사이의 점수
        """
        if not required_context_slots:
            return 1.0

        utilized_count = 0
        for slot in required_context_slots:
            # 슬롯이 답변에 언급되었는지 확인 (단순 문자열 매칭)
            if slot.lower() in answer.lower():
                utilized_count += 1

        return utilized_count / len(required_context_slots)

    def calculate_context_contradiction(
        self,
        answer: str,
        conversation_history: List[Dict],
        safety_keywords: List[str] = None
    ) -> float:
        """
        Context Contradiction Rate (CCR)
        이전 턴 정보와 모순되는 위험한 조언을 하는지 측정

        Args:
            answer: 현재 턴의 답변
            conversation_history: 이전 대화 히스토리
            safety_keywords: 금기 키워드 리스트

        Returns:
            0.0 (모순 없음) ~ 1.0 (심각한 모순) 사이의 점수
        """
        if safety_keywords is None:
            safety_keywords = [
                "운동하세요", "운동을 권장",  # 심혈관 증상 시 위험
                "괜찮습니다", "걱정 안 하셔도",  # 응급 상황 시 위험
            ]

        contradiction_score = 0.0

        # 이전 히스토리에서 위험 신호 확인
        has_risk_signals = False
        risk_keywords = ["흉통", "호흡곤란", "어지러움", "혈압 상승"]

        for hist in conversation_history:
            question = hist.get('question', '').lower()
            for keyword in risk_keywords:
                if keyword in question:
                    has_risk_signals = True
                    break

        # 위험 신호가 있는데 안전하지 않은 조언을 하면 모순
        if has_risk_signals:
            for keyword in safety_keywords:
                if keyword in answer:
                    contradiction_score += 0.3

        return min(contradiction_score, 1.0)

    def calculate_update_responsiveness(
        self,
        answer: str,
        turn_id: int,
        new_information: Dict
    ) -> float:
        """
        Update Responsiveness (UR)
        Turn3에서 새로 들어온 수치/증상 변화가 답변에 반영되는지 측정

        Args:
            answer: 현재 턴의 답변
            turn_id: 현재 턴 번호
            new_information: 새로운 정보 (예: 바이탈 업데이트)

        Returns:
            0.0 ~ 1.0 사이의 점수
        """
        if turn_id != 3:
            return 1.0  # Turn 3이 아니면 평가하지 않음

        # 새 정보가 답변에 언급되었는지 확인
        responsiveness_score = 0.0

        for key, value in new_information.items():
            if isinstance(value, str):
                if value.lower() in answer.lower():
                    responsiveness_score += 0.5
            elif isinstance(value, dict):
                # 중첩 딕셔너리 처리 (예: vital 정보)
                for subkey, subvalue in value.items():
                    if str(subvalue).lower() in answer.lower():
                        responsiveness_score += 0.5

        return min(responsiveness_score, 1.0)

    def evaluate_turn(
        self,
        turn_data: Dict,
        conversation_history: List[Dict],
        profile_card: Dict
    ) -> Dict[str, float]:
        """
        단일 턴 평가

        Args:
            turn_data: 턴 데이터 (events.jsonl의 한 줄)
            conversation_history: 이전 대화 히스토리
            profile_card: 환자 프로파일 카드

        Returns:
            지표별 점수 딕셔너리
        """
        answer = turn_data.get('answer', {}).get('text', '')
        turn_id = turn_data.get('turn_id', 1)

        # Turn 2: Context Utilization (약물/질환 슬롯 활용)
        cus = 1.0
        if turn_id == 2:
            required_slots = []
            medications = profile_card.get('clinical_summary', {}).get('medications', [])
            conditions = profile_card.get('clinical_summary', {}).get('conditions', [])

            if medications:
                required_slots.append(medications[0]['name'].split()[0])
            if conditions:
                required_slots.append(conditions[0]['name'])

            cus = self.calculate_context_utilization(
                answer, required_slots, conversation_history
            )

        # Context Contradiction
        ccr = self.calculate_context_contradiction(
            answer, conversation_history
        )

        # Turn 3: Update Responsiveness
        ur = 1.0
        if turn_id == 3:
            new_info = profile_card.get('turn_injection_fields', {}).get(
                'T3_update_event', {}
            ).get('payload', {})
            ur = self.calculate_update_responsiveness(
                answer, turn_id, new_info
            )

        return {
            "context_utilization": cus,
            "context_contradiction": ccr,
            "update_responsiveness": ur
        }


def analyze_events_log(events_jsonl_path: str, profile_cards_dir: str) -> Dict:
    """
    events.jsonl 분석 및 지표 계산

    Args:
        events_jsonl_path: events.jsonl 파일 경로
        profile_cards_dir: 프로파일 카드 디렉토리

    Returns:
        집계된 메트릭
    """
    metrics_calculator = MultiTurnMetrics()

    # 이벤트 로드
    events = []
    with open(events_jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            events.append(json.loads(line))

    # 환자별/모드별 그룹화
    results = {}

    for event in events:
        patient_id = event['patient_id']
        mode = event['mode']
        turn_id = event['turn_id']

        key = f"{patient_id}_{mode}"
        if key not in results:
            results[key] = {
                "patient_id": patient_id,
                "mode": mode,
                "turns": {},
                "conversation_history": []
            }

        # 프로파일 카드 로드
        profile_card_path = Path(profile_cards_dir) / f"{patient_id}.json"
        with open(profile_card_path, 'r', encoding='utf-8') as f:
            profile_card = json.load(f)

        # 턴 평가
        turn_metrics = metrics_calculator.evaluate_turn(
            event,
            results[key]["conversation_history"],
            profile_card
        )

        results[key]["turns"][turn_id] = {
            "metrics": turn_metrics,
            "answer": event['answer']['text'],
            "question": event['question']['text']
        }

        # 대화 히스토리 업데이트
        results[key]["conversation_history"].append({
            "question": event['question']['text'],
            "answer": event['answer']['text']
        })

    # 집계
    summary = {
        "llm": {"cus": [], "ccr": [], "ur": []},
        "agent": {"cus": [], "ccr": [], "ur": []}
    }

    for key, data in results.items():
        mode = data['mode']
        for turn_id, turn_data in data['turns'].items():
            metrics = turn_data['metrics']
            summary[mode]["cus"].append(metrics["context_utilization"])
            summary[mode]["ccr"].append(metrics["context_contradiction"])
            summary[mode]["ur"].append(metrics["update_responsiveness"])

    # 평균 계산
    for mode in ["llm", "agent"]:
        for metric in ["cus", "ccr", "ur"]:
            values = summary[mode][metric]
            summary[mode][f"{metric}_mean"] = sum(values) / len(values) if values else 0

    return summary


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python multiturn_metrics.py <events.jsonl> <profile_cards_dir>")
        sys.exit(1)

    events_path = sys.argv[1]
    profiles_dir = sys.argv[2]

    summary = analyze_events_log(events_path, profiles_dir)

    print("\n=== Multi-Turn Metrics Summary ===\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
