"""
7, 8번 bat 파일에서 사용하는 이벤트 메트릭 확인 스크립트
"""
import json
import sys
from pathlib import Path

def check_metrics(run_dir: str):
    """이벤트 파일에서 메트릭 확인"""
    events_file = Path(run_dir) / "events.jsonl"
    
    if not events_file.exists():
        print(f"[오류] 이벤트 파일을 찾을 수 없습니다: {events_file}")
        return
    
    events = []
    with open(events_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"[경고] JSON 파싱 오류: {e}")
                continue
    
    if not events:
        print("[경고] 이벤트가 없습니다.")
        return
    
    # 턴별 응답 시간 확인 (8번용)
    print("\n[턴별 응답 시간 확인]")
    print("-" * 60)
    for e in events:
        turn_id = e.get('turn_id', '?')
        mode = e.get('mode', '?')
        timing_ms = e.get('timing_ms', {})
        total_ms = timing_ms.get('total', 'N/A') if timing_ms else 'N/A'
        print(f"Turn {turn_id} ({mode}): {total_ms}ms")
    
    # 평가지표 확인
    print("\n[평가지표 확인]")
    print("-" * 60)
    metrics_events = [e for e in events if e.get('metrics')]
    print(f"평가지표가 계산된 이벤트: {len(metrics_events)}/{len(events)}개")
    for e in metrics_events[:5]:
        turn_id = e.get('turn_id', '?')
        mode = e.get('mode', '?')
        metrics = e.get('metrics', {})
        metric_keys = list(metrics.keys()) if metrics else '없음'
        print(f"Turn {turn_id} ({mode}): 메트릭 = {metric_keys}")
    
    # 고급 평가지표 확인
    print("\n[고급 평가지표 확인 (SFS, CSP, CUS_improved, ASS)]")
    print("-" * 60)
    advanced_events = [
        e for e in events 
        if e.get('metrics') and (
            e.get('metrics', {}).get('SFS') is not None or 
            e.get('metrics', {}).get('CSP') is not None
        )
    ]
    print(f"고급 평가지표가 계산된 이벤트: {len(advanced_events)}/{len(events)}개")
    for e in advanced_events[:5]:
        turn_id = e.get('turn_id', '?')
        mode = e.get('mode', '?')
        metrics = e.get('metrics', {})
        sfs = metrics.get('SFS', 'N/A')
        csp = metrics.get('CSP', 'N/A')
        cus_improved = metrics.get('CUS_improved', 'N/A')
        ass = metrics.get('ASS', 'N/A')
        if isinstance(sfs, (int, float)):
            sfs = f"{sfs:.2f}"
        if isinstance(csp, (int, float)):
            csp = f"{csp:.2f}"
        if isinstance(cus_improved, (int, float)):
            cus_improved = f"{cus_improved:.2f}"
        if isinstance(ass, (int, float)):
            ass = f"{ass:.2f}"
        print(f"Turn {turn_id} ({mode}): SFS={sfs}, CSP={csp}, CUS_improved={cus_improved}, ASS={ass}")
    
    # 응답 샘플 확인 (8번용)
    if events:
        print("\n[응답 샘플 확인]")
        print("-" * 60)
        e = events[0]
        mode = e.get('mode', '?')
        question = e.get('question', {})
        question_text = question.get('text', '') if isinstance(question, dict) else str(question)
        answer = e.get('answer', '')
        print(f"Mode: {mode}")
        print(f"Question: {question_text[:100]}...")
        print(f"Answer: {answer[:200]}...")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python check_events_metrics.py <run_dir>")
        sys.exit(1)
    
    run_dir = sys.argv[1]
    check_metrics(run_dir)

