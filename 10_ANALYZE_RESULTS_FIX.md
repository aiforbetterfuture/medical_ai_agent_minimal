# 10번 파일 결과 분석 스크립트 수정 사항

## 📋 문제점

10번 파일(`10_analyze_results.bat`)이 결과 분석을 실행하지 못하는 원인:

1. **스크립트 인자 형식 오류**: 각 Python 스크립트가 요구하는 인자 형식과 다름
2. **summary.json 구조 불일치**: 출력 코드에서 사용하는 키가 실제 summary.json 구조와 다름

---

## ✅ 수정 사항

### 1. 스크립트 호출 인자 수정

#### `validate_run.py`
- **수정 전**: `scripts\validate_run.py %RUN_DIR%`
- **수정 후**: `scripts\validate_run.py --run_dir %RUN_DIR%`

#### `check_fairness.py`
- **수정 전**: `scripts\check_fairness.py %RUN_DIR%`
- **수정 후**: `scripts\check_fairness.py --events_path %RUN_DIR%\events.jsonl`

#### `summarize_run.py`
- **수정 전**: `scripts\summarize_run.py %RUN_DIR%`
- **수정 후**: `scripts\summarize_run.py --run_dir %RUN_DIR%`

#### `make_paper_tables.py`
- **수정 전**: `scripts\make_paper_tables.py %RUN_DIR%`
- **수정 후**: `scripts\make_paper_tables.py --summary_json %RUN_DIR%\summary.json --output_dir %RUN_DIR%\tables`
- **추가**: `summary.json` 존재 확인 및 `tables` 디렉토리 자동 생성

#### `make_paper_figures.py`
- **수정 전**: `scripts\make_paper_figures.py %RUN_DIR%`
- **수정 후**: `scripts\make_paper_figures.py --summary_json %RUN_DIR%\summary.json --output_dir %RUN_DIR%\figures`
- **추가**: `figures` 디렉토리 자동 생성

---

### 2. summary.json 구조에 맞춘 출력 코드 수정

#### 수정 전 (잘못된 키 사용)
```python
s["overall"]["total_events"]
s["overall"]["llm_mean_latency_ms"]
s["overall"]["agent_mean_latency_ms"]
s["overall"]["paired_ttest_pvalue"]
s["overall"]["cohens_d"]
```

#### 수정 후 (올바른 키 사용)
```python
s.get('counts', {}).get('total_events', 0)
s.get('efficiency', {}).get('latency', {}).get('by_mode', {}).get('llm', {}).get('mean', 0)
s.get('efficiency', {}).get('latency', {}).get('by_mode', {}).get('agent', {}).get('mean', 0)
comps[0].get('t_test_p_value', 0) if comps else 0
comps[0].get('effect_size_cohens_d', 0) if comps else 0
```

---

### 3. 파일명 업데이트

논문 작성 가이드의 파일명을 실제 생성되는 파일명에 맞게 수정:

- `tables\main_results.csv` → `tables\overall_comparison.csv`
- `tables\by_turn.csv` → `tables\per_turn_comparison.csv`
- `tables\efficiency.csv` → `tables\efficiency_metrics.csv`
- `figures\latency_comparison.png` → `figures\overall_comparison.png`
- `figures\by_turn.png` → `figures\per_turn_trends.png`
- 추가: `figures\efficiency_comparison.png`, `figures\effect_sizes.png`

---

## 📊 summary.json 구조

실제 `summary.json`의 구조:

```json
{
  "schema_version": "summary.v1",
  "run_id": "2025-12-13_primary_v1",
  "counts": {
    "total_events": 780,
    "completed_pairs": 390
  },
  "efficiency": {
    "latency": {
      "by_mode": {
        "llm": {
          "metric": "latency_ms",
          "mean": 1234.5,
          "std": 234.5,
          "min": 800.0,
          "max": 2000.0
        },
        "agent": {
          "metric": "latency_ms",
          "mean": 2345.6,
          "std": 345.6,
          "min": 1500.0,
          "max": 3000.0
        }
      }
    },
    "cost": { ... },
    "cache": { ... }
  },
  "comparisons": {
    "paired_agent_minus_llm": [
      {
        "metric": "faithfulness",
        "n_pairs": 390,
        "delta_mean": 0.05,
        "delta_std": 0.12,
        "t_test_p_value": 0.001,
        "effect_size_cohens_d": 0.42
      },
      ...
    ]
  }
}
```

---

## 🚀 사용 방법

이제 10번 파일을 실행하면:

1. **데이터 검증**: `validate_run.py` 실행
2. **공정성 검증**: `check_fairness.py` 실행
3. **통계 분석**: `summarize_run.py` 실행 → `summary.json` 생성
4. **표 생성**: `make_paper_tables.py` 실행 → `tables/*.csv` 생성
5. **그래프 생성**: `make_paper_figures.py` 실행 → `figures/*.png` 생성

---

## 📝 생성되는 파일

### 통계 요약
- `runs/2025-12-13_primary_v1/summary.json`

### CSV 표
- `runs/2025-12-13_primary_v1/tables/overall_comparison.csv`
- `runs/2025-12-13_primary_v1/tables/per_turn_comparison.csv`
- `runs/2025-12-13_primary_v1/tables/efficiency_metrics.csv`
- `runs/2025-12-13_primary_v1/tables/ablation_comparison.csv` (있는 경우)

### 그래프
- `runs/2025-12-13_primary_v1/figures/overall_comparison.png` (및 `.pdf`)
- `runs/2025-12-13_primary_v1/figures/per_turn_trends.png` (및 `.pdf`)
- `runs/2025-12-13_primary_v1/figures/efficiency_comparison.png` (및 `.pdf`)
- `runs/2025-12-13_primary_v1/figures/effect_sizes.png` (및 `.pdf`)

---

## ✅ 검증 완료

모든 스크립트 호출이 올바른 인자 형식으로 수정되었으며, `summary.json` 구조에 맞게 출력 코드도 수정되었습니다.

이제 10번 파일을 실행하면 정상적으로 결과 분석이 수행됩니다.

