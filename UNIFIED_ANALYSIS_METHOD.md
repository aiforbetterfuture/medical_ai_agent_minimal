# 통합된 결과 분석 방법

## ✅ 통합 완료

결과 분석 방법이 **단일 통합 파이프라인**으로 통합되었습니다.

---

## 🚀 사용 방법

### Windows 배치 파일 (권장)

```bash
10_analyze_results.bat
```

### Python 스크립트 직접 실행

```bash
python scripts/run_paper_pipeline.py --run_dir runs/2025-12-13_primary_v1
```

---

## 📋 실행 단계

1. ✅ **데이터 검증** (`validate_run.py`)
2. ✅ **공정성 검증** (`check_fairness.py`)
3. ✅ **통계 분석** (`summarize_run.py`) - RAGAS 지표 포함
4. ✅ **멀티턴 컨텍스트 지표 평가** (`evaluate_metrics_from_run.py`) - CUS, UR, CCR
5. ✅ **멀티턴 컨텍스트 지표 통합** (summary.json에 자동 추가)
6. ✅ **CSV 표 생성** (`make_paper_tables.py`)
7. ✅ **그래프 생성** (`make_paper_figures.py`)
8. ✅ **LaTeX 테이블 생성** (`make_latex_tables.py`)
9. ✅ **요약 통계 출력** (`show_summary_stats.py`)

---

## 📁 출력 위치

모든 결과는 다음 위치에 생성됩니다:

```
runs/2025-12-13_primary_v1/paper_assets/
├── summary.json                    # 모든 지표 통합
├── tables/                         # CSV 표
├── figures/                        # PNG/PDF 그래프
└── latex/                          # LaTeX 테이블
```

---

## ✅ 포함된 평가 지표

### 1층: 표준 RAG/QA 지표 (RAGAS)
- Faithfulness
- Answer Relevance
- Context Precision
- Context Recall
- Context Relevancy
- Perplexity

### 2층: 멀티턴 컨텍스트 지표 (논문 핵심)
- **CUS** (Context Utilization Score)
- **UR** (Update Responsiveness)
- **CCR** (Context Contradiction Rate)

---

## 🔧 변경 사항

### 삭제된 파일
- ❌ `scripts/integrate_multiturn_metrics.py` (통합 로직이 `run_paper_pipeline.py`에 포함됨)

### 수정된 파일
- ✅ `10_analyze_results.bat` → `run_paper_pipeline.py` 호출 래퍼로 변경
- ✅ `scripts/run_paper_pipeline.py` → 멀티턴 컨텍스트 지표 통합 로직 포함
- ✅ `PAPER_ASSETS_GUIDE.md` → 통합된 방법으로 업데이트

---

## 📚 참고 문서

- `PAPER_ASSETS_GUIDE.md`: 상세한 결과 파일 가이드
- `ANALYSIS_METHOD_COMPARISON.md`: 통합 결정 근거

---

**작성일**: 2025-12-13  
**버전**: 1.0 (통합 완료)

