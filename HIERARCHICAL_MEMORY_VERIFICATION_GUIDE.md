# 계층형 메모리 검증 가이드

## 개요

3-Tier 계층형 메모리 시스템의 검증 시스템입니다.

### 검증 대상

1. **Tier 1 (Working Memory)**: 최근 5턴 원본 저장 확인
2. **Tier 2 (Compressed Memory)**: 5턴 도달 시 의학적 요약 확인
3. **Tier 3 (Semantic Memory)**: 만성질환/알레르기 저장 확인

---

## 검증 항목 상세

### Tier 1: Working Memory 검증

**검증 항목**:
- ✅ 최근 5턴이 모두 저장되어 있는가?
- ✅ 원본 형태로 저장되어 있는가? (user_query, agent_response 원문 유지)
- ✅ 턴 ID가 순차적으로 저장되어 있는가?

**검증 기준**:
- `working_memory_size >= 5` (5턴 도달 시)
- 모든 턴의 `user_query`와 `agent_response`가 비어있지 않음
- 턴 ID가 순차적 (예: [0, 1, 2, 3, 4])

---

### Tier 2: Compressed Memory 검증

**검증 항목**:
- ✅ 5턴 도달 시 압축이 트리거되었는가?
- ✅ 요약이 의학적으로 의미 있는가? (의학 키워드 포함 여부)
- ✅ 핵심 의학 정보가 보존되었는가?

**검증 기준**:
- `compression_triggered = True` (5턴 도달 시)
- `compression_quality >= 0.5` (의학 키워드 포함 여부)
- `medical_info_preserved = True` (conditions, medications, symptoms 중 하나 이상 포함)

---

### Tier 3: Semantic Memory 검증

**검증 항목**:
- ✅ 만성 질환이 저장되었는가?
- ✅ 만성 약물이 저장되었는가?
- ✅ 알레르기가 저장되었는가?
- ✅ 예상된 만성 질환이 포함되어 있는가?

**검증 기준**:
- `chronic_conditions_count > 0` 또는
- `chronic_medications_count > 0` 또는
- `allergies_count > 0`
- 예상된 만성 질환이 모두 포함되어 있음

---

## 사용 방법

### 1. 메모리 검증 활성화

`experiments/config.yaml`에서 메모리 검증 활성화:

```yaml
evaluation:
  memory_verification_enabled: true  # 계층형 메모리 검증 활성화
```

### 2. 멀티턴 실험 실행

메모리 검증을 포함한 멀티턴 실험 실행:

```bash
9_run_full_experiment.bat
```

또는 Python 스크립트:

```bash
python experiments/run_multiturn_experiment_v2.py --config experiments/config.yaml
```

### 3. 검증 결과 확인

검증 결과는 `events.jsonl`의 각 이벤트에 `memory_verification` 필드로 저장됩니다.

검증 결과 분석:

```bash
11_test_memory_verification.bat
```

또는 Python 스크립트:

```bash
python experiments/test_memory_verification.py --events runs/2025-12-13_primary_v1/events.jsonl
```

### 4. 메모리 소모량 계산

80명 x 5턴 시나리오에서 메모리/토큰/캐시 소모량 계산:

```bash
12_calculate_memory_consumption.bat
```

또는 Python 스크립트:

```bash
python experiments/calculate_memory_consumption.py
```

---

## 결과 파일

### 1. events.jsonl

각 이벤트에 `memory_verification` 필드가 추가됩니다:

```json
{
  "memory_verification": {
    "patient_id": "patient_001",
    "turn_id": 5,
    "tier1_working_memory": {
      "verified": true,
      "size": 5,
      "turns": [0, 1, 2, 3, 4],
      "originality": true
    },
    "tier2_compressed_memory": {
      "verified": true,
      "count": 1,
      "compression_triggered": true,
      "quality": 0.8,
      "medical_info_preserved": true
    },
    "tier3_semantic_memory": {
      "verified": true,
      "chronic_conditions_count": 2,
      "chronic_medications_count": 1,
      "allergies_count": 0,
      "updated": true
    },
    "overall": {
      "all_tiers_verified": true,
      "errors": []
    }
  }
}
```

### 2. memory_verification.json

전체 검증 결과 요약:

```json
{
  "verification_timestamp": "2025-12-14T10:00:00",
  "total_verifications": 400,
  "results": [...]
}
```

### 3. memory_verification_analysis.json

검증 결과 분석:

```json
{
  "verification_results": [...],
  "analysis": {
    "total_verifications": 400,
    "tier1_working_memory": {
      "verified_count": 380,
      "verified_rate": 0.95
    },
    "tier2_compressed_memory": {
      "verified_count": 320,
      "verified_rate": 0.80
    },
    "tier3_semantic_memory": {
      "verified_count": 350,
      "verified_rate": 0.875
    }
  }
}
```

### 4. memory_consumption_report.json

메모리 소모량 리포트:

```json
{
  "scenario": {
    "num_patients": 80,
    "num_turns": 5,
    "num_sessions": 80
  },
  "memory_consumption": {
    "total_memory_mb": 12.5
  },
  "token_consumption": {
    "total_tokens": 160000
  },
  "cost_estimation": {
    "total_llm_cost_usd": 0.024
  }
}
```

---

## 메모리 소모량 계산 결과 (예상)

### 시나리오: 80명 x 5턴 (AI Agent 모드만)

**메모리 소모량**:
- 작업 메모리 (Tier 1): ~10 MB
- 압축 메모리 (Tier 2): ~2 MB
- 의미 메모리 (Tier 3): ~0.5 MB
- **총 메모리**: ~12.5 MB

**토큰 소모량** (압축 시 LLM 호출):
- 압축 호출 횟수: 80회 (5턴당 1회)
- 압축당 토큰: ~2,000 토큰
- **총 토큰**: ~160,000 토큰 (0.16M)

**비용 추정** (OpenAI GPT-4o-mini):
- 입력 비용: $0.024
- 출력 비용: $0.096
- **총 비용**: ~$0.12

**세션당 소모량**:
- 메모리: ~0.16 MB
- 토큰: ~2,000 토큰
- 비용: ~$0.0015

---

## 주의사항

1. **메모리 검증은 Agent 모드에서만 수행됩니다**
   - LLM 모드에서는 계층형 메모리를 사용하지 않음

2. **hierarchical_memory_enabled가 true여야 합니다**
   - `config.yaml`의 `features.hierarchical_memory_enabled` 확인

3. **5턴 이상 실행되어야 Tier 2 검증 가능**
   - 5턴 도달 시 압축이 트리거됨

4. **프로필 카드에 만성 질환 정보가 있어야 Tier 3 검증 가능**
   - 예상 만성 질환 비교를 위해 필요

---

## 문제 해결

### 검증 결과가 없는 경우

1. `memory_verification_enabled`가 `true`인지 확인
2. `hierarchical_memory_enabled`가 `true`인지 확인
3. Agent 모드로 실행되었는지 확인
4. `events.jsonl`에 `memory_verification` 필드가 있는지 확인

### Tier 1 검증 실패

- 작업 메모리 크기가 5턴 미만인 경우
- 턴 ID가 순차적이지 않은 경우
- 원본이 손상된 경우 (user_query 또는 agent_response가 비어있음)

### Tier 2 검증 실패

- 5턴 도달 시 압축이 트리거되지 않은 경우
- 요약 품질이 낮은 경우 (의학 키워드 부족)
- 핵심 의학 정보가 보존되지 않은 경우

### Tier 3 검증 실패

- 만성 질환/약물/알레르기가 저장되지 않은 경우
- 예상된 만성 질환이 누락된 경우

---

## 참고

- `memory/hierarchical_memory.py`: 계층형 메모리 시스템 구현
- `experiments/evaluation/memory_verification.py`: 메모리 검증 모듈
- `experiments/calculate_memory_consumption.py`: 메모리 소모량 계산
- `experiments/test_memory_verification.py`: 검증 결과 분석

