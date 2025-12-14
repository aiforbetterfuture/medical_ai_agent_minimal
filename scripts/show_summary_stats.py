#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
show_summary_stats.py
- summary.json을 읽어서 주요 통계를 출력
- 경로 문제 해결을 위해 별도 스크립트로 분리
"""

import json
import sys
import os
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("[오류] run_dir 또는 summary.json 경로가 필요합니다.")
        sys.exit(1)
    
    arg = sys.argv[1]
    # summary.json 직접 경로인지 확인
    if arg.endswith("summary.json") and os.path.exists(arg):
        summary_path = arg
    else:
        # run_dir로 간주
        run_dir = arg
        summary_path = os.path.join(run_dir, "summary.json")
    
    if not os.path.exists(summary_path):
        print(f"[오류] summary.json을 찾을 수 없습니다: {summary_path}")
        sys.exit(1)
    
    # UTF-8 출력 설정
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    try:
        with open(summary_path, 'r', encoding='utf-8') as f:
            s = json.load(f)
        
        # 통계 추출
        total = s.get('counts', {}).get('total_events', 0)
        llm_lat = s.get('efficiency', {}).get('latency', {}).get('by_mode', {}).get('llm', {}).get('mean', 0)
        agent_lat = s.get('efficiency', {}).get('latency', {}).get('by_mode', {}).get('agent', {}).get('mean', 0)
        comps = s.get('comparisons', {}).get('paired_agent_minus_llm', [])
        
        # 첫 번째 비교 결과에서 p-value와 Cohen's d 추출
        if comps:
            pval = comps[0].get('t_test_p_value', 0)
            cohen_d = comps[0].get('effect_size_cohens_d', 0)
        else:
            pval = 0
            cohen_d = 0
        
        # 출력
        print(f'총 이벤트 수: {total}')
        print(f'LLM 평균 응답시간: {llm_lat:.0f}ms')
        print(f'Agent 평균 응답시간: {agent_lat:.0f}ms')
        print(f'p-value: {pval:.6f}')
        print(f'Cohen d: {cohen_d:.3f}')
        
    except Exception as e:
        print(f"[오류] 통계 출력 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

