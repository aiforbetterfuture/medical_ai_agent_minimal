"""
후처리 평가 모듈 (Post-hoc Evaluator)

events.jsonl을 읽어서 평가 지표를 재계산하는 모듈
에이전트 로직과 완전히 분리되어 무결성을 보장
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

logger = logging.getLogger(__name__)

try:
    from .advanced_metrics import compute_advanced_metrics
    HAS_ADVANCED_METRICS = True
except ImportError:
    HAS_ADVANCED_METRICS = False
    logger.warning("고급 평가 지표 모듈을 로드할 수 없습니다.")


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    """JSONL 파일 읽기"""
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning(f"JSON 파싱 실패 (건너뜀): {e}")
    return rows


def evaluate_events_post_hoc(
    events_jsonl_path: str,
    output_jsonl_path: str,
    config_dir: str = "config/eval"
) -> None:
    """
    events.jsonl을 읽어서 평가 지표를 재계산
    
    Args:
        events_jsonl_path: 입력 events.jsonl 경로
        output_jsonl_path: 출력 평가 결과 JSONL 경로
        config_dir: 설정 파일 디렉토리
    """
    if not HAS_ADVANCED_METRICS:
        raise RuntimeError("고급 평가 지표 모듈이 없습니다. advanced_metrics.py를 확인하세요.")
    
    events = read_jsonl(events_jsonl_path)
    logger.info(f"총 {len(events)}개 이벤트 로드")
    
    results = []
    
    for event in events:
        patient_id = event.get('patient_id', 'unknown')
        mode = event.get('mode', 'unknown')
        turn_id = event.get('turn_id', 1)
        
        # 질문과 답변 추출
        question_data = event.get('question', {})
        answer_data = event.get('answer', {})
        
        question_text = question_data.get('text', '') if isinstance(question_data, dict) else str(question_data)
        answer_text = answer_data.get('text', '') if isinstance(answer_data, dict) else str(answer_data)
        
        # slots_truth 추출
        slots_truth = event.get('slots_truth')
        
        if not slots_truth:
            logger.debug(f"slots_truth가 없습니다. 건너뜁니다. (환자: {patient_id}, 턴: {turn_id})")
            continue
        
        # 고급 평가 지표 계산
        try:
            advanced_results = compute_advanced_metrics(
                answer=answer_text,
                question=question_text,
                slots_truth=slots_truth,
                turn_id=turn_id,
                config_dir=config_dir
            )
            
            # 결과 저장
            result = {
                "patient_id": patient_id,
                "mode": mode,
                "turn_id": turn_id,
                "question": question_text,
                "answer": answer_text,
                "metrics": {
                    "SFS": advanced_results.get('SFS', {}).get('score'),
                    "CSP": advanced_results.get('CSP', {}).get('score'),
                    "CUS_improved": advanced_results.get('CUS_improved', {}).get('score'),
                    "ASS": advanced_results.get('ASS', {}).get('score')
                },
                "details": {
                    "SFS": advanced_results.get('SFS', {}),
                    "CSP": advanced_results.get('CSP', {}),
                    "CUS_improved": advanced_results.get('CUS_improved', {}),
                    "ASS": advanced_results.get('ASS', {})
                }
            }
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"평가 지표 계산 실패 (환자: {patient_id}, 턴: {turn_id}): {e}")
            continue
    
    # 결과 저장
    output_path = Path(output_jsonl_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    logger.info(f"평가 결과 저장 완료: {output_path} ({len(results)}개 결과)")


def main():
    """CLI 진입점"""
    parser = argparse.ArgumentParser(
        description="events.jsonl을 읽어서 평가 지표를 재계산"
    )
    parser.add_argument(
        "--events",
        type=str,
        required=True,
        help="입력 events.jsonl 경로"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="출력 평가 결과 JSONL 경로"
    )
    parser.add_argument(
        "--config_dir",
        type=str,
        default="config/eval",
        help="설정 파일 디렉토리 (기본값: config/eval)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="상세 로그 출력"
    )
    
    args = parser.parse_args()
    
    # 로깅 설정
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 평가 실행
    evaluate_events_post_hoc(
        events_jsonl_path=args.events,
        output_jsonl_path=args.output,
        config_dir=args.config_dir
    )


if __name__ == "__main__":
    main()

