"""
노드 4: 하이브리드 검색
"""

from agent.state import AgentState
from retrieval.hybrid_retriever import HybridRetriever
from core.llm_client import get_llm_client
from core.config import get_retrieval_config, get_embedding_config
from core.utils import is_llm_mode
from core.config import get_agent_config


def _select_route(slot_out: dict, feature_flags: dict) -> str:
    """
    간단한 라우팅 규칙:
    - 약물 언급 시 medication
    - 증상/질환 언급 시 symptom
    - 그 외 default
    """
    if not feature_flags.get('dynamic_rag_routing', True):
        return 'default'

    if slot_out.get('medications'):
        return 'medication'
    if slot_out.get('symptoms') or slot_out.get('conditions'):
        return 'symptom'
    return 'default'


def _rewrite_query(user_text: str, slot_out: dict, profile_summary: str, feature_flags: dict) -> str:
    """슬롯/프로필을 활용한 질의 재작성"""
    if not feature_flags.get('query_rewrite_enabled', True):
        return user_text

    parts = [user_text]
    demo = slot_out.get('demographics', {})
    additions = []
    if demo.get('age'):
        additions.append(f"age: {demo.get('age')}")
    if demo.get('gender'):
        additions.append(f"gender: {demo.get('gender')}")
    if slot_out.get('conditions'):
        additions.append("conditions: " + ", ".join(c.get('name', '') for c in slot_out.get('conditions', []) if c.get('name')))
    if slot_out.get('medications'):
        additions.append("medications: " + ", ".join(m.get('name', '') for m in slot_out.get('medications', []) if m.get('name')))

    if additions:
        parts.append(" | ".join(additions))
    if profile_summary:
        parts.append(f"profile: {profile_summary.replace(chr(10), ' ')}")

    return "\n".join(parts)


def retrieve_node(state: AgentState) -> AgentState:
    """
    검색 노드
    
    하이브리드 검색을 수행합니다.
    LLM 모드에서는 건너뜁니다.
    """
    print("[Node] retrieve")
    
    # LLM 모드: 검색 건너뛰기
    if is_llm_mode(state):
        return {
            **state,
            'retrieved_docs': []
        }

    feature_flags = state.get('feature_flags', {})
    
    # 재검색 시 iteration_count 증가 (이미 답변이 생성된 경우에만)
    if state.get('answer', ''):
        state['iteration_count'] = state.get('iteration_count', 0) + 1
    else:
        # 첫 검색인 경우 0으로 초기화
        state['iteration_count'] = 0
    
    # 설정 로드
    retrieval_config = get_retrieval_config()
    embedding_config = get_embedding_config()
    agent_config = state.get('agent_config') or get_agent_config()
    routing_table = (agent_config.get('routing') or {})
    
    # LLM 클라이언트 초기화 (임베딩용)
    if 'llm_client' not in state:
        llm_client = get_llm_client(provider=embedding_config.get('provider', 'openai'))
        state['llm_client'] = llm_client
    else:
        llm_client = state['llm_client']
    
    # 질의 재작성 (개인화 정보 포함)
    profile_summary = state.get('profile_summary', '')
    slot_out = state.get('slot_out', {})
    rewritten_query = _rewrite_query(state['user_text'], slot_out, profile_summary, feature_flags)
    state['query_for_retrieval'] = rewritten_query

    # 쿼리 벡터 생성
    try:
        query_vector = llm_client.embed(rewritten_query)
        state['query_vector'] = query_vector
    except Exception as e:
        print(f"[WARNING] 임베딩 생성 실패: {e}")
        query_vector = None
    
    # 라우팅 규칙 적용
    route = _select_route(slot_out, feature_flags)
    state['active_route'] = route

    retriever_key = f"hybrid_retriever::{route}"
    retriever_cache = state.get('retriever_cache', {})

    if retriever_key in retriever_cache:
        hybrid_retriever = retriever_cache[retriever_key]
    else:
        route_cfg = routing_table.get(route) or routing_table.get('default', {})
        retriever_config = {
            'bm25_corpus_path': route_cfg.get('bm25_corpus_path') or retrieval_config.get('bm25_corpus_path'),
            'faiss_index_path': route_cfg.get('faiss_index_path') or retrieval_config.get('faiss_index_path'),
            'faiss_meta_path': route_cfg.get('faiss_meta_path') or retrieval_config.get('faiss_meta_path'),
            'rrf_k': retrieval_config.get('multi', {}).get('rrf_k', 60)
        }
        hybrid_retriever = HybridRetriever(retriever_config)
        retriever_cache[retriever_key] = hybrid_retriever
        state['retriever_cache'] = retriever_cache
    
    # 검색 실행
    retrieved_docs = hybrid_retriever.search(
        query=rewritten_query,
        query_vector=query_vector,
        k=feature_flags.get('top_k', retrieval_config.get('multi', {}).get('retrievers', [{}])[0].get('k', 8))
    )
    
    return {
        **state,
        'retrieved_docs': retrieved_docs
    }

