# 7개 노드의 세부 기능과 역할 심층 분석

## 📌 개요
본 문서는 Medical AI Agent의 LangGraph 워크플로우를 구성하는 7개 노드의 세부 기능, 역할, 내부 메커니즘, 그리고 상호작용을 심층적으로 분석합니다.

---

## 제1장: 노드별 상세 분석

### Node 1: extract_slots (정보 추출의 시작점)

#### 1.1 핵심 기능
```python
def extract_slots_node(state: AgentState) -> AgentState:
    """
    사용자 입력에서 의학 정보를 추출하는 노드
    - MedCAT2 + 정규표현식 기반 추출
    - 6개 슬롯 구조화 (demographics, conditions, symptoms, vitals, labs, medications)
    - LLM 모드에서는 스킵 (성능 최적화)
    """
```

#### 1.2 내부 메커니즘

##### 계층적 추출 전략
```
Level 1: MedCAT2 의료 엔티티 추출
    ↓
Level 2: 정규표현식 기반 보완
    ↓
Level 3: 신뢰도 필터링 (confidence ≥ 0.7)
    ↓
Level 4: 슬롯 구조화
```

##### 슬롯 구조 상세
| 슬롯 유형 | 추출 방법 | 데이터 형식 | 예시 |
|----------|----------|-----------|------|
| demographics | Regex | Dict | {age: 65, gender: '남성'} |
| conditions | MedCAT2 + Keywords | List[Dict] | [{name: '당뇨병', cui: 'C0011849'}] |
| symptoms | MedCAT2 + Keywords | List[Dict] | [{name: '두통', negated: false}] |
| vitals | Regex patterns | List[Dict] | [{name: 'SBP', value: 140, unit: 'mmHg'}] |
| labs | Regex patterns | List[Dict] | [{name: 'A1c', value: 8.2, unit: '%'}] |
| medications | MedCAT2 + Keywords | List[Dict] | [{name: 'Metformin', dosage: '500mg'}] |

#### 1.3 최적화 전략

##### 캐싱 메커니즘
```python
# SlotExtractor 인스턴스를 state에 저장하여 재사용
if 'slot_extractor' not in state:
    extractor = SlotExtractor(use_medcat2=True)
    state['slot_extractor'] = extractor  # 캐싱
else:
    extractor = state['slot_extractor']  # 재사용
```

##### 지능형 스킵 로직
- LLM 모드: 즉시 리턴 (오버헤드 제거)
- 빈 입력: 빈 슬롯 반환
- 중복 입력: 캐시된 결과 반환

#### 1.4 혁신적 특징

1. **UMLS 통합**: MedCAT2를 통한 표준 의료 코드 체계 활용
2. **이중 검증**: AI 모델과 규칙 기반 접근의 하이브리드
3. **도메인 적응**: 한국어 의료 용어 특화 처리

---

### Node 2: store_memory (메모리 관리의 핵심)

#### 2.1 핵심 기능
```python
def store_memory_node(state: AgentState) -> AgentState:
    """
    추출된 슬롯을 장기 메모리에 저장
    - ProfileStore를 통한 구조화된 저장
    - 시계열 가중치 적용 (최신 정보 우선순위)
    - 프로필 요약 자동 생성
    """
```

#### 2.2 메모리 계층 구조

##### 3-Tier Memory Architecture
```
┌─────────────────────────────────┐
│    Working Memory (State)       │ ← 현재 대화 컨텍스트
├─────────────────────────────────┤
│    Short-term Memory (Slots)    │ ← 세션 내 정보
├─────────────────────────────────┤
│    Long-term Memory (Profile)   │ ← 영구 환자 프로필
└─────────────────────────────────┘
```

#### 2.3 시계열 가중치 알고리즘

```python
def apply_temporal_weights(self):
    """
    시간 경과에 따른 정보 가중치 조정

    Weight(t) = base_weight * exp(-λ * Δt)
    where:
        λ = decay rate (0.1 default)
        Δt = time difference in hours
    """
    current_time = time.time()

    for item in self.ltm.conditions:
        age_hours = (current_time - item.timestamp) / 3600
        item.weight = exp(-0.1 * age_hours)
```

#### 2.4 프로필 요약 생성 전략

##### 구조화된 요약 템플릿
```markdown
### 환자 정보
- 인구통계: {age}세 {gender}
- 진단: {top_conditions}
- 최근 증상: {recent_symptoms}
- 현재 수치: {latest_vitals_labs}
- 복용 약물: {active_medications}
```

##### 우선순위 알고리즘
1. **Recency**: 최근 24시간 내 정보 우선
2. **Frequency**: 반복 언급된 정보 강조
3. **Severity**: 중요도 높은 진단 우선 표시

#### 2.5 혁신적 특징

1. **적응형 메모리**: 대화 패턴에 따른 동적 조정
2. **압축 알고리즘**: 중복 제거 및 정보 압축
3. **프라이버시 보호**: 민감 정보 마스킹 옵션

---

### Node 3: assemble_context (컨텍스트 엔지니어링의 정수)

#### 3.1 핵심 기능
```python
def assemble_context_node(state: AgentState) -> AgentState:
    """
    동적 프롬프트 조립 엔진
    - 모드별 차별화된 프롬프트 생성
    - 프로필 + 검색 결과 + 대화 이력 통합
    - 컨텍스트 최적화 (토큰 효율성)
    """
```

#### 3.2 컨텍스트 조립 파이프라인

##### 4-Stage Assembly Process
```
Stage 1: Base Template Selection
    ↓
Stage 2: Profile Injection
    ↓
Stage 3: Evidence Integration
    ↓
Stage 4: History Concatenation
```

#### 3.3 프롬프트 엔지니어링 전략

##### 모드별 프롬프트 구조

| 모드 | 시스템 프롬프트 | 사용자 프롬프트 | 컨텍스트 크기 |
|-----|---------------|--------------|-------------|
| LLM | 기본 역할 정의 | 질문만 | ~500 tokens |
| AI Agent | 역할 + 개인화 + 근거 | 질문 + 이력 | ~3000 tokens |

##### 토큰 최적화 기법
```python
def optimize_context(text: str, max_tokens: int = 3000) -> str:
    """
    컨텍스트 토큰 최적화

    전략:
    1. 중요도 점수 계산
    2. 토큰 수 추정 (tiktoken)
    3. 저우선순위 정보 트리밍
    4. 요약을 통한 압축
    """
```

#### 3.4 대화 이력 관리 (신규 기능)

##### Conversation History Integration
```python
# 멀티턴 대화 지원을 위한 이력 포함
if conversation_history:
    context = f"""
    ## 이전 대화
    {conversation_history}

    ## 현재 질문
    {user_text}
    """
```

##### 이력 압축 알고리즘
- 최근 5턴만 유지
- 핵심 정보 추출 후 요약
- 토큰 한계 내 최적화

#### 3.5 혁신적 특징

1. **동적 템플릿**: 상황별 자동 템플릿 선택
2. **컨텍스트 윈도우 관리**: 효율적 토큰 활용
3. **크로스 레퍼런스**: 프로필-문서 간 연결

---

### Node 4: retrieve (하이브리드 검색의 실행)

#### 4.1 핵심 기능
```python
def retrieve_node(state: AgentState) -> AgentState:
    """
    듀얼 검색 엔진
    - BM25 키워드 검색 + FAISS 벡터 검색
    - RRF 융합 (k=60)
    - 적응형 재검색 메커니즘
    """
```

#### 4.2 하이브리드 검색 아키텍처

##### Dual-Path Retrieval System
```
         Query
           ↓
    ┌──────┴──────┐
    ↓             ↓
  BM25         FAISS
(Lexical)    (Semantic)
    ↓             ↓
    └──────┬──────┘
           ↓
      RRF Fusion
           ↓
     Top-k Results
```

#### 4.3 검색 최적화 전략

##### 쿼리 확장 기법
```python
def expand_query(original_query: str, profile: Profile) -> str:
    """
    프로필 기반 쿼리 확장

    예시:
    원본: "혈당 관리"
    확장: "혈당 관리 당뇨병 65세 남성 A1c 8.2"
    """
    expanded = original_query
    if profile.conditions:
        expanded += f" {' '.join([c.name for c in profile.conditions[:3]])}"
    if profile.demographics:
        expanded += f" {profile.demographics.get('age')}세"
    return expanded
```

##### 재검색 로직
```python
# iteration_count 기반 전략 변경
if state['iteration_count'] == 0:
    k = 8  # 첫 검색: 표준
elif state['iteration_count'] == 1:
    k = 12  # 재검색: 확대
else:
    k = 16  # 최종: 최대 확대
```

#### 4.4 벡터 임베딩 전략

##### 임베딩 모델 선택
| 모델 | 차원 | 속도 | 정확도 | 비용 |
|------|-----|------|--------|------|
| text-embedding-3-small | 1536 | 빠름 | 좋음 | 낮음 |
| text-embedding-3-large | 3072 | 보통 | 우수 | 보통 |
| text-embedding-ada-002 | 1536 | 빠름 | 보통 | 낮음 |

##### 캐싱 전략
```python
# 임베딩 캐시로 API 호출 최소화
embedding_cache = {}
if query in embedding_cache:
    return embedding_cache[query]
else:
    vector = llm_client.embed(query)
    embedding_cache[query] = vector
    return vector
```

#### 4.5 혁신적 특징

1. **적응형 검색**: 품질에 따른 동적 파라미터 조정
2. **Cross-lingual**: 한영 혼용 검색 지원
3. **Contextual Reranking**: 프로필 기반 재순위화

---

### Node 5: generate_answer (LLM 활용의 중심)

#### 5.1 핵심 기능
```python
def generate_answer_node(state: AgentState) -> AgentState:
    """
    지능형 답변 생성 엔진
    - Multi-provider 지원 (OpenAI, Gemini)
    - 스트리밍 응답 옵션
    - 에러 복구 메커니즘
    """
```

#### 5.2 생성 전략

##### Temperature 조정 로직
```python
def adjust_temperature(context_type: str) -> float:
    """
    컨텍스트 유형별 temperature 동적 조정

    의료 정보: 0.3 (정확성 우선)
    일반 상담: 0.7 (자연스러움)
    창의적 답변: 0.9 (다양성)
    """
    temperature_map = {
        'medical_facts': 0.3,
        'consultation': 0.7,
        'creative': 0.9
    }
    return temperature_map.get(context_type, 0.7)
```

##### 응답 구조화
```python
def structure_response(raw_answer: str) -> str:
    """
    답변 구조화 및 포맷팅

    1. 핵심 정보 추출
    2. 단락 구분
    3. 불렛 포인트 추가
    4. 의학 용어 설명 추가
    """
```

#### 5.3 Multi-Provider 전략

##### Provider 선택 알고리즘
```python
def select_provider(query_complexity: float, latency_requirement: float):
    """
    쿼리 복잡도와 지연시간 요구사항에 따른 프로바이더 선택

    High complexity + Low latency tolerance → GPT-4
    Low complexity + High latency tolerance → Gemini Flash
    Medium complexity + Medium latency → GPT-4o-mini
    """
```

##### Fallback Chain
```
Primary: GPT-4o
    ↓ (실패 시)
Secondary: Gemini Pro
    ↓ (실패 시)
Tertiary: GPT-3.5-turbo
    ↓ (실패 시)
Static: 사전 정의 응답
```

#### 5.4 스트리밍 및 청킹

##### 스트리밍 응답 구현
```python
async def stream_generate(prompt: str):
    """
    실시간 스트리밍 응답

    장점:
    - 첫 토큰까지 시간 단축 (TTFT)
    - 사용자 체감 속도 향상
    - 중간 취소 가능
    """
    async for chunk in llm_client.stream(prompt):
        yield chunk
```

#### 5.5 혁신적 특징

1. **Adaptive Generation**: 컨텍스트 기반 파라미터 조정
2. **Multi-modal Ready**: 이미지/차트 생성 준비
3. **Citation Generation**: 근거 자동 인용

---

### Node 6: refine (품질 보증의 관문)

#### 6.1 핵심 기능
```python
def refine_node(state: AgentState) -> AgentState:
    """
    Self-Refine 품질 검증 엔진
    - 다차원 품질 평가
    - 점수 기반 의사결정
    - 개선 방향 제시
    """
```

#### 6.2 품질 평가 매트릭스

##### 3-Dimensional Quality Assessment
```python
quality_dimensions = {
    'completeness': {
        'weight': 0.3,
        'metrics': ['length', 'coverage', 'depth'],
        'threshold': 500  # characters
    },
    'evidence_based': {
        'weight': 0.4,
        'metrics': ['doc_count', 'citation_quality', 'relevance'],
        'threshold': 3  # documents
    },
    'personalization': {
        'weight': 0.3,
        'metrics': ['profile_usage', 'specificity', 'context_alignment'],
        'threshold': 0.5  # score
    }
}
```

#### 6.3 고급 품질 메트릭

##### 의료 특화 품질 지표
```python
def medical_quality_metrics(answer: str) -> Dict[str, float]:
    """
    의료 답변 특화 품질 평가

    Returns:
        accuracy_score: 의학적 정확성
        safety_score: 안전성 (해로운 조언 체크)
        clarity_score: 이해 용이성
        actionability_score: 실행 가능성
    """
    metrics = {}

    # 의학적 정확성 체크
    metrics['accuracy'] = check_medical_accuracy(answer)

    # 위험한 조언 감지
    metrics['safety'] = detect_harmful_advice(answer)

    # 전문 용어 대 일반 용어 비율
    metrics['clarity'] = calculate_readability(answer)

    # 구체적 행동 지침 포함 여부
    metrics['actionability'] = has_actionable_advice(answer)

    return metrics
```

##### 동적 임계값 조정
```python
def dynamic_threshold(iteration: int) -> float:
    """
    반복 횟수에 따른 품질 임계값 동적 조정

    iteration 0: 0.7 (높은 기준)
    iteration 1: 0.5 (중간 기준)
    iteration 2: 0.3 (최소 기준)
    """
    base_threshold = 0.7
    decay_rate = 0.2
    return max(0.3, base_threshold - (iteration * decay_rate))
```

#### 6.4 개선 제안 생성

##### Improvement Suggestions
```python
def generate_improvement_suggestions(quality_scores: Dict) -> List[str]:
    """
    품질 점수 기반 개선 제안 생성

    낮은 완성도 → "더 자세한 설명 필요"
    낮은 근거 → "추가 문서 검색 필요"
    낮은 개인화 → "환자 정보 더 활용 필요"
    """
    suggestions = []

    if quality_scores['completeness'] < 0.5:
        suggestions.append("expand_answer")

    if quality_scores['evidence_based'] < 0.5:
        suggestions.append("search_more_docs")

    if quality_scores['personalization'] < 0.5:
        suggestions.append("use_profile_more")

    return suggestions
```

#### 6.5 혁신적 특징

1. **Multi-criteria Optimization**: 다목적 최적화
2. **Adaptive Thresholding**: 상황별 기준 조정
3. **Explainable Scoring**: 점수 산출 과정 설명

---

### Node 7: quality_check (조건부 분기 로직)

#### 7.1 핵심 기능
```python
def quality_check_node(state: AgentState) -> str:
    """
    워크플로우 라우팅 결정 엔진
    - 품질 기반 분기
    - 무한 루프 방지
    - 모드별 라우팅 전략
    """
```

#### 7.2 의사결정 트리

##### Decision Tree Structure
```
                quality_check
                     │
        ┌────────────┼────────────┐
        │                         │
    LLM Mode?                 AI Agent Mode?
        │                         │
       END                   quality_score
                                  │
                    ┌─────────────┼─────────────┐
                    │                           │
                score < 0.5                score ≥ 0.5
                    │                           │
              iteration < 2?                   END
                    │
            ┌───────┴───────┐
            │               │
           YES              NO
            │               │
        retrieve           END
```

#### 7.3 라우팅 전략

##### 모드별 라우팅 로직
| 모드 | 조건 | 액션 | 이유 |
|-----|------|------|------|
| LLM | 항상 | END | 빠른 응답 우선 |
| AI Agent | score < 0.5 & iter < 2 | retrieve | 품질 개선 시도 |
| AI Agent | score ≥ 0.5 | END | 품질 만족 |
| AI Agent | iter ≥ 2 | END | 무한 루프 방지 |

##### 복합 조건 처리
```python
def complex_routing_logic(state: AgentState) -> str:
    """
    복잡한 라우팅 로직 구현

    고려 사항:
    1. 품질 점수
    2. 반복 횟수
    3. 시간 제약
    4. 사용자 선호도
    5. 리소스 가용성
    """
    # 우선순위 1: 시간 제약
    if time_elapsed > MAX_TIME:
        return END

    # 우선순위 2: 품질 기준
    if state['quality_score'] >= dynamic_threshold(state['iteration_count']):
        return END

    # 우선순위 3: 반복 제한
    if state['iteration_count'] >= MAX_ITERATIONS:
        return END

    # 우선순위 4: 개선 가능성
    if has_improvement_potential(state):
        return "retrieve"

    return END
```

#### 7.4 루프 최적화

##### 루프 효율성 향상
```python
def optimize_loop_performance(state: AgentState):
    """
    재검색 루프 최적화 전략

    1. 캐시 활용: 이전 검색 결과 재사용
    2. 증분 검색: 추가 문서만 검색
    3. 파라미터 조정: k값, temperature 변경
    """
    if state['iteration_count'] == 1:
        # 첫 재검색: 파라미터 미세 조정
        state['search_params']['k'] += 4
        state['llm_params']['temperature'] -= 0.1

    elif state['iteration_count'] == 2:
        # 두 번째 재검색: 전략 변경
        state['search_strategy'] = 'semantic_only'
        state['llm_params']['model'] = 'gpt-4'  # 더 강력한 모델
```

#### 7.5 혁신적 특징

1. **Smart Routing**: AI 기반 라우팅 결정
2. **Loop Learning**: 루프 패턴 학습 및 최적화
3. **Predictive Termination**: 개선 가능성 예측

---

## 제2장: 노드 간 상호작용 분석

### 2.1 데이터 흐름 매핑

#### 정보 전파 경로
```
User Input → [Node 1] → Slots
    ↓
Slots → [Node 2] → Profile Summary
    ↓
Profile → [Node 3] → Context Assembly
    ↓
Context → [Node 4] → Retrieved Docs
    ↓
Docs + Context → [Node 5] → Answer
    ↓
Answer → [Node 6] → Quality Score
    ↓
Score → [Node 7] → Routing Decision
    ↓
[Loop back to Node 4] OR [END]
```

### 2.2 상태 전파 메커니즘

#### Critical State Variables
```python
state_dependencies = {
    'extract_slots': ['user_text'],
    'store_memory': ['slot_out'],
    'assemble_context': ['profile_summary', 'conversation_history'],
    'retrieve': ['user_text', 'iteration_count'],
    'generate_answer': ['system_prompt', 'user_prompt'],
    'refine': ['answer', 'retrieved_docs', 'profile_summary'],
    'quality_check': ['quality_score', 'needs_retrieval', 'iteration_count']
}
```

### 2.3 병목 지점 분석

#### Performance Bottlenecks
| 노드 | 평균 시간 | 병목 원인 | 최적화 방안 |
|-----|----------|---------|-----------|
| extract_slots | 50ms | MedCAT2 로딩 | 모델 캐싱 |
| retrieve | 100ms | 벡터 검색 | 인덱스 최적화 |
| generate_answer | 1500ms | API 호출 | 스트리밍 |

---

## 제3장: 혁신적 개선 방향

### 3.1 노드 레벨 혁신

#### Node 1 개선: Multi-modal Extraction
```python
class MultiModalExtractor:
    """
    텍스트 + 이미지 + 음성에서 정보 추출

    - OCR for medical reports
    - Speech-to-text for voice input
    - Image analysis for X-rays, MRI
    """
```

#### Node 2 개선: Graph-based Memory
```python
class GraphMemory:
    """
    Neo4j 기반 그래프 메모리

    - 관계형 정보 저장
    - 복잡한 의료 관계 모델링
    - 추론 기반 정보 발견
    """
```

#### Node 3 개선: Dynamic Template Generation
```python
class DynamicTemplateEngine:
    """
    LLM 기반 동적 템플릿 생성

    - Few-shot learning으로 템플릿 학습
    - 상황별 최적 템플릿 자동 생성
    - A/B 테스트로 템플릿 최적화
    """
```

#### Node 4 개선: Neural Retrieval
```python
class NeuralRetriever:
    """
    학습 가능한 검색 시스템

    - Dense Passage Retrieval (DPR)
    - Cross-encoder reranking
    - Query-Document interaction modeling
    """
```

#### Node 5 개선: Mixture of Experts
```python
class MoEGenerator:
    """
    전문가 혼합 모델

    - 의료 분야별 특화 모델
    - 동적 전문가 선택
    - 앙상블 답변 생성
    """
```

#### Node 6 개선: Reinforcement Learning
```python
class RLRefiner:
    """
    강화학습 기반 품질 개선

    - 보상 함수 학습
    - 정책 그래디언트 최적화
    - 인간 피드백 통합 (RLHF)
    """
```

#### Node 7 개선: Predictive Routing
```python
class PredictiveRouter:
    """
    예측 기반 라우팅

    - 개선 가능성 사전 예측
    - 최적 경로 학습
    - 조기 종료 결정
    """
```

### 3.2 시스템 레벨 혁신

#### Parallel Processing
```python
async def parallel_workflow():
    """
    병렬 처리 워크플로우

    - extract_slots와 retrieve 동시 실행
    - 비동기 LLM 호출
    - 파이프라인 병렬화
    """
    tasks = [
        asyncio.create_task(extract_slots()),
        asyncio.create_task(initial_retrieve())
    ]
    results = await asyncio.gather(*tasks)
```

#### Caching Strategy
```python
class IntelligentCache:
    """
    지능형 캐싱 시스템

    - Query similarity 기반 캐싱
    - TTL 동적 조정
    - 캐시 히트율 최적화
    """
```

---

## 제4장: 멀티턴 대화 지원 강화

### 4.1 Context Carryover

#### 상태 지속성 메커니즘
```python
class ConversationState:
    """
    대화 상태 관리

    - 전체 대화 히스토리
    - 핵심 정보 추출
    - 컨텍스트 압축
    """
    def __init__(self):
        self.history = []
        self.extracted_slots = {}
        self.profile_evolution = []

    def update(self, turn_data):
        self.history.append(turn_data)
        self.merge_slots(turn_data['slots'])
        self.track_profile_changes()
```

### 4.2 Reference Resolution

#### 대명사 및 참조 해결
```python
def resolve_references(current_query: str, history: List[str]) -> str:
    """
    참조 해결

    "그것" → "당뇨병"
    "위 증상" → "두통과 어지러움"
    "이전에 말한" → 구체적 내용 복원
    """
```

### 4.3 Context Window Management

#### 효율적 윈도우 관리
```python
def manage_context_window(history: List, max_tokens: int = 4000):
    """
    컨텍스트 윈도우 최적화

    전략:
    1. 중요도 점수 계산
    2. 토큰 수 추정
    3. 선택적 포함/제외
    4. 요약을 통한 압축
    """
```

---

## 제5장: 실전 적용 시나리오

### 5.1 응급실 트리아지

#### 워크플로우 적용
```
환자 도착 → 증상 입력 → [Node 1-7] → 우선순위 결정
    ↓
긴급도 평가 → 의료진 배정 → 실시간 업데이트
```

### 5.2 원격 진료 상담

#### 워크플로우 적용
```
화상 상담 시작 → 멀티턴 대화 → [Node 1-7 반복] → 처방 제안
    ↓
의사 검토 → 최종 처방 → 팔로업 일정
```

### 5.3 임상 의사결정 지원

#### 워크플로우 적용
```
검사 결과 입력 → 과거 기록 통합 → [Node 1-7] → 진단 제안
    ↓
치료 옵션 제시 → 위험도 평가 → 의사 최종 결정
```

---

## 결론

### 핵심 통찰

7개 노드로 구성된 LangGraph 워크플로우는:

1. **모듈성**: 각 노드가 독립적 기능 수행
2. **확장성**: 새로운 노드 추가 용이
3. **유연성**: 다양한 의료 시나리오 대응
4. **최적화**: 캐싱과 병렬 처리 가능

### 혁신 방향

1. **지능화**: ML/DL 기법 통합
2. **병렬화**: 비동기 처리 확대
3. **개인화**: 사용자별 맞춤 워크플로우
4. **자동화**: AutoML 기반 파라미터 최적화

### 다음 단계

1. 각 노드의 단위 테스트 강화
2. 엔드-투-엔드 성능 벤치마킹
3. 실제 의료 환경 파일럿 테스트
4. 사용자 피드백 기반 반복 개선

---

*작성일: 2024년 12월 4일*
*버전: 1.0*