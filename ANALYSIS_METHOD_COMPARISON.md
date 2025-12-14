# 결과 분석 방법 비교 및 통합 결정

## 📊 현재 상황 분석

### 방법 1: `10_analyze_results.bat` (기존)
**실행 스크립트**:
- `validate_run.py`
- `check_fairness.py`
- `summarize_run.py`
- `make_paper_tables.py`
- `make_paper_figures.py`
- `show_summary_stats.py`

**출력 위치**: `runs/<run_id>/`
- `summary.json`
- `tables/`
- `figures/`

**단점**:
- ❌ 멀티턴 컨텍스트 지표 (CUS, UR, CCR) 미포함
- ❌ LaTeX 테이블 미생성
- ❌ 출력 디렉토리 구조화 부족

---

### 방법 2: `run_paper_pipeline.py` (신규)
**실행 스크립트**:
- `validate_run.py`
- `check_fairness.py`
- `summarize_run.py`
- `evaluate_metrics_from_run.py` (멀티턴 컨텍스트 지표)
- `integrate_multiturn_metrics.py` (통합)
- `make_paper_tables.py`
- `make_paper_figures.py`
- `make_latex_tables.py`

**출력 위치**: `<output_dir>/paper_assets/`
- `summary.json` (모든 지표 통합)
- `tables/`
- `figures/`
- `latex/`

**장점**:
- ✅ 멀티턴 컨텍스트 지표 자동 포함
- ✅ LaTeX 테이블 생성
- ✅ 출력 디렉토리 구조화
- ✅ 모든 기능 통합

---

## 🎯 통합 결정

### 선택: `run_paper_pipeline.py` 기준 통합

**이유**:
1. **기존 코드 무결성 최소화**: 기존 스크립트 모두 재사용
2. **스캐폴드 연계**: 멀티턴 컨텍스트 지표와 완벽 통합
3. **정밀도 및 효율성**: 모든 평가 지표 포함, 자동화 완성도 높음

### 통합 계획:
1. `10_analyze_results.bat` → `run_paper_pipeline.py` 호출 래퍼로 변경
2. `integrate_multiturn_metrics.py` → `run_paper_pipeline.py`에 통합 (별도 스크립트 불필요)
3. `PAPER_ASSETS_GUIDE.md` 업데이트

---

## ✅ 최종 구조

### 단일 진입점: `10_analyze_results.bat`
- Windows 배치 파일 (사용자 친화적)
- `run_paper_pipeline.py` 호출
- 출력 위치: `runs/<run_id>/paper_assets/`

### 핵심 파이프라인: `run_paper_pipeline.py`
- 모든 분석 단계 자동화
- 멀티턴 컨텍스트 지표 자동 포함
- 완전한 논문 자료 생성

