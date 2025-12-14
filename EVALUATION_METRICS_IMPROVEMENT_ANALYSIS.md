# 평가 지표 구현 개선 분석

## ChatGPT 제안 vs 현재 구현 비교

### 1. 구조적 차이

| 항목 | ChatGPT 제안 | 현재 구현 | 개선 필요 |
|------|-------------|----------|----------|
| **평가 방식** | 후처리(post-hoc) - events.jsonl 읽기 | 실시간 통합 - 실험 러너에 직접 통합 | ✅ 하이브리드 권장 |
| **파일 구조** | `evaluation/mt_eval/` 모듈 분리 | `experiments/evaluation/advanced_metrics.py` 단일 파일 | ⚠️ 선택적 (현재도 충분) |
| **무결성 보장** | 에이전트 로직과 완전 분리 | 실험 러너에 통합 (안전하지만 결합도 높음) | ✅ 후처리 옵션 추가 |

### 2. 기능적 차이

#### ✅ ChatGPT 제안의 장점

1. **ASS (Actionability/Specificity Score) 구현**
   - 현재 구현: ❌ 없음
   - ChatGPT: ✅ Turn 3/4에서 실행 가능성 측정
   - **개선 필요**: ASS 추가 구현

2. **SFS의 "환자-사실 주장" vs "예시" 구분**
   - 현재 구현: `_is_asserted()` 함수로 간단히 처리
   - ChatGPT: 더 정교한 패턴 매칭 + LLM Judge 옵션
   - **개선 필요**: 패턴 매칭 개선

3. **FHIR 파싱 로직**
   - 현재 구현: `synthea_slot_builder.py` 사용 (이미 구현됨)
   - ChatGPT: 독립적인 FHIR 파서 제안
   - **개선 필요**: 기존 구현 활용 (중복 방지)

4. **후처리 방식**
   - 현재 구현: 실시간 계산만
   - ChatGPT: 후처리 옵션 제공
   - **개선 필요**: 후처리 모듈 추가 (선택적)

#### ✅ 현재 구현의 장점

1. **실시간 계산**: 즉시 확인 가능
2. **통합성**: 실험 러너와 자연스럽게 통합
3. **기존 인프라 활용**: `synthea_slot_builder.py` 재사용

---

## 개선 사항 요약

### 필수 개선 (High Priority)

1. **ASS 지표 추가**
   - Turn 3: 운동 계획 요소 (frequency, intensity, duration, stop_criteria)
   - Turn 4: 식단 규칙 (3-5개 규칙, 모니터링 지표, 추적)
   - 현재: 구현 없음 → **추가 필요**

2. **SFS "환자-사실 주장" 판정 개선**
   - 현재: 간단한 예시 패턴 체크
   - 개선: 더 정교한 문맥 분석 (CLAIM_CUES 활용)
   - LLM Judge 옵션 추가 (선택적)

3. **후처리 모듈 추가**
   - `events.jsonl`을 읽어서 재계산하는 옵션
   - 실험 후 별도 평가 실행 가능
   - 무결성 보장 (에이전트 로직과 분리)

### 선택적 개선 (Medium Priority)

4. **FHIR 파싱 로직**
   - 현재: `synthea_slot_builder.py` 사용 (충분)
   - ChatGPT 제안: 독립 파서 (중복이므로 선택적)

5. **모듈 구조**
   - 현재: 단일 파일 (관리 용이)
   - ChatGPT: 모듈 분리 (확장성 높음)
   - 선택적: 필요시 리팩토링

---

## 개선 구현 계획

### Phase 1: ASS 지표 추가 (필수)

**파일**: `experiments/evaluation/advanced_metrics.py`

**추가 함수**:
```python
def compute_ass(
    self,
    answer: str,
    turn_id: int
) -> Dict[str, Any]:
    """
    ASS (Actionability/Specificity Score) 계산
    
    Turn 3: 운동 계획 요소 (frequency, intensity, duration, stop_criteria)
    Turn 4: 식단 규칙 (3-5개 규칙, 모니터링 지표, 추적)
    """
```

### Phase 2: SFS 개선 (필수)

**개선 사항**:
1. CLAIM_CUES 패턴 추가
2. "환자-사실 주장" 판정 로직 강화
3. LLM Judge 옵션 추가 (선택적)

### Phase 3: 후처리 모듈 추가 (권장)

**파일**: `experiments/evaluation/post_hoc_evaluator.py`

**기능**:
- `events.jsonl` 읽기
- 환자 truth 로드
- 평가 지표 재계산
- 결과 저장

---

## 결론

### 즉시 구현 필요

1. ✅ **ASS 지표 추가** - 현재 완전히 누락
2. ✅ **SFS 판정 로직 개선** - 오탐 방지
3. ✅ **후처리 모듈 추가** - 무결성 보장

### 선택적 개선

4. ⚠️ 모듈 구조 리팩토링 (현재도 충분)
5. ⚠️ FHIR 파서 독립화 (기존 구현 활용 권장)

**우선순위**: ASS > SFS 개선 > 후처리 모듈

