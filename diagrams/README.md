# Context Engineering 기반 의학지식 AI Agent - 다이어그램 모음

본 디렉토리는 석사 논문 "Context Engineering 기반 의학지식 AI Agent 설계"에 포함된 모든 다이어그램을 포함합니다.

## 📋 목차

- [제3장: 연구방법론 다이어그램](#제3장-연구방법론-다이어그램)
- [핵심 다이어그램 (우선순위 높음)](#핵심-다이어그램-우선순위-높음)
- [보조 다이어그램](#보조-다이어그램)
- [다이어그램 생성 가이드](#다이어그램-생성-가이드)

---

## 제3장: 연구방법론 다이어그램

### 🌟 핵심 다이어그램 (우선순위 높음)

이 8개의 다이어그램은 논문의 핵심 개념을 설명하는 필수 다이어그램입니다.

#### 1. Context Engineering 4단계 순환 프로세스
- **파일**: `diagram_01_context_engineering_4_stages.md`
- **섹션**: 제3.1절 - 연구 목표 및 접근 방법
- **내용**: 추출 → 저장 → 주입 → 검증의 4단계 순환 프로세스
- **주요 시각화**: 
  - 4단계 플로우차트
  - 의사 진료 프로세스와의 비교
  - 정량적 효과 표
- **중요도**: ⭐⭐⭐⭐⭐

#### 5. 6개 슬롯 체계 구조도
- **파일**: `diagram_05_6_slot_system.md`
- **섹션**: 제3.2.2절 - 1단계: 추출(Extraction)
- **내용**: Demographics, Conditions, Symptoms, Medications, Vitals, Labs 슬롯
- **주요 시각화**:
  - 슬롯별 데이터 구조
  - MedCAT2 + Regex 추출 방법
  - 시간 가중치 적용
- **중요도**: ⭐⭐⭐⭐⭐

#### 15. Self-Refine 순환 구조 상세 플로우차트
- **파일**: `diagram_15_self_refine_detailed.md`
- **섹션**: 제3.2.5절 - 4단계: 검증(Verification)
- **내용**: LLM Judge 기반 품질 평가, 동적 질의 재작성, 이중 안전장치
- **주요 시각화**:
  - 초기 생성 → 평가 → 재작성 → 재검색 → 재생성 순환
  - 품질 점수 변화 추적
  - 안전장치 작동 원리
- **중요도**: ⭐⭐⭐⭐⭐

#### 18. 전체 워크플로우 플로우차트 (10개 노드)
- **파일**: `diagram_18_full_workflow.md`
- **섹션**: 제3.3절 - LangGraph 기반 순환식 시스템 아키텍처
- **내용**: 10개 노드의 전체 실행 흐름
- **주요 시각화**:
  - check_similarity → classify_intent → extract_slots → ... → store_response
  - 조건부 엣지 및 라우팅 로직
  - 경로별 처리 시간 분석
- **중요도**: ⭐⭐⭐⭐⭐

#### 20. AgentState 필드 분류 다이어그램
- **파일**: `diagram_20_agentstate.md`
- **섹션**: 제3.3.5절 - AgentState 설계
- **내용**: 28개 필드를 7개 카테고리로 분류
- **주요 시각화**:
  - 입력, Context Engineering, 검색, 생성, Self-Refine, 캐시, 설정
  - 필드별 타입 및 예시
  - 노드 간 상태 전달 흐름
- **중요도**: ⭐⭐⭐⭐

#### 22. Active Retrieval 3단계 분류 플로우차트
- **파일**: `diagram_22_active_retrieval.md`
- **섹션**: 제3.4.2절 - 능동적 검색 (Active Retrieval)
- **내용**: Rule-based → Slot-based → Content-based 3단계 분류
- **주요 시각화**:
  - 질의 복잡도 판단 (Simple/Moderate/Complex)
  - 동적 k 결정 (3/8/15)
  - 레이턴시 및 비용 절감 효과
- **중요도**: ⭐⭐⭐⭐⭐

#### 24. 하이브리드 검색 (BM25 + FAISS + RRF) 구조도
- **파일**: `diagram_24_hybrid_retrieval.md`
- **섹션**: 제3.4.3절 - 하이브리드 검색 (Hybrid Retrieval)
- **내용**: BM25 키워드 검색 + FAISS 벡터 검색 + RRF 융합
- **주요 시각화**:
  - BM25 수식 및 예시 계산
  - FAISS 코사인 유사도
  - RRF 순위 융합
  - 성능 비교 (Precision/Recall/MRR)
- **중요도**: ⭐⭐⭐⭐⭐

#### 28. 정량적 성능 개선 종합 막대 그래프
- **파일**: `diagram_28_quantitative_improvements.md`
- **섹션**: 제3.5절 - 차별성 및 기여도 종합
- **내용**: 모든 메트릭의 Before/After 비교
- **주요 시각화**:
  - Faithfulness, Relevance, Perplexity, Latency, Cost
  - Self-Refine, Active Retrieval, Hybrid Retrieval, Cache 효과
  - Ablation Study 결과
  - 통계적 유의성 (t-test, Cohen's d)
- **중요도**: ⭐⭐⭐⭐⭐

---

### 📊 보조 다이어그램

아래 다이어그램들은 논문에서 언급되었으나 아직 파일로 생성되지 않은 것들입니다.
필요에 따라 추가 생성 가능합니다.

#### 2. 연구 수행 절차 타임라인
- **섹션**: 제3.1.2절
- **내용**: 1-4단계 연구 절차 (6-8개월 타임라인)

#### 3. 기존 시스템 vs 본 연구 비교 다이어그램
- **섹션**: 제3.1.3절
- **내용**: 6가지 비교 항목 표 시각화

#### 4. Context Engineering과 의사 진료 프로세스 비교
- **섹션**: 제3.2.1절
- **내용**: 의사의 문진/차트/판단/검증 vs AI의 4단계

#### 6. MedCAT2 추출 프로세스 플로우차트
- **섹션**: 제3.2.2.2절
- **내용**: 텍스트 → NER → CUI 매핑 → TUI 분류

#### 7. MedCAT2 + 정규표현식 결합 구조도
- **섹션**: 제3.2.2.3절
- **내용**: 두 방법의 상호 보완 관계

#### 8. ProfileStore 아키텍처 다이어그램
- **섹션**: 제3.2.3.1절
- **내용**: 클래스 구조, 메서드, 저장소

#### 9. 시간 가중치 감쇠 곡선 그래프
- **섹션**: 제3.2.3.2절
- **내용**: exp(-λt) 곡선, 슬롯별 감쇠율

#### 10. PatientProfile 스키마 클래스 다이어그램
- **섹션**: 제3.2.3.4절
- **내용**: TypedDict 스키마 UML

#### 11. 다층 프롬프트 구조 다이어그램
- **섹션**: 제3.2.4.1절
- **내용**: 4개 섹션 (시스템/프로필/근거/질의)

#### 12. 토큰 예산 할당 파이 차트
- **섹션**: 제3.2.4.5절
- **내용**: 5%+10%+50%+15%+5%+15%

#### 13. LLM 기반 품질 평가 프로세스 플로우차트
- **섹션**: 제3.2.5.2절
- **내용**: LLM Judge 입출력

#### 14. 동적 질의 재작성 Before/After 비교
- **섹션**: 제3.2.5.3절
- **내용**: 원본 vs 재작성 질의 예시

#### 16. 이중 안전장치 작동 원리 다이어그램
- **섹션**: 제3.2.5.5절
- **내용**: 중복 문서 감지 + 품질 정체 감지

#### 17. 10개 노드 상세 역할 다이어그램
- **섹션**: 제3.3.2절
- **내용**: 노드별 입출력, 처리 시간

#### 19. 조건부 엣지 라우팅 결정 트리
- **섹션**: 제3.3.4절
- **내용**: 4가지 라우팅 로직

#### 21. 응답 캐시 작동 흐름도
- **섹션**: 제3.4.1절
- **내용**: 벡터 유사도 → 캐시 히트/미스

#### 23. 복잡도별 k 값 분포 막대 그래프
- **섹션**: 제3.4.2.2절
- **내용**: Greeting(0), Simple(3), Moderate(8), Complex(15)

#### 25. 검색 방법별 성능 비교 막대 그래프
- **섹션**: 제3.4.3.4절
- **내용**: BM25 vs FAISS vs Hybrid

#### 26. 성능 최적화 전후 레이턴시 비교 그래프
- **섹션**: 제3.4.4절
- **내용**: 그래프 캐싱, 설정 캐싱, heapq 등

#### 27. 기존 연구 vs 본 연구 비교표 (시각화)
- **섹션**: 제3.5.1절
- **내용**: 5가지 차별점 표

---

## 다이어그램 생성 가이드

### Mermaid 다이어그램 렌더링

모든 다이어그램은 Mermaid 형식으로 작성되어 있어 다음 도구로 렌더링할 수 있습니다:

1. **GitHub**: `.md` 파일을 GitHub에 푸시하면 자동으로 Mermaid가 렌더링됩니다.
2. **Mermaid Live Editor**: https://mermaid.live/
3. **VS Code**: Mermaid Preview 확장 설치
4. **Typora**: 마크다운 에디터에서 자동 렌더링

### PNG/SVG 이미지로 변환

논문에 삽입하려면 이미지 파일로 변환이 필요합니다:

```bash
# Mermaid CLI 설치
npm install -g @mermaid-js/mermaid-cli

# 단일 파일 변환
mmdc -i diagram_01_context_engineering_4_stages.md -o diagram_01.png

# 전체 디렉토리 일괄 변환
for file in diagram_*.md; do
    mmdc -i "$file" -o "${file%.md}.png"
done
```

### 다이어그램 스타일 커스터마이징

각 다이어그램의 색상은 다음 팔레트를 사용합니다:

```
- #e3f2fd: 파란색 계열 (입력, 캐시)
- #fff3e0: 주황색 계열 (Context Engineering: 저장)
- #f3e5f5: 보라색 계열 (검색)
- #ffecb3: 노란색 계열 (생성)
- #c8e6c9: 초록색 계열 (Self-Refine, 최종 답변)
- #f8bbd0: 분홍색 계열 (활력징후, 캐시)
- #c5cae9: 남색 계열 (종료, 결과)
- #ffcdd2: 빨간색 계열 (경고, 재검색)
```

---

## 추가 생성된 다이어그램

### 제1장 (서론)
- **[추가 A]** 연구 배경 및 동기 마인드맵 ✅ **완료**
  - 파일: `diagram_additional_A_research_motivation.md`
  - 내용: 문제 인식 → 필요성 → 연구 목표 → 기대 효과 (4단계)
  - 상세 설명 포함
- **[추가 B]** 연구 목표와 기대 효과 관계도 (선택적)

### 제2장 (관련 연구)
- **[추가 C]** RAG 발전 타임라인 (2020-2025) ✅ **완료**
  - 파일: `diagram_additional_C_rag_timeline.md`
  - 내용: 2020년 RAG 탄생 → 2025년 본 연구 (5년 발전 과정)
  - 각 시기별 상세 설명 및 본 연구의 위치 강조
- **[추가 D]** 의료 AI 챗봇 분류 체계도 (선택적)

### 제4장 (실험 및 결과, 향후 작성)
- **[추가 E]** 실험 설계 다이어그램
- **[추가 F]** Synthea 가상 환자 생성 프로세스
- **[추가 G]** 정량적 메트릭 비교 박스플롯
- **[추가 H]** Ablation Study 결과 히트맵

### 제5장 (결론, 향후 작성)
- **[추가 I]** 향후 연구 로드맵
- **[추가 J]** 계층적 메모리 (Hierarchical Memory) 설계안

---

## 생성된 다이어그램 현황

| 번호 | 제목 | 파일명 | 상태 | 우선순위 |
|-----|------|--------|------|----------|
| 1 | Context Engineering 4단계 | diagram_01_context_engineering_4_stages.md | ✅ 완료 | ⭐⭐⭐⭐⭐ |
| 5 | 6개 슬롯 체계 | diagram_05_6_slot_system.md | ✅ 완료 | ⭐⭐⭐⭐⭐ |
| 15 | Self-Refine 상세 | diagram_15_self_refine_detailed.md | ✅ 완료 | ⭐⭐⭐⭐⭐ |
| 18 | 전체 워크플로우 | diagram_18_full_workflow.md | ✅ 완료 | ⭐⭐⭐⭐⭐ |
| 20 | AgentState 구조 | diagram_20_agentstate.md | ✅ 완료 | ⭐⭐⭐⭐ |
| 22 | Active Retrieval | diagram_22_active_retrieval.md | ✅ 완료 | ⭐⭐⭐⭐⭐ |
| 24 | 하이브리드 검색 | diagram_24_hybrid_retrieval.md | ✅ 완료 | ⭐⭐⭐⭐⭐ |
| 28 | 정량적 성능 개선 | diagram_28_quantitative_improvements.md | ✅ 완료 | ⭐⭐⭐⭐⭐ |
| A | 연구 배경 및 동기 | diagram_additional_A_research_motivation.md | ✅ 완료 | ⭐⭐⭐⭐ |
| C | RAG 발전 타임라인 | diagram_additional_C_rag_timeline.md | ✅ 완료 | ⭐⭐⭐⭐ |
| 2-4, 6-14, 16-17, 19, 21, 23, 25-27 | 보조 다이어그램들 | - | ⏳ 대기 | ⭐⭐⭐ |

---

## 사용 예시

### 논문에 다이어그램 삽입

```latex
\begin{figure}[h]
    \centering
    \includegraphics[width=0.9\textwidth]{diagrams/diagram_01.png}
    \caption{Context Engineering 4단계 순환 프로세스}
    \label{fig:context_engineering_4_stages}
\end{figure}

본 연구에서 제안하는 Context Engineering은 Figure \ref{fig:context_engineering_4_stages}와 같이...
```

### 마크다운 문서에 삽입

```markdown
## Context Engineering

![Context Engineering 4단계](diagrams/diagram_01.png)

본 시스템은 추출, 저장, 주입, 검증의 4단계 순환 프로세스를 통해...
```

---

## 라이선스

이 다이어그램들은 "Context Engineering 기반 의학지식 AI Agent 설계" 석사 논문의 일부로 작성되었습니다.

- **작성자**: [저자명]
- **소속**: [대학/연구소]
- **작성일**: 2025년 12월 12일

---

## 문의

다이어그램 관련 문의사항이나 오류 발견 시 연락 주세요.

