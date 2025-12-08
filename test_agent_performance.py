"""
Agent 실제 실행 성능 테스트
API 키가 필요한 경우 스킵
"""

import time
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent.graph import run_agent, get_agent_graph
from dotenv import load_dotenv

# .env 파일 로드
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


def test_agent_execution():
    """Agent 실행 테스트"""
    print("\n" + "="*60)
    print("Agent 실행 성능 테스트")
    print("="*60)
    
    # API 키 확인
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("⚠️ OPENAI_API_KEY가 설정되지 않아 실제 실행 테스트를 스킵합니다.")
        print("   환경 변수를 설정하면 실제 성능 테스트를 수행할 수 있습니다.")
        return None
    
    print("✅ API 키 확인됨")
    
    # 테스트 케이스
    test_cases = [
        {
            'name': '간단한 질문 (LLM 모드)',
            'text': '당뇨병이 뭔가요?',
            'mode': 'llm'
        },
        {
            'name': '복잡한 질문 (AI Agent 모드)',
            'text': '65세 남성으로 당뇨병이 있습니다. 혈당 관리를 어떻게 해야 할까요?',
            'mode': 'ai_agent'
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n[테스트: {test_case['name']}]")
        print(f"질문: {test_case['text']}")
        print(f"모드: {test_case['mode']}")
        
        try:
            # 첫 실행 (캐시 워밍업)
            print("워밍업 실행 중...")
            start = time.time()
            answer1 = run_agent(test_case['text'], mode=test_case['mode'])
            time1 = time.time() - start
            
            # 두 번째 실행 (캐시 활용)
            print("캐시 활용 실행 중...")
            start = time.time()
            answer2 = run_agent(test_case['text'], mode=test_case['mode'])
            time2 = time.time() - start
            
            speedup = time1 / time2 if time2 > 0 else 0
            saved_time = (time1 - time2) * 1000
            
            print(f"첫 실행 시간: {time1:.2f}초")
            print(f"두 번째 실행 시간: {time2:.2f}초")
            print(f"속도 개선: {speedup:.2f}x")
            print(f"절약 시간: {saved_time:.2f}ms")
            print(f"답변 길이: {len(answer1)}자")
            
            results.append({
                'name': test_case['name'],
                'first_time': time1,
                'cached_time': time2,
                'speedup': speedup,
                'saved_time': saved_time,
                'answer_length': len(answer1)
            })
            
        except Exception as e:
            print(f"❌ 실행 실패: {e}")
            import traceback
            traceback.print_exc()
    
    return results


def benchmark_graph_build():
    """그래프 빌드 벤치마크"""
    print("\n" + "="*60)
    print("그래프 빌드 벤치마크")
    print("="*60)
    
    from agent.graph import build_agent_graph, get_agent_graph
    
    # 직접 빌드 시간 측정
    build_times = []
    for i in range(10):
        start = time.time()
        graph = build_agent_graph()
        build_times.append(time.time() - start)
    
    # 캐시에서 가져오기 시간 측정
    cache_times = []
    for i in range(100):
        start = time.time()
        graph = get_agent_graph()
        cache_times.append(time.time() - start)
    
    avg_build = sum(build_times) / len(build_times)
    avg_cache = sum(cache_times) / len(cache_times)
    
    print(f"직접 빌드 평균: {avg_build*1000:.2f}ms")
    print(f"캐시에서 가져오기 평균: {avg_cache*1000:.2f}ms")
    print(f"속도 개선: {avg_build/avg_cache:.2f}x")
    print(f"요청당 절약: {(avg_build - avg_cache)*1000:.2f}ms")


def benchmark_config_load():
    """설정 로드 벤치마크"""
    print("\n" + "="*60)
    print("설정 로드 벤치마크")
    print("="*60)
    
    from core.config import load_config, get_llm_config, get_retrieval_config, get_embedding_config
    
    # 첫 로드 시간
    start = time.time()
    config = load_config()
    llm_config = get_llm_config()
    retrieval_config = get_retrieval_config()
    embedding_config = get_embedding_config()
    first_load = time.time() - start
    
    # 캐시된 로드 시간
    cache_times = []
    for i in range(100):
        start = time.time()
        config = load_config()
        llm_config = get_llm_config()
        retrieval_config = get_retrieval_config()
        embedding_config = get_embedding_config()
        cache_times.append(time.time() - start)
    
    avg_cache = sum(cache_times) / len(cache_times)
    
    print(f"첫 로드 시간: {first_load*1000:.2f}ms")
    print(f"캐시 로드 평균: {avg_cache*1000:.2f}ms")
    print(f"속도 개선: {first_load/avg_cache:.2f}x")
    print(f"요청당 절약: {(first_load - avg_cache)*1000:.2f}ms")


def main():
    """메인 함수"""
    print("="*60)
    print("Agent 성능 테스트 및 벤치마크")
    print("="*60)
    
    # 벤치마크 실행
    benchmark_graph_build()
    benchmark_config_load()
    
    # 실제 Agent 실행 테스트
    results = test_agent_execution()
    
    # 결과 요약
    print("\n" + "="*60)
    print("성능 개선 요약")
    print("="*60)
    
    if results:
        total_saved = sum(r['saved_time'] for r in results)
        avg_speedup = sum(r['speedup'] for r in results) / len(results)
        
        print(f"평균 속도 개선: {avg_speedup:.2f}x")
        print(f"총 절약 시간: {total_saved:.2f}ms")
    
    print("\n✅ 모든 테스트 완료!")


if __name__ == "__main__":
    main()


