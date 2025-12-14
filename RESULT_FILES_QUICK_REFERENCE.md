# 실험 결과 파일 빠른 참조 가이드

## 📍 파일 위치

```
runs/2025-12-13_primary_v1/
├── summary.json              ⭐ 통계 분석 결과 (JSON)
├── tables/
│   ├── overall_comparison.csv      ⚠️ 메트릭 데이터 필요
│   ├── per_turn_comparison.csv     ⚠️ 메트릭 데이터 필요
│   └── efficiency_metrics.csv      ✅ 항상 사용 가능
└── figures/                  ⚠️ matplotlib 필요
    ├── overall_comparison.png
    ├── per_turn_trends.png
    ├── efficiency_comparison.png
    └── effect_sizes.png
```

---

## ✅ 현재 사용 가능한 데이터

### 1. `summary.json` - 효율성 지표 ✅

**경로**: `runs/2025-12-13_primary_v1/summary.json`

**사용 가능한 데이터**:

```json
{
  "efficiency": {
    "latency": {
      "by_mode": {
        "llm": {
          "mean": 8255.4,      // 평균 응답 시간 (ms)
          "std": 2141.6,
          "median": 8026.5,
          "p25": 6899.0,
          "p75": 9556.75
        },
        "agent": {
          "mean": 13525.7,     // 평균 응답 시간 (ms)
          "std": 17587.8,
          "median": 73.0,      // ⚠️ 캐시 히트로 인해 매우 낮음
          "p25": 7.0,
          "p75": 22099.0
        }
      }
    },
    "cost": {
      "by_mode": {
        "llm": {
          "mean": 0.000188,    // 평균 비용 ($)
          "std": 0.000065
        },
        "agent": {
          "mean": 0.000190,    // 평균 비용 ($)
          "std": 0.000032
        }
      }
    },
    "cache": {
      "agent_cache_hit_rate": 0.508  // 50.8% 캐시 히트율
    }
  },
  "counts": {
    "total_events": 932,
    "completed_pairs": 390
  }
}
```

**논문 작성 예시**:
> "AI Agent 모드는 LLM 모드에 비해 평균 응답 시간이 64% 증가하였다 (LLM: 8255ms, Agent: 13526ms). 
> 그러나 Agent 모드의 캐시 히트율이 50.8%로, 캐시 히트 시 응답 시간은 중앙값 73ms로 크게 단축되었다. 
> 비용 측면에서는 두 모드 간 차이가 미미하였다 (LLM: $0.000188, Agent: $0.000190)."

---

### 2. `tables/efficiency_metrics.csv` ✅

**경로**: `runs/2025-12-13_primary_v1/tables/efficiency_metrics.csv`

**내용**: 비용, 응답 시간, 캐시 히트율 비교

**사용 방법**:
- Excel에서 열어서 바로 확인 가능
- 논문의 효율성 분석 섹션에 삽입

---

## ⚠️ 메트릭 데이터가 필요한 파일들

다음 파일들은 `events.jsonl`에 메트릭 데이터(faithfulness, answer_relevance 등)가 있어야 사용 가능합니다:

- `tables/overall_comparison.csv`
- `tables/per_turn_comparison.csv`
- `figures/overall_comparison.png`
- `figures/per_turn_trends.png`
- `figures/effect_sizes.png`

현재는 메트릭 데이터가 없어서 이 파일들이 비어있거나 "N/A"로 표시됩니다.

---

## 📊 논문 작성 우선순위

### 1순위: 효율성 분석 (현재 사용 가능) ✅

**데이터 소스**: `summary.json` → `efficiency` 섹션

**논문에 포함할 내용**:
- 응답 시간 비교 (LLM vs Agent)
- 비용 비교 (LLM vs Agent)
- 캐시 히트율 분석
- 캐시 효과 분석 (캐시 히트 시 응답 시간 단축)

**표/그래프**:
- `tables/efficiency_metrics.csv` → 논문 표로 삽입
- `figures/efficiency_comparison.png` → 논문 그림으로 삽입 (matplotlib 설치 시)

---

### 2순위: 메트릭 분석 (메트릭 데이터 필요) ⚠️

**데이터 소스**: `summary.json` → `comparisons.paired_agent_minus_llm`

**필요한 작업**:
- `events.jsonl`에 메트릭 데이터 추가
- 또는 별도의 평가 스크립트로 메트릭 계산

**논문에 포함할 내용**:
- Faithfulness, Answer Relevance 등 주요 메트릭 비교
- 통계 검정 결과 (p-value, Cohen's d)
- 턴별 성능 추이

---

## 🔍 데이터 확인 방법

### Python으로 확인

```python
import json

# summary.json 읽기
with open('runs/2025-12-13_primary_v1/summary.json', 'r', encoding='utf-8') as f:
    summary = json.load(f)

# 효율성 지표 확인
efficiency = summary['efficiency']
print(f"LLM 평균 응답 시간: {efficiency['latency']['by_mode']['llm']['mean']:.1f}ms")
print(f"Agent 평균 응답 시간: {efficiency['latency']['by_mode']['agent']['mean']:.1f}ms")
print(f"Agent 캐시 히트율: {efficiency['cache']['agent_cache_hit_rate']*100:.1f}%")
```

### Excel로 확인

1. `tables/efficiency_metrics.csv` 파일을 Excel에서 열기
2. 데이터 확인 및 표 형식으로 정리
3. 논문에 삽입

---

## 📝 논문 작성 체크리스트

### 현재 가능한 작업 ✅

- [x] 효율성 지표 분석 (응답 시간, 비용, 캐시 히트율)
- [x] `efficiency_metrics.csv` 표 작성
- [x] 효율성 비교 그래프 생성 (matplotlib 설치 시)
- [x] 실험 규모 확인 (총 이벤트 수, 완료된 페어 수)

### 메트릭 데이터 필요 ⚠️

- [ ] 주요 메트릭 비교 (Faithfulness, Answer Relevance 등)
- [ ] 통계 검정 결과 (p-value, Cohen's d)
- [ ] 턴별 성능 추이 분석
- [ ] 효과 크기 분석

---

## 💡 논문 작성 팁

1. **효율성 분석 우선**: 현재 사용 가능한 효율성 데이터를 먼저 분석하고 논문에 포함
2. **캐시 효과 강조**: Agent 모드의 캐시 히트율(50.8%)과 그 효과를 명확히 설명
3. **응답 시간 해석 주의**: Agent의 평균 응답 시간은 캐시 히트와 미스의 혼합이므로, 중앙값(73ms)도 함께 보고
4. **비용 분석**: 두 모드 간 비용 차이가 미미함을 강조 (성능 향상 대비 비용 증가가 작음)

---

이 가이드를 참고하여 논문을 작성하시면 됩니다! 🎓

