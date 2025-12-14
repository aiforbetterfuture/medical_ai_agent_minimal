"""
Basic RAG vs Corrective RAG 빠른 테스트

목적: 실험 스크립트가 제대로 작동하는지 확인
설정: 단일 쿼리만 테스트
"""

import json
import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent.graph import run_agent

# 간단한 테스트 쿼리
TEST_QUERY = "당뇨병이란 무엇인가요?"

print("="*80)
print("Basic RAG vs Corrective RAG 빠른 테스트")
print("="*80)
print(f"테스트 쿼리: {TEST_QUERY}")
print("="*80)

# Basic RAG 설정
basic_config = {
    'self_refine_enabled': False,
    'quality_check_enabled': False,
    'response_cache_enabled': False,
}

# Corrective RAG 설정
crag_config = {
    'self_refine_enabled': True,
    'quality_check_enabled': True,
    'llm_based_quality_check': True,
    'dynamic_query_rewrite': True,
    'max_refine_iterations': 2,
    'quality_threshold': 0.5,
    'response_cache_enabled': False,
}

print("\n[1/2] Basic RAG 실행 중...")
try:
    basic_result = run_agent(
        user_text=TEST_QUERY,
        mode='ai_agent',
        feature_overrides=basic_config,
        return_state=True
    )
    print(f"  [OK] 성공")
    print(f"    - 품질: {basic_result.get('quality_score', 0.0):.3f}")
    print(f"    - 반복: {basic_result.get('iteration_count', 0)}")
    print(f"    - 문서: {len(basic_result.get('retrieved_docs', []))}")
except Exception as e:
    print(f"  [FAIL] 실패: {e}")
    basic_result = None

print("\n[2/2] Corrective RAG 실행 중...")
try:
    crag_result = run_agent(
        user_text=TEST_QUERY,
        mode='ai_agent',
        feature_overrides=crag_config,
        return_state=True
    )
    print(f"  [OK] 성공")
    print(f"    - 품질: {crag_result.get('quality_score', 0.0):.3f}")
    print(f"    - 반복: {crag_result.get('iteration_count', 0)}")
    print(f"    - 문서: {len(crag_result.get('retrieved_docs', []))}")
except Exception as e:
    print(f"  [FAIL] 실패: {e}")
    crag_result = None

print("\n" + "="*80)
if basic_result and crag_result:
    print("[SUCCESS] 테스트 성공! 전체 실험을 실행할 준비가 되었습니다.")
    print("\n다음 명령어로 전체 실험 실행:")
    print("  run_basic_vs_crag_experiment.bat")
else:
    print("[WARNING] 테스트 실패. 설정을 확인해주세요.")
print("="*80)