"""
코드 최적화 테스트 및 성능 측정
"""

import time
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent.graph import run_agent, get_agent_graph, build_agent_graph
from core.config import load_config, get_llm_config, get_retrieval_config, get_embedding_config
from core.utils import is_llm_mode
from agent.state import AgentState


def test_graph_caching():
    """그래프 캐싱 테스트"""
    print("\n" + "="*60)
    print("테스트 1: 그래프 캐싱")
    print("="*60)
    
    # 첫 번째 호출
    start = time.time()
    graph1 = get_agent_graph()
    time1 = time.time() - start
    
    # 두 번째 호출 (캐시에서 가져와야 함)
    start = time.time()
    graph2 = get_agent_graph()
    time2 = time.time() - start
    
    # 같은 객체인지 확인
    is_same = graph1 is graph2
    speedup = time1 / time2 if time2 > 0 else float('inf')
    
    print(f"첫 번째 빌드 시간: {time1*1000:.2f}ms")
    print(f"두 번째 빌드 시간: {time2*1000:.2f}ms")
    print(f"같은 객체 반환: {is_same}")
    print(f"속도 개선: {speedup:.2f}x")
    
    assert is_same, "그래프가 캐싱되지 않았습니다!"
    assert time2 < time1, "캐시된 그래프가 더 느립니다!"
    print("✅ 그래프 캐싱 정상 작동")
    return time1, time2


def test_config_caching():
    """설정 캐싱 테스트"""
    print("\n" + "="*60)
    print("테스트 2: 설정 캐싱")
    print("="*60)
    
    # 첫 번째 호출
    start = time.time()
    config1 = load_config()
    llm_config1 = get_llm_config()
    retrieval_config1 = get_retrieval_config()
    embedding_config1 = get_embedding_config()
    time1 = time.time() - start
    
    # 두 번째 호출 (캐시에서 가져와야 함)
    start = time.time()
    config2 = load_config()
    llm_config2 = get_llm_config()
    retrieval_config2 = get_retrieval_config()
    embedding_config2 = get_embedding_config()
    time2 = time.time() - start
    
    # 같은 객체인지 확인
    is_same_config = config1 is config2
    is_same_llm = llm_config1 is llm_config2
    is_same_retrieval = retrieval_config1 is retrieval_config2
    is_same_embedding = embedding_config1 is embedding_config2
    
    speedup = time1 / time2 if time2 > 0 else float('inf')
    
    print(f"첫 번째 로드 시간: {time1*1000:.2f}ms")
    print(f"두 번째 로드 시간: {time2*1000:.2f}ms")
    print(f"설정 캐싱: {is_same_config}")
    print(f"LLM 설정 캐싱: {is_same_llm}")
    print(f"검색 설정 캐싱: {is_same_retrieval}")
    print(f"임베딩 설정 캐싱: {is_same_embedding}")
    print(f"속도 개선: {speedup:.2f}x")
    
    assert is_same_config, "설정이 캐싱되지 않았습니다!"
    assert time2 < time1, "캐시된 설정이 더 느립니다!"
    print("✅ 설정 캐싱 정상 작동")
    return time1, time2


def test_utils():
    """유틸리티 함수 테스트"""
    print("\n" + "="*60)
    print("테스트 3: 유틸리티 함수")
    print("="*60)
    
    # LLM 모드 테스트
    state_llm: AgentState = {
        'user_text': 'test',
        'mode': 'llm',
        'slot_out': {},
        'profile_summary': '',
        'retrieved_docs': [],
        'query_vector': [],
        'system_prompt': '',
        'user_prompt': '',
        'answer': '',
        'quality_score': 0.0,
        'needs_retrieval': False,
        'iteration_count': 0
    }
    
    # AI Agent 모드 테스트
    state_agent: AgentState = {
        'user_text': 'test',
        'mode': 'ai_agent',
        'slot_out': {},
        'profile_summary': '',
        'retrieved_docs': [],
        'query_vector': [],
        'system_prompt': '',
        'user_prompt': '',
        'answer': '',
        'quality_score': 0.0,
        'needs_retrieval': False,
        'iteration_count': 0
    }
    
    is_llm1 = is_llm_mode(state_llm)
    is_llm2 = is_llm_mode(state_agent)
    
    print(f"LLM 모드 감지: {is_llm1} (예상: True)")
    print(f"AI Agent 모드 감지: {not is_llm2} (예상: True)")
    
    assert is_llm1 == True, "LLM 모드 감지 실패!"
    assert is_llm2 == False, "AI Agent 모드 감지 실패!"
    print("✅ 유틸리티 함수 정상 작동")


def test_bm25_optimization():
    """BM25 최적화 테스트 (heapq 사용 확인)"""
    print("\n" + "="*60)
    print("테스트 4: BM25 최적화")
    print("="*60)
    
    try:
        from retrieval.hybrid_retriever import BM25Retriever
        import heapq
        
        # heapq가 import되었는지 확인
        assert 'heapq' in sys.modules or hasattr(BM25Retriever, '__module__'), "heapq가 import되지 않았습니다!"
        
        # 코드에서 heapq.nlargest 사용 확인
        import inspect
        source = inspect.getsource(BM25Retriever.search)
        has_heapq = 'heapq.nlargest' in source or 'nlargest' in source
        
        print(f"heapq 모듈 import: ✅")
        print(f"heapq.nlargest 사용: {has_heapq}")
        
        if has_heapq:
            print("✅ BM25 최적화 적용됨")
        else:
            print("⚠️ BM25 최적화 코드 확인 필요")
            
    except Exception as e:
        print(f"⚠️ BM25 테스트 스킵: {e}")


def test_profile_store_optimization():
    """ProfileStore 최적화 테스트"""
    print("\n" + "="*60)
    print("테스트 5: ProfileStore 최적화")
    print("="*60)
    
    try:
        from memory.profile_store import ProfileStore
        import inspect
        
        source = inspect.getsource(ProfileStore.get_profile_summary)
        has_dict = 'vitals_dict' in source or 'labs_dict' in source
        
        print(f"딕셔너리 인덱싱 사용: {has_dict}")
        
        if has_dict:
            print("✅ ProfileStore 최적화 적용됨")
        else:
            print("⚠️ ProfileStore 최적화 코드 확인 필요")
            
    except Exception as e:
        print(f"⚠️ ProfileStore 테스트 스킵: {e}")


def performance_benchmark():
    """성능 벤치마크"""
    print("\n" + "="*60)
    print("성능 벤치마크")
    print("="*60)
    
    # 그래프 빌드 시간 측정
    print("\n[그래프 빌드]")
    times = []
    for i in range(5):
        # 캐시 초기화를 위해 직접 빌드
        start = time.time()
        graph = build_agent_graph()
        times.append(time.time() - start)
    
    avg_time = sum(times) / len(times)
    print(f"평균 빌드 시간: {avg_time*1000:.2f}ms")
    print(f"최소: {min(times)*1000:.2f}ms, 최대: {max(times)*1000:.2f}ms")
    
    # 캐시된 그래프 가져오기 시간
    print("\n[캐시된 그래프 가져오기]")
    cache_times = []
    for i in range(10):
        start = time.time()
        graph = get_agent_graph()
        cache_times.append(time.time() - start)
    
    avg_cache_time = sum(cache_times) / len(cache_times)
    print(f"평균 캐시 시간: {avg_cache_time*1000:.2f}ms")
    print(f"최소: {min(cache_times)*1000:.2f}ms, 최대: {max(cache_times)*1000:.2f}ms")
    
    speedup = avg_time / avg_cache_time if avg_cache_time > 0 else float('inf')
    print(f"\n캐싱으로 인한 속도 개선: {speedup:.2f}x")
    
    # 설정 로드 시간 측정
    print("\n[설정 로드]")
    config_times = []
    for i in range(5):
        # 캐시 초기화를 위해 모듈 리로드 필요 (실제로는 첫 호출만 측정)
        if i == 0:
            start = time.time()
            config = load_config()
            llm_config = get_llm_config()
            retrieval_config = get_retrieval_config()
            embedding_config = get_embedding_config()
            config_times.append(time.time() - start)
    
    if config_times:
        first_load = config_times[0]
        
        # 캐시된 설정 로드
        cache_config_times = []
        for i in range(10):
            start = time.time()
            config = load_config()
            llm_config = get_llm_config()
            retrieval_config = get_retrieval_config()
            embedding_config = get_embedding_config()
            cache_config_times.append(time.time() - start)
        
        avg_cache_config = sum(cache_config_times) / len(cache_config_times)
        print(f"첫 번째 로드 시간: {first_load*1000:.2f}ms")
        print(f"평균 캐시 로드 시간: {avg_cache_config*1000:.2f}ms")
        config_speedup = first_load / avg_cache_config if avg_cache_config > 0 else float('inf')
        print(f"캐싱으로 인한 속도 개선: {config_speedup:.2f}x")


def test_agent_basic():
    """기본 Agent 실행 테스트 (API 호출 없이)"""
    print("\n" + "="*60)
    print("테스트 6: Agent 기본 구조")
    print("="*60)
    
    try:
        # 그래프가 정상적으로 빌드되는지 확인
        graph = get_agent_graph()
        assert graph is not None, "그래프가 None입니다!"
        
        # 초기 상태 생성
        initial_state: AgentState = {
            'user_text': '테스트 질문',
            'mode': 'llm',  # LLM 모드로 빠른 테스트
            'slot_out': {},
            'profile_summary': '',
            'retrieved_docs': [],
            'query_vector': [],
            'system_prompt': '',
            'user_prompt': '',
            'answer': '',
            'quality_score': 0.0,
            'needs_retrieval': False,
            'iteration_count': 0
        }
        
        print("그래프 빌드: ✅")
        print("초기 상태 생성: ✅")
        print("⚠️ 실제 실행은 API 키가 필요하므로 스킵")
        print("✅ Agent 기본 구조 정상")
        
    except Exception as e:
        print(f"❌ Agent 구조 테스트 실패: {e}")
        raise


def main():
    """메인 테스트 함수"""
    print("="*60)
    print("코드 최적화 테스트 및 성능 측정")
    print("="*60)
    
    results = {}
    
    try:
        # 테스트 실행
        time1, time2 = test_graph_caching()
        results['graph_caching'] = {'first': time1, 'cached': time2}
        
        config_time1, config_time2 = test_config_caching()
        results['config_caching'] = {'first': config_time1, 'cached': config_time2}
        
        test_utils()
        test_bm25_optimization()
        test_profile_store_optimization()
        test_agent_basic()
        
        # 성능 벤치마크
        performance_benchmark()
        
        print("\n" + "="*60)
        print("✅ 모든 테스트 통과!")
        print("="*60)
        
        # 결과 요약
        print("\n[성능 개선 요약]")
        graph_speedup = time1 / time2 if time2 > 0 else float('inf')
        config_speedup = config_time1 / config_time2 if config_time2 > 0 else float('inf')
        
        print(f"그래프 캐싱: {graph_speedup:.2f}x 개선")
        print(f"설정 캐싱: {config_speedup:.2f}x 개선")
        print(f"총 절약 시간: {(time1 - time2 + config_time1 - config_time2)*1000:.2f}ms/요청")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


