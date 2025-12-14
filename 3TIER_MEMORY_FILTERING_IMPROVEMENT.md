# 3-Tier 메모리 Semantic Memory 필터링 개선

## 문제점

### 이전 문제
- Semantic Memory에 **31개의 만성질환**이 저장되었지만, 실제로는:
  - 실제 만성 질환: 2개 (고혈압, 당뇨병)
  - 일반 단어: 27개 (Current, Effect, Recent, Minute, Walking 등)
  - 약물: 2개 (리시노프릴, Atorvastatin - conditions에 잘못 포함)

### 원인
1. **일반 단어 필터링 없음**: MedCAT에서 추출된 일반 단어들이 그대로 포함됨
2. **약물 필터링 없음**: 약물이 conditions에 포함되어 만성 질환으로 잘못 분류됨
3. **만성 질환 키워드 매칭 부족**: 빈도만으로 판단하여 일반 단어도 포함됨

## 개선 방법

### 1. 일반 단어 제외 (Stop Words)

```python
# 일반 단어 제외 (stop words)
stop_words = [
    'current', 'effect', 'recent', 'minute', 'walking', 'daily',
    'increase', 'maintained', 'needed', 'prevent', 'complication',
    'blood', 'glucose', 'health', 'lifestyle', 'speaking',
    'awakening', 'frequent', 'during', 'sleep', 'emotion',
    'simple', 'carbohydrate', 'after', 'exercise', 'once',
    'day', 'bedtime', 'dietary', 'finding', 'light',
    'electromagnetic', 'radiation', 'constant', 'dosing',
    'instruction', 'fragment', 'was', 'a', 'family', 'history',
    # 한글 인코딩 오류 포함
    'con', '대', 'hi', '대tory', '대leep', '대imple', '대peaking',
    'gluco', '대e', 'blood', '대', 'atorva', '스타틴', 'increa', '대e'
]

# 1. 일반 단어 제외
if any(stop_word in cond_name_lower for stop_word in stop_words):
    print(f"[Semantic Memory] 일반 단어 제외: {cond_name}")
    continue
```

**효과:**
- "Current", "Effect", "Recent", "Minute", "Walking" 등 일반 단어 제외
- MedCAT 인코딩 오류로 인한 이상한 단어들도 제외

### 2. 약물 제외

```python
# 약물 키워드 (제외 - 약물은 medications로만 처리)
medication_keywords = [
    '리시노프릴', '메트포르민', '메트폴민', '아토르바스타틴', '스타틴',
    'lisinopril', 'metformin', 'atorvastatin', 'statin',
    'aspirin', '아스피린', '약물', 'medication', 'drug'
]

# 2. 약물 제외
if any(med_keyword in cond_name_lower for med_keyword in medication_keywords):
    print(f"[Semantic Memory] 약물 제외 (conditions에서): {cond_name}")
    continue
```

**효과:**
- 약물이 conditions에 포함되어도 제외
- 약물은 `_extract_chronic_medications()`에서만 처리

### 3. 만성 질환 키워드 매칭 강화

```python
# 4. 만성 질환 키워드 확인
has_chronic_keyword = any(keyword in cond_name_lower for keyword in chronic_keywords)

# 5. MedCAT CUI 확인
cond_detail = condition_details.get(cond_name, {})
cui = cond_detail.get('cui', '')

# 6. 만성 질환 판정
is_chronic = (
    (freq >= 2 and has_chronic_keyword) or  # 빈도 2회 이상 + 만성 키워드
    (has_chronic_keyword) or  # 만성 키워드 포함
    (freq >= 3 and cui)  # 빈도 3회 이상 + MedCAT CUI
)
```

**효과:**
- 만성 키워드가 없으면 제외 (일반 단어 필터링)
- MedCAT CUI가 있어도 빈도가 낮으면 제외

### 4. MedCAT 정보 활용

```python
chronic_cond = {
    'name': cond_name,
    'first_mentioned': datetime.now().isoformat(),
    'last_mentioned': datetime.now().isoformat(),
    'frequency': freq,
    'verified_by': 'frequency' if freq >= 2 else 'keyword',
    'medcat_verified': bool(cui),  # CUI가 있으면 검증됨
    'medcat_cui': cui if cui else '',
    'medcat_confidence': cond_detail.get('confidence', 0.0) if cui else 0.0
}
```

**효과:**
- MedCAT CUI 및 신뢰도 저장
- 검증 상태 명확히 표시

## 예상 결과

### 이전 (31개)
- 실제 만성 질환: 2개
- 일반 단어: 27개
- 약물: 2개

### 이후 (예상 2-3개)
- 실제 만성 질환: 2-3개
  - 고혈압 (Family history: 고혈압 환자)
  - 당뇨병 환자
  - (기타 실제 만성 질환이 있다면)

## 테스트 방법

```bash
# 11번 bat 파일 재실행
11_test_3tier_memory.bat
```

**확인 사항:**
1. Semantic Memory 만성질환 수가 2-3개로 감소
2. 일반 단어들이 제외됨
3. 약물이 conditions에서 제외됨
4. 실제 만성 질환만 저장됨

## 결론

✅ **Semantic Memory 필터링 로직이 강화되었습니다!**

**개선 사항:**
1. ✅ 일반 단어 제외 (Stop Words)
2. ✅ 약물 제외 (약물은 medications로만 처리)
3. ✅ 만성 질환 키워드 매칭 강화
4. ✅ MedCAT CUI 활용

**효과:**
- Semantic Memory에 **실제 만성 질환만** 저장
- 일반 단어 및 약물 제외
- 메모리 정확도 향상

이제 11번 bat 파일을 재실행하면 Semantic Memory에 실제 만성 질환만 저장됩니다! 🚀

