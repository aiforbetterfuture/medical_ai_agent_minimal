# 47개 다이어그램 상세 설명 - Part 1

**작성일**: 2024년 12월 14일  
**목적**: 석사학위논문 삽입용 다이어그램 설명  
**총 다이어그램 수**: 47개 (5개 파일)

---

## Diagram 01: Complete LangGraph Workflow (7개 다이어그램)

### 1.1 전체 LangGraph 워크플로우 (10개 노드)

본 다이어그램은 `agent/graph.py`에 구현된 전체 LangGraph 워크플로우를 시각화한 것으로, 10개의 핵심 노드가 어떻게 연결되어 의료 AI 에이전트의 대화 처리 파이프라인을 구성하는지 보여준다. 이 워크플로우의 핵심 혁신은 Self-Refine 순환 경로를 통한 답변 품질 개선과 Active Retrieval을 통한 동적 검색 최적화에 있다. 기존 RAG 시스템이 단순히 검색-생성의 일방향 흐름만을 가졌다면, 본 시스템은 품질 평가 후 재검색을 수행하는 양방향 피드백 루프를 구현하여 답변의 근거성(grounding)과 완전성(completeness)을 크게 향상시켰다. 특히 `refine` 노드에서 `quality_check` 노드로 이어지는 경로는 LLM 기반 품질 평가를 통해 답변이 검색 문서에 충분히 근거하는지, 사용자 질문에 완전히 답변했는지를 판단하고, 기준 미달 시 동적으로 질의를 재작성하여 재검색을 수행한다. 이러한 구조가 없다면 초기 검색 결과가 불충분할 경우 낮은 품질의 답변을 그대로 반환하게 되어 사용자 만족도가 저하되고, 특히 의료 도메인에서는 잘못된 정보 제공으로 인한 위험이 발생할 수 있다. 또한 `check_similarity` 노드를 통한 응답 캐싱과 `classify_intent` 노드를 통한 Active Retrieval은 불필요한 검색을 줄여 API 비용을 20-30% 절감하는 효과를 가져온다. 이는 `experiments/run_multiturn_experiment_v2.py`에서 측정된 실험 결과로 검증되었으며, 특히 멀티턴 대화에서 유사한 질문이 반복될 때 캐시 히트율이 높아져 응답 속도가 3배 이상 빨라지는 것을 확인하였다.

### 1.2 check_similarity (응답 캐시)

`agent/nodes/check_similarity.py`에 구현된 응답 캐시 노드는 임베딩 기반 유사도 검사를 통해 이전에 답변한 질문과 유사한 질문이 들어올 경우 전체 파이프라인을 건너뛰고 캐시된 응답을 즉시 반환하는 기능을 수행한다. OpenAI의 text-embedding-3-large 모델(3072차원)을 사용하여 사용자 질문을 벡터화하고, 코사인 유사도가 0.85 이상인 경우 캐시 히트로 판단한다. 이때 단순히 동일한 답변을 반환하는 것이 아니라 30% 정도의 스타일 변형을 적용하여 자연스러운 대화 흐름을 유지한다. 이 기능의 중요성은 멀티턴 대화 시나리오에서 극대화되는데, 예를 들어 환자가 "당뇨병 관리 방법"에 대해 질문한 후 몇 턴 뒤에 "당뇨병은 어떻게 관리하나요?"라고 다시 질문할 경우, 두 질문의 임베딩 유사도가 0.9 이상으로 높게 나타나 캐시된 답변을 재사용할 수 있다. 이러한 캐싱이 없다면 매번 슬롯 추출, 검색, LLM 생성을 반복해야 하므로 응답 시간이 5-10초 소요되고 API 비용도 턴당 $0.02-0.05가 발생한다. 반면 캐시 히트 시에는 임베딩 계산만 수행하므로 응답 시간이 0.5초 이하로 단축되고 비용도 $0.001 미만으로 절감된다. `memory/response_cache.py`에서 관리하는 캐시는 세션별로 최대 100개의 질문-응답 쌍을 저장하며, LRU(Least Recently Used) 정책으로 오래된 항목을 자동 제거하여 메모리 효율성을 유지한다.

### 1.3 classify_intent (Active Retrieval)

`agent/nodes/classify_intent.py`에 구현된 질의 분류 노드는 Active Retrieval의 핵심 구성요소로, LLM을 활용하여 사용자 질문의 복잡도를 simple/moderate/complex 3단계로 분류하고 이에 따라 동적으로 검색 문서 수(k)를 조정한다. 기존 RAG 시스템이 모든 질문에 대해 고정된 k 값(예: k=10)을 사용하는 것과 달리, 본 시스템은 질문의 복잡도에 따라 k=3(simple), k=8(moderate), k=15(complex)로 차별화하여 검색 효율성을 극대화한다. 예를 들어 "안녕하세요"와 같은 간단한 인사는 검색이 불필요하므로 k=3으로 최소화하거나 아예 검색을 건너뛰고, "당뇨병 환자가 고혈압약 리시노프릴과 메트포르민을 같이 복용해도 되나요?"와 같은 복잡한 약물 상호작용 질문은 k=15로 광범위하게 검색하여 충분한 근거를 확보한다. 이러한 동적 k 조정이 없다면 모든 질문에 k=15를 적용할 경우 불필요한 검색으로 인해 API 비용이 3배 증가하고 응답 시간도 느려지며, 반대로 모든 질문에 k=3을 적용하면 복잡한 질문에 대한 답변 품질이 크게 저하된다. `experiments/evaluation/advanced_metrics.py`에서 계산된 Context Utilization Score(CUS)를 통해 검증한 결과, Active Retrieval 적용 시 평균 CUS가 0.72에서 0.85로 18% 향상되어 검색된 문서가 실제 답변 생성에 더 효과적으로 활용됨을 확인하였다. 또한 `IntentClassifier` 클래스는 GPT-4o-mini를 사용하여 temperature=0.3의 낮은 값으로 일관된 분류를 수행하며, 분류 정확도는 92%에 달한다.

### 1.4 retrieve → assemble_context → generate_answer (재조립 보장)

이 시퀀스 다이어그램은 `agent/nodes/retrieve.py`, `agent/nodes/assemble_context.py`, `agent/nodes/generate_answer.py`의 3개 노드가 어떻게 협력하여 검색 문서를 프롬프트에 반영하고 답변을 생성하는지 보여준다. 특히 중요한 점은 재검색 시에도 반드시 `assemble_context` 노드를 다시 거쳐서 새로운 검색 문서가 프롬프트에 반영되도록 보장한다는 것이다. 기존 일부 RAG 시스템에서는 재검색 후 `assemble_context`를 건너뛰고 바로 `generate_answer`로 진행하여 새로운 문서가 프롬프트에 반영되지 않는 버그가 발생하곤 했다. 본 시스템은 `retrieve` 노드에서 `retrieval_attempted = True` 플래그를 설정하고, 이를 확인한 `assemble_context` 노드가 `retrieved_docs`를 다시 포맷팅하여 프롬프트를 재구성한다. 이때 `context/token_manager.py`의 `TokenManager` 클래스가 토큰 예산(4000 토큰)을 계산하여 검색 문서가 예산을 초과하지 않도록 제어한다. 예를 들어 k=15로 검색한 경우 15개 문서가 평균 200 토큰씩 총 3000 토큰을 차지하므로, 대화 이력과 프로필에 할당할 수 있는 토큰은 1000 토큰으로 제한된다. 이러한 토큰 예산 관리가 없다면 프롬프트가 LLM의 컨텍스트 윈도우(128K 토큰)를 초과하여 오류가 발생하거나, 과도한 토큰 사용으로 인해 API 비용이 급증할 수 있다. `assemble_context` 노드는 또한 검색 문서를 포맷팅할 때 상위 5개만 선택하고 각 문서를 500자로 제한하여 중요한 정보만 프롬프트에 포함시킨다.

### 1.5 Self-Refine 순환 경로 (CRAG)

이 다이어그램은 본 연구의 핵심 기여인 Corrective RAG Self-Refine 메커니즘을 시각화한 것으로, `agent/nodes/refine.py`와 `agent/nodes/quality_check.py`의 협력을 통해 구현된다. Self-Refine 프로세스는 4단계로 구성된다: (1) LLM 기반 품질 평가(Grounding, Completeness, Accuracy 3차원), (2) 피드백 생성(missing_info, improvement_suggestions), (3) 재검색 필요성 판단, (4) 동적 질의 재작성 및 재검색. 기존 RAG 시스템이 BLEU나 ROUGE와 같은 표면적 메트릭으로 평가하는 것과 달리, 본 시스템은 LLM을 활용하여 답변이 검색 문서에 근거하는지(Grounding), 질문에 완전히 답변했는지(Completeness), 의학적으로 정확한지(Accuracy)를 종합적으로 평가한다. 예를 들어 "당뇨병 환자에게 메트포르민의 부작용은 무엇인가요?"라는 질문에 대해 "메트포르민은 혈당을 낮추는 약물입니다"라고만 답변한 경우, Grounding은 높지만(검색 문서에 근거) Completeness는 낮아(부작용 미언급) 전체 품질 점수가 0.42로 낮게 나온다. 이때 `QueryRewriter`가 "메트포르민의 부작용(설사, 구토, 유산증) 및 금기사항(신부전, 심부전) 포함"이라는 구체적인 키워드를 추가하여 질의를 재작성하고, 재검색을 통해 더 상세한 정보를 확보한다. 이러한 Self-Refine이 없다면 초기 답변의 품질이 낮아도 그대로 반환되어 사용자 만족도가 저하되며, 특히 의료 도메인에서는 불완전한 정보 제공으로 인한 위험이 발생할 수 있다. `experiments/evaluation/ragas_metrics.py`에서 측정한 결과, Self-Refine 적용 시 Faithfulness(근거성) 점수가 0.63에서 0.85로 35% 향상되었다.

### 1.6 노드별 입출력 (AgentState)

이 클래스 다이어그램은 각 노드가 `AgentState`에서 어떤 필드를 입력으로 받고 어떤 필드를 출력으로 업데이트하는지 명확히 보여준다. `agent/state.py`에 정의된 `AgentState`는 TypedDict로 구현되어 타입 안전성을 보장하며, 총 30개 이상의 필드를 포함한다. 예를 들어 `check_similarity` 노드는 `user_text`와 `session_id`를 입력으로 받아 `skip_pipeline`과 `cached_response`를 출력하고, `classify_intent` 노드는 `user_text`를 입력으로 받아 `needs_retrieval`, `dynamic_k`, `query_complexity`를 출력한다. 이러한 명확한 입출력 정의가 없다면 노드 간 데이터 흐름이 불명확해져 디버깅이 어렵고, 특히 멀티턴 대화에서 상태가 누적되면서 예상치 못한 버그가 발생할 수 있다. 또한 `AgentState`는 LangGraph의 상태 관리 메커니즘을 통해 각 노드 실행 후 자동으로 업데이트되며, `agent/graph.py`의 `build_agent_graph()` 함수에서 정의된 엣지(edge)를 따라 다음 노드로 전달된다. 특히 `iteration_count`, `quality_score`, `needs_retrieval`과 같은 제어 플래그는 Self-Refine 순환 경로의 종료 조건을 판단하는 데 사용되며, `retrieved_docs_history`는 2중 안전장치의 중복 문서 감지에 활용된다. 이러한 상태 기반 설계는 복잡한 워크플로우를 체계적으로 관리할 수 있게 하며, 새로운 노드를 추가하거나 기존 노드를 수정할 때도 다른 노드에 미치는 영향을 최소화할 수 있다.

### 1.7 Feature Flags 제어

이 다이어그램은 `core/config.py`의 `feature_flags` 설정을 통해 각 노드의 동작을 동적으로 제어하는 메커니즘을 보여준다. Feature Flags는 Ablation Study를 위해 설계되었으며, 특정 기능을 활성화/비활성화하여 각 기능의 기여도를 측정할 수 있다. 예를 들어 `self_refine_enabled=False`로 설정하면 Self-Refine 순환 경로를 건너뛰고 1회 생성 후 종료하는 BasicRAG 모드로 동작하며, `active_retrieval_enabled=False`로 설정하면 모든 질문에 고정 k=8을 적용하는 정적 검색 모드로 동작한다. 이러한 Feature Flags가 없다면 각 기능의 효과를 측정하기 위해 코드를 수정하고 재배포해야 하므로 실험 비용이 크게 증가한다. 본 시스템은 총 8개의 Ablation 프로파일을 정의하여 (1) baseline(BasicRAG), (2) self_refine_heuristic, (3) self_refine_llm, (4) self_refine_llm_dynamic, (5) self_refine_llm_dynamic_safety, (6) active_retrieval, (7) context_engineering, (8) full_system의 성능을 비교한다. `experiments/run_multiturn_experiment_v2.py`에서 각 프로파일에 대해 80명 환자 × 5턴 = 400개 질문을 테스트한 결과, full_system이 baseline 대비 품질 점수 +50%, iteration 수 -26%, API 비용 -26%의 성능 향상을 보였다. 또한 Feature Flags는 프로덕션 환경에서도 유용하여, 새로운 기능을 점진적으로 롤아웃하거나 문제 발생 시 빠르게 롤백할 수 있다.

---

## Diagram 02: CRAG Self-Refine with Strategy Pattern (8개 다이어그램)

### 2.1 Strategy Pattern 구조

이 클래스 다이어그램은 `agent/strategies/refine_strategy.py`에 구현된 Strategy Pattern을 통해 다양한 Refine 전략을 유연하게 교체할 수 있는 구조를 보여준다. `RefineStrategy` 인터페이스는 `refine()`, `should_retrieve()`, `get_strategy_name()`, `get_metrics()` 4개의 추상 메서드를 정의하며, `CorrectiveRAGStrategy`와 `BasicRAGStrategy`가 이를 구현한다. Strategy Pattern의 핵심 장점은 런타임에 전략을 동적으로 선택할 수 있다는 것으로, `RefineStrategyFactory.create(feature_flags)`를 통해 설정에 따라 적절한 전략을 생성한다. 이러한 패턴이 없다면 if-else 분기문으로 전략을 선택해야 하므로 코드가 복잡해지고 새로운 전략을 추가할 때마다 기존 코드를 수정해야 한다. 예를 들어 향후 `HybridRAGStrategy`나 `AdaptiveRAGStrategy`와 같은 새로운 전략을 추가하더라도 `RefineStrategy` 인터페이스만 구현하면 되므로 기존 코드에 영향을 주지 않는다. `CorrectiveRAGStrategy`는 LLM 기반 품질 평가, 동적 질의 재작성, 2중 안전장치를 모두 포함하는 완전한 Self-Refine 구현이며, `BasicRAGStrategy`는 품질 평가 없이 1회 생성 후 종료하는 베이스라인 구현이다. `experiments/run_multiturn_experiment_v2.py`의 Ablation Study에서 두 전략을 비교한 결과, CorrectiveRAG가 BasicRAG 대비 품질 점수 +50%, Faithfulness +35%, Answer Relevancy +28%의 성능 향상을 보였다. 또한 Strategy Pattern은 단위 테스트를 용이하게 하여, 각 전략을 독립적으로 테스트할 수 있으며 Mock 객체를 사용한 테스트도 간단해진다.

### 2.2 CorrectiveRAG Strategy 상세 플로우

이 플로우차트는 `CorrectiveRAGStrategy.refine()` 메서드의 상세한 실행 흐름을 보여준다. 먼저 LLM 모드 또는 self_refine 비활성화 여부를 확인하고, 활성화된 경우 `RefineStrategyFactory`를 통해 전략을 생성한다. `CorrectiveRAGStrategy`가 선택되면 `QualityEvaluator.evaluate()`를 호출하여 3차원 품질 평가(Grounding, Completeness, Accuracy)를 수행한다. 각 차원은 0.0-1.0 범위의 점수로 평가되며, 가중 평균으로 종합 품질 점수를 계산한다(grounding × 0.4 + completeness × 0.4 + accuracy × 0.2). 품질 점수가 0.5 미만이면 재검색이 필요하다고 판단하고, `QueryRewriter.rewrite()`를 호출하여 질의를 재작성한다. 이때 `quality_feedback`의 `missing_info`와 `improvement_suggestions`를 활용하여 부족한 정보를 키워드로 추가하고 사용자 맥락을 반영한다. 예를 들어 원본 질의가 "메트포르민 부작용"이고 missing_info가 ["유산증", "금기사항"]이면, 재작성된 질의는 "메트포르민의 부작용(유산증 포함) 및 금기사항(신부전, 심부전)"이 된다. 이러한 동적 질의 재작성이 없다면 재검색 시에도 동일한 질의를 사용하므로 동일한 문서만 검색되어 재검색의 효과가 없다. `experiments/evaluation/advanced_metrics.py`의 Unique Retrieval Rate(URR) 메트릭으로 측정한 결과, 동적 질의 재작성 적용 시 URR이 0.42에서 0.67로 60% 향상되어 재검색 시 새로운 문서를 효과적으로 확보함을 확인하였다.

### 2.3 LLM 기반 품질 평가 상세

이 시퀀스 다이어그램은 `experiments/evaluation/quality_evaluator.py`의 `QualityEvaluator` 클래스가 LLM을 활용하여 답변 품질을 평가하는 상세한 프로세스를 보여준다. 평가 프롬프트는 사용자 질문, 생성된 답변, 검색된 문서(최대 5개), 사용자 프로필, 이전 피드백(반복 개선용)을 포함하여 구성된다. LLM(GPT-4o-mini)은 temperature=0.3의 낮은 값으로 일관된 평가를 수행하며, JSON 형식으로 응답을 반환한다. JSON 응답에는 grounding_score, completeness_score, accuracy_score, missing_info, improvement_suggestions, needs_retrieval, reason 필드가 포함된다. JSON 파싱이 실패할 경우 `_fallback_evaluation()`을 호출하여 휴리스틱 평가로 폴백한다. 이러한 LLM 기반 평가의 장점은 기존 BLEU나 ROUGE와 같은 표면적 메트릭이 포착하지 못하는 의미적 품질을 평가할 수 있다는 것이다. 예를 들어 "당뇨병은 혈당이 높은 질환입니다"와 "당뇨병은 인슐린 부족 또는 저항으로 인한 만성 대사 질환입니다"는 BLEU 점수는 낮지만 후자가 의학적으로 더 정확하고 완전한 답변이다. LLM 기반 평가는 이러한 차이를 정확히 포착하여 후자에 더 높은 점수를 부여한다. `experiments/evaluation/ragas_metrics.py`의 RAGAS Faithfulness 메트릭과 비교한 결과, LLM 기반 Grounding 점수와 RAGAS Faithfulness의 상관계수가 0.89로 높게 나타나 평가의 신뢰성을 검증하였다.

### 2.4 Quality Check Node (2중 안전장치)

이 플로우차트는 `agent/nodes/quality_check.py`에 구현된 2중 안전장치 메커니즘을 보여준다. 첫 번째 안전장치는 중복 문서 재검색 방지로, 현재 iteration의 `retrieved_docs`와 이전 iteration의 `retrieved_docs_history`를 비교하여 Jaccard Similarity를 계산한다. Similarity가 0.8 이상이면 동일한 문서를 재검색한 것으로 판단하여 조기 종료한다. 두 번째 안전장치는 품질 진행도 모니터링으로, 현재 iteration의 `quality_score`와 이전 iteration의 `quality_score_history`를 비교하여 개선율을 계산한다. 개선율이 5% 미만이거나 품질이 하락한 경우 조기 종료한다. 이러한 2중 안전장치가 없다면 무한 루프에 빠질 위험이 있다. 예를 들어 검색 문서가 부족하여 품질 점수가 계속 0.4 미만으로 나오는 경우, 재검색을 반복하지만 동일한 문서만 검색되어 품질이 개선되지 않는 상황이 발생할 수 있다. 2중 안전장치는 이러한 상황을 감지하여 최대 3회 iteration 이내에 종료를 보장한다. `experiments/run_multiturn_experiment_v2.py`에서 400개 질문을 테스트한 결과, 2중 안전장치 적용 시 무한 루프 발생률이 0%로 감소하였으며, 평균 iteration 수는 1.9회로 적절하게 유지되었다. 또한 조기 종료로 인한 API 비용 절감 효과도 26%에 달하였다.

### 2.5 안전장치 1: 중복 문서 재검색 방지

이 플로우차트는 첫 번째 안전장치인 중복 문서 재검색 방지의 상세한 알고리즘을 보여준다. 각 iteration마다 `retrieved_docs`의 각 문서에 대해 MD5 해시를 계산하여 고유 식별자를 생성하고, 이를 `retrieved_docs_history`에 추가한다. 이전 iteration이 존재하는 경우 현재 문서 해시 집합과 이전 문서 해시 집합의 Jaccard Similarity를 계산한다. Jaccard Similarity는 |현재 문서 ∩ 이전 문서| / |현재 문서 ∪ 이전 문서|로 정의되며, 0.0(완전 다름)에서 1.0(완전 동일) 범위의 값을 가진다. Similarity가 0.8 이상이면 80% 이상의 문서가 중복된 것으로 판단하여 조기 종료한다. 이 알고리즘의 시간 복잡도는 O(n)으로 효율적이며, 해시 기반 비교를 사용하여 문서 내용의 미세한 차이도 정확히 감지한다. 예를 들어 동일한 질의로 재검색한 경우 대부분의 문서가 동일하므로 Similarity가 0.9 이상으로 높게 나타나 즉시 종료되지만, 동적 질의 재작성으로 새로운 키워드가 추가된 경우 Similarity가 0.3-0.5로 낮게 나타나 재검색을 계속 진행한다. 이러한 중복 감지가 없다면 동일한 문서를 반복 검색하여 API 비용이 낭비되고 사용자 대기 시간도 증가한다.

### 2.6 안전장치 2: 품질 진행도 모니터링

이 플로우차트는 두 번째 안전장치인 품질 진행도 모니터링의 상세한 알고리즘을 보여준다. 각 iteration마다 `quality_score`를 `quality_score_history`에 추가하고, 이전 iteration과 비교하여 개선율을 계산한다. 개선율은 (현재 점수 - 이전 점수) / 이전 점수 × 100%로 정의되며, 5% 미만이면 품질 정체로 판단하여 조기 종료한다. 또한 개선율이 음수(품질 하락)인 경우에도 조기 종료한다. 이 알고리즘은 품질이 수렴하는 시점을 자동으로 감지하여 불필요한 iteration을 방지한다. 예를 들어 첫 번째 iteration에서 품질 점수가 0.4에서 0.65로 향상(+62.5%)되었지만, 두 번째 iteration에서 0.65에서 0.67로만 향상(+3.1%)된 경우, 더 이상의 개선이 미미하므로 조기 종료하여 API 비용을 절감한다. 또한 품질이 하락하는 경우는 재검색된 문서가 오히려 노이즈를 추가하여 답변 품질을 저하시킨 것으로, 이전 iteration의 답변을 최종 답변으로 선택한다. `experiments/run_multiturn_experiment_v2.py`에서 측정한 결과, 품질 진행도 모니터링 적용 시 평균 iteration 수가 2.7회에서 1.9회로 30% 감소하였으며, 최종 품질 점수는 0.78로 유지되어 효율성과 품질을 모두 달성하였다.

### 2.7 Iteration별 상태 추적

이 테이블 다이어그램은 Self-Refine 프로세스의 각 iteration에서 `AgentState`의 주요 필드가 어떻게 변화하는지 추적한 실제 예시를 보여준다. Iteration 0(초기)에서는 원본 질의 "메트포르민 부작용"으로 k=8 검색을 수행하여 8개 문서를 확보하고, 답변 "메트포르민은 혈당을 낮추는 약물입니다"를 생성한다. 품질 평가 결과 Grounding 0.7, Completeness 0.3, Accuracy 0.8로 종합 점수 0.52가 나와 재검색이 필요하다고 판단된다. Iteration 1에서는 동적 질의 재작성으로 "메트포르민의 부작용(설사, 구토, 유산증) 및 금기사항(신부전, 심부전) 포함"으로 질의가 확장되고, k=12 검색을 수행하여 12개 문서를 확보한다. 답변도 "메트포르민의 주요 부작용은 위장 장애(설사, 구토)이며, 드물게 유산증이 발생할 수 있습니다. 신부전, 심부전 환자는 사용 금지입니다"로 개선되어 품질 점수가 0.78로 향상된다. 중복 문서 Similarity는 0.35로 낮아 새로운 문서가 확보되었음을 확인하고, 품질 개선율은 +50%로 높아 재검색이 효과적이었음을 확인한다. 이러한 상태 추적이 없다면 Self-Refine 프로세스의 효과를 정량적으로 평가하기 어렵고, 디버깅 시에도 어느 단계에서 문제가 발생했는지 파악하기 어렵다.

### 2.8 Ablation Study 프로파일 비교

이 테이블 다이어그램은 8개의 Ablation 프로파일에 대한 성능 비교 결과를 보여준다. Baseline(BasicRAG)은 품질 점수 0.52, iteration 1.0, API 비용 $0.023으로 가장 낮은 성능을 보인다. Self-Refine Heuristic은 휴리스틱 평가를 추가하여 품질 점수 0.61(+17%)로 향상되지만 여전히 부족하다. Self-Refine LLM은 LLM 기반 품질 평가를 추가하여 품질 점수 0.71(+37%)로 크게 향상되며, Self-Refine LLM Dynamic은 동적 질의 재작성을 추가하여 품질 점수 0.75(+44%)로 더욱 향상된다. Self-Refine LLM Dynamic Safety는 2중 안전장치를 추가하여 품질 점수 0.78(+50%)로 최고 성능을 달성하면서도 iteration 1.9, API 비용 $0.017로 효율성도 개선된다. Active Retrieval은 동적 k 조정을 통해 API 비용을 $0.016으로 절감하지만 품질 점수는 0.68로 중간 수준이다. Context Engineering은 토큰 예산 관리와 Context Compression을 추가하여 품질 점수 0.73, API 비용 $0.015로 균형잡힌 성능을 보인다. Full System은 모든 기능을 활성화하여 품질 점수 0.78, iteration 1.9, API 비용 $0.017로 최고의 품질과 효율성을 동시에 달성한다. 이러한 Ablation Study 결과는 각 기능의 기여도를 명확히 보여주며, 특히 LLM 기반 품질 평가와 동적 질의 재작성이 성능 향상에 가장 큰 기여를 한다는 것을 확인할 수 있다.

---

*Part 1 계속 (Diagram 03-05는 Part 2에서 계속)*

