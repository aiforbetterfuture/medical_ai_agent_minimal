# Context Engineering 기반 의학지식 AI Agent (최소 스캐폴드)

## 개요

이 프로젝트는 Context Engineering 기반 의학지식 AI Agent의 최소 구현 스캐폴드입니다.

### 핵심 기능

1. **Context Engineering 4단계**: 추출 → 저장 → 주입 → 검증
2. **하이브리드 검색**: BM25 + FAISS + RRF Fusion
3. **Self-Refine 메커니즘**: 품질 검증 및 재검색 루프
4. **MedCAT2 엔티티 추출**: UMLS 기반 의학 개념 추출

## 설치

### 1. 가상 환경 생성

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 또는
.venv\Scripts\activate  # Windows
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일을 생성하고 다음 변수를 설정하세요:

```env
# LLM API 키
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key  # 선택적

# MedCAT2 모델 경로
MEDCAT2_MODEL_PATH=path/to/medcat2/model.pack
```

## 사용법

### 기본 사용

```python
from agent.graph import run_agent

# AI Agent 모드
answer = run_agent(
    user_text="65세 남성으로 당뇨병이 있습니다.",
    mode='ai_agent'
)

print(answer)
```

### LangGraph 직접 사용

```python
from agent.graph import build_agent_graph

app = build_agent_graph()

initial_state = {
    'user_text': '당뇨병 관리 방법을 알려주세요.',
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

final_state = app.invoke(initial_state)
print(final_state['answer'])
```

## 프로젝트 구조

```
medical_ai_agent_minimal/
├── core/              # 핵심 모듈 (설정, LLM 클라이언트, 프롬프트)
├── extraction/        # 슬롯 추출 (MedCAT2, 정규표현식)
├── memory/           # 프로필 저장소
├── retrieval/        # 하이브리드 검색 (BM25, FAISS, RRF)
├── agent/            # LangGraph 워크플로우
│   └── nodes/        # 7개 노드
├── config/           # 설정 파일 (YAML)
├── data/             # 데이터셋 (corpus, index, labels)
└── requirements.txt  # 의존성 목록
```

## 워크플로우

```
User Input
    ↓
[1] extract_slots (슬롯 추출)
    ↓
[2] store_memory (메모리 저장)
    ↓
[3] assemble_context (컨텍스트 조립)
    ↓
[4] retrieve (하이브리드 검색)
    ↓
[5] generate_answer (LLM 답변 생성)
    ↓
[6] refine (Self-Refine 검증)
    ↓
[7] quality_check (품질 검사)
    ↓
    ├─ 품질 낮음 → [4] retrieve (재검색)
    └─ 품질 양호 → Final Answer
```

## 주요 모듈

### Core
- `config.py`: 설정 관리
- `llm_client.py`: LLM 클라이언트 (OpenAI, Gemini)
- `prompts.py`: 프롬프트 템플릿

### Extraction
- `slot_extractor.py`: 슬롯 추출기
- `medcat2_adapter.py`: MedCAT2 어댑터

### Memory
- `profile_store.py`: 프로필 저장소
- `schema.py`: 데이터 스키마

### Retrieval
- `hybrid_retriever.py`: 하이브리드 검색기
- `rrf_fusion.py`: RRF 융합
- `faiss_index.py`: FAISS 인덱스

### Agent
- `graph.py`: LangGraph 워크플로우
- `state.py`: AgentState 정의
- `nodes/`: 7개 노드 구현

## 라이선스

MIT License

## 참고

이 스캐폴드는 최소 구현 버전입니다. 추가 기능이 필요하면 원본 프로젝트를 참고하세요.

