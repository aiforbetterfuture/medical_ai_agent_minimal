"""
계층형 메모리 시스템 소모량 계산

80명 x 5턴 x 2모드 (LLM + Agent) = 160개 세션
AI Agent 모드에서만 계층형 메모리 사용

계산 항목:
1. 메모리 소모량 (작업 메모리 원본 저장)
2. 토큰 소모량 (압축 메모리 생성 시 LLM 호출)
3. 캐시 소모량 (메모리 상태 저장)
"""

import json
import math
from typing import Dict, Any
from pathlib import Path


def estimate_turn_size(user_query: str, agent_response: str, extracted_slots: Dict) -> int:
    """
    단일 턴의 크기 추정 (바이트)
    
    Args:
        user_query: 사용자 질문
        agent_response: 에이전트 답변
        extracted_slots: 추출된 슬롯
    
    Returns:
        예상 크기 (바이트)
    """
    # 텍스트 크기 (UTF-8 기준, 한국어는 평균 3바이트)
    query_bytes = len(user_query.encode('utf-8'))
    response_bytes = len(agent_response.encode('utf-8'))
    
    # 슬롯 크기 (JSON 직렬화)
    slots_json = json.dumps(extracted_slots, ensure_ascii=False)
    slots_bytes = len(slots_json.encode('utf-8'))
    
    # 메타데이터 (턴 ID, 타임스탬프 등) 약 200바이트
    metadata_bytes = 200
    
    total = query_bytes + response_bytes + slots_bytes + metadata_bytes
    return total


def estimate_compression_tokens(working_memory_turns: int) -> Dict[str, int]:
    """
    압축 메모리 생성 시 토큰 소모량 추정
    
    Args:
        working_memory_turns: 작업 메모리의 턴 수
    
    Returns:
        {'input_tokens': int, 'output_tokens': int}
    """
    # 평균 턴 크기 추정
    avg_turn_chars = 500  # 질문 + 답변 평균
    avg_turn_tokens = int(avg_turn_chars / 3)  # 한국어는 약 3자당 1토큰
    
    # 입력: 모든 턴 + 프롬프트
    prompt_tokens = 200  # 요약 프롬프트
    input_tokens = (avg_turn_tokens * working_memory_turns) + prompt_tokens
    
    # 출력: 요약 (200 토큰 이내)
    output_tokens = 200
    
    return {
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_tokens': input_tokens + output_tokens
    }


def calculate_memory_consumption(
    num_patients: int = 80,
    num_turns: int = 5,
    working_memory_capacity: int = 5,
    compression_threshold: int = 5
) -> Dict[str, Any]:
    """
    전체 메모리 소모량 계산
    
    Args:
        num_patients: 환자 수
        num_turns: 턴 수
        working_memory_capacity: 작업 메모리 용량
        compression_threshold: 압축 임계값
    
    Returns:
        소모량 통계
    """
    # AI Agent 모드만 계산 (LLM 모드는 메모리 사용 안 함)
    num_sessions = num_patients  # 1명당 1세션
    
    # 평균 턴 크기 추정 (실제 데이터 기반)
    avg_query_length = 150  # 평균 질문 길이 (자)
    avg_response_length = 500  # 평균 답변 길이 (자)
    avg_slots_size = 1000  # 평균 슬롯 크기 (바이트)
    
    # 1. 작업 메모리 (Tier 1) 소모량
    # 최근 5턴을 원본 형태로 저장
    avg_turn_size = estimate_turn_size(
        user_query='A' * avg_query_length,
        agent_response='B' * avg_response_length,
        extracted_slots={'conditions': [], 'medications': [], 'symptoms': [], 'vitals': []}
    )
    
    # 작업 메모리는 최대 5턴까지 저장 (deque maxlen=5)
    working_memory_per_session = avg_turn_size * working_memory_capacity
    total_working_memory = working_memory_per_session * num_sessions
    
    # 2. 압축 메모리 (Tier 2) 소모량
    # 5턴 도달 시 압축 수행
    num_compressions = num_turns // compression_threshold  # 5턴당 1회
    avg_compressed_size = 2000  # 압축된 요약 평균 크기 (바이트)
    compressed_memory_per_session = avg_compressed_size * num_compressions
    total_compressed_memory = compressed_memory_per_session * num_sessions
    
    # 3. 의미 메모리 (Tier 3) 소모량
    # 만성 질환, 약물, 알레르기 등 (작은 크기)
    avg_semantic_size = 500  # 의미 메모리 평균 크기 (바이트)
    total_semantic_memory = avg_semantic_size * num_sessions
    
    # 4. 토큰 소모량 (압축 시 LLM 호출)
    compression_tokens = estimate_compression_tokens(working_memory_capacity)
    total_compression_calls = num_compressions * num_sessions
    total_input_tokens = compression_tokens['input_tokens'] * total_compression_calls
    total_output_tokens = compression_tokens['output_tokens'] * total_compression_calls
    total_tokens = total_input_tokens + total_output_tokens
    
    # 5. 캐시 소모량 (메모리 상태 저장)
    # 각 세션의 메모리 상태를 캐시로 저장
    avg_cache_entry_size = (
        working_memory_per_session + 
        compressed_memory_per_session + 
        avg_semantic_size
    )
    total_cache_size = avg_cache_entry_size * num_sessions
    
    # 6. 비용 계산 (OpenAI GPT-4o-mini 기준)
    # Input: $0.15 / 1M tokens
    # Output: $0.60 / 1M tokens
    input_cost_per_1m = 0.15
    output_cost_per_1m = 0.60
    
    total_input_cost = (total_input_tokens / 1_000_000) * input_cost_per_1m
    total_output_cost = (total_output_tokens / 1_000_000) * output_cost_per_1m
    total_llm_cost = total_input_cost + total_output_cost
    
    return {
        'scenario': {
            'num_patients': num_patients,
            'num_turns': num_turns,
            'num_sessions': num_sessions,
            'working_memory_capacity': working_memory_capacity,
            'compression_threshold': compression_threshold
        },
        'memory_consumption': {
            'working_memory_per_session_bytes': working_memory_per_session,
            'total_working_memory_bytes': total_working_memory,
            'total_working_memory_mb': total_working_memory / (1024 * 1024),
            'compressed_memory_per_session_bytes': compressed_memory_per_session,
            'total_compressed_memory_bytes': total_compressed_memory,
            'total_compressed_memory_mb': total_compressed_memory / (1024 * 1024),
            'semantic_memory_per_session_bytes': avg_semantic_size,
            'total_semantic_memory_bytes': total_semantic_memory,
            'total_semantic_memory_mb': total_semantic_memory / (1024 * 1024),
            'total_memory_bytes': (
                total_working_memory + 
                total_compressed_memory + 
                total_semantic_memory
            ),
            'total_memory_mb': (
                total_working_memory + 
                total_compressed_memory + 
                total_semantic_memory
            ) / (1024 * 1024)
        },
        'token_consumption': {
            'compression_tokens_per_call': compression_tokens,
            'num_compression_calls': total_compression_calls,
            'total_input_tokens': total_input_tokens,
            'total_output_tokens': total_output_tokens,
            'total_tokens': total_tokens,
            'total_tokens_millions': total_tokens / 1_000_000
        },
        'cache_consumption': {
            'cache_entry_size_bytes': avg_cache_entry_size,
            'total_cache_size_bytes': total_cache_size,
            'total_cache_size_mb': total_cache_size / (1024 * 1024)
        },
        'cost_estimation': {
            'input_cost_usd': total_input_cost,
            'output_cost_usd': total_output_cost,
            'total_llm_cost_usd': total_llm_cost,
            'cost_per_session_usd': total_llm_cost / num_sessions if num_sessions > 0 else 0
        },
        'breakdown_per_session': {
            'working_memory_mb': working_memory_per_session / (1024 * 1024),
            'compressed_memory_mb': compressed_memory_per_session / (1024 * 1024),
            'semantic_memory_mb': avg_semantic_size / (1024 * 1024),
            'total_memory_mb': (
                working_memory_per_session + 
                compressed_memory_per_session + 
                avg_semantic_size
            ) / (1024 * 1024),
            'compression_calls': num_compressions,
            'tokens_per_compression': compression_tokens['total_tokens'],
            'total_tokens_per_session': compression_tokens['total_tokens'] * num_compressions
        }
    }


def print_consumption_report(consumption: Dict[str, Any]) -> None:
    """소모량 리포트 출력"""
    print("=" * 80)
    print("계층형 메모리 시스템 소모량 계산 리포트")
    print("=" * 80)
    print()
    
    scenario = consumption['scenario']
    print(f"시나리오:")
    print(f"  - 환자 수: {scenario['num_patients']}명")
    print(f"  - 턴 수: {scenario['num_turns']}턴/환자")
    print(f"  - 세션 수: {scenario['num_sessions']}개 (AI Agent 모드만)")
    print(f"  - 작업 메모리 용량: {scenario['working_memory_capacity']}턴")
    print(f"  - 압축 임계값: {scenario['compression_threshold']}턴")
    print()
    
    mem = consumption['memory_consumption']
    print("메모리 소모량:")
    print(f"  - 작업 메모리 (Tier 1): {mem['total_working_memory_mb']:.2f} MB")
    print(f"  - 압축 메모리 (Tier 2): {mem['total_compressed_memory_mb']:.2f} MB")
    print(f"  - 의미 메모리 (Tier 3): {mem['total_semantic_memory_mb']:.2f} MB")
    print(f"  - 총 메모리: {mem['total_memory_mb']:.2f} MB")
    print()
    
    tokens = consumption['token_consumption']
    print("토큰 소모량 (압축 메모리 생성 시):")
    print(f"  - 압축 호출 횟수: {tokens['num_compression_calls']}회")
    print(f"  - 총 입력 토큰: {tokens['total_input_tokens']:,} 토큰")
    print(f"  - 총 출력 토큰: {tokens['total_output_tokens']:,} 토큰")
    print(f"  - 총 토큰: {tokens['total_tokens']:,} 토큰 ({tokens['total_tokens_millions']:.3f}M)")
    print()
    
    cache = consumption['cache_consumption']
    print("캐시 소모량:")
    print(f"  - 총 캐시 크기: {cache['total_cache_size_mb']:.2f} MB")
    print()
    
    cost = consumption['cost_estimation']
    print("비용 추정 (OpenAI GPT-4o-mini 기준):")
    print(f"  - 입력 비용: ${cost['input_cost_usd']:.4f}")
    print(f"  - 출력 비용: ${cost['output_cost_usd']:.4f}")
    print(f"  - 총 LLM 비용: ${cost['total_llm_cost_usd']:.4f}")
    print(f"  - 세션당 비용: ${cost['cost_per_session_usd']:.6f}")
    print()
    
    breakdown = consumption['breakdown_per_session']
    print("세션당 소모량:")
    print(f"  - 작업 메모리: {breakdown['working_memory_mb']:.4f} MB")
    print(f"  - 압축 메모리: {breakdown['compressed_memory_mb']:.4f} MB")
    print(f"  - 의미 메모리: {breakdown['semantic_memory_mb']:.4f} MB")
    print(f"  - 총 메모리: {breakdown['total_memory_mb']:.4f} MB")
    print(f"  - 압축 호출: {breakdown['compression_calls']}회")
    print(f"  - 압축당 토큰: {breakdown['tokens_per_compression']:,} 토큰")
    print(f"  - 세션당 총 토큰: {breakdown['total_tokens_per_session']:,} 토큰")
    print()
    
    print("=" * 80)


if __name__ == '__main__':
    # 80명 x 5턴 시나리오 계산
    consumption = calculate_memory_consumption(
        num_patients=80,
        num_turns=5,
        working_memory_capacity=5,
        compression_threshold=5
    )
    
    print_consumption_report(consumption)
    
    # JSON으로 저장
    output_path = Path('runs/memory_consumption_report.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(consumption, f, indent=2, ensure_ascii=False)
    
    print(f"\n리포트 저장 완료: {output_path}")

