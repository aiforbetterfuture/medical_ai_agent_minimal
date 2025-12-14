# Synthea 환자 데이터 정보 구성 분석 보고서

## 개요
Synthea로 생성된 환자 데이터에서 5명을 무작위로 선택하여 상세 정보를 분석한 결과입니다.

---

## 주요 발견 사항

### ✅ 포함된 정보

#### 1. 기본 인구통계 정보
- **이름**: 성명 (예: Delaine470 Osinski784)
- **성별**: male/female
- **생년월일**: YYYY-MM-DD 형식
- **나이**: 계산된 나이
- **혼인 상태**: Married, Divorced 등
- **출생 시 성별**: M/F
- **어머니 결혼 전 성**: (일부 환자)
- **주소**: 상세 주소 정보

#### 2. 질환 정보 (Condition)
- 질환명 (SNOMED 코드 기반)
- 발병일 (onset date)
- 임상 상태 (clinical status)
- 심각도 (severity)
- 질환 카테고리

**예시 질환들:**
- 당뇨병 관련: Prediabetes, Type 2 Diabetes Mellitus
- 심혈관: Essential hypertension, Ischemic heart disease, Hyperlipidemia
- 정신건강: Stress, Depression, Anxiety
- 사회적 상황: Full-time employment, Part-time employment, Unemployed, Social isolation
- 기타: Anemia, Obesity, Gingivitis, Chronic sinusitis 등

#### 3. 처방약 정보 (MedicationRequest)
- 약물명 (RxNorm 코드 기반)
- 용법 (dosage instructions)
- 상태 (active, completed)
- 처방일 (authoredOn)

**예시 약물들:**
- Simvastatin (콜레스테롤)
- Lisinopril, Hydrochlorothiazide (고혈압)
- Insulin (당뇨)
- Clopidogrel (혈전 예방)
- Metoprolol (심장)
- 진통제, 항생제 등

#### 4. 알레르기 정보 (AllergyIntolerance)
- 알레르기 원인 물질
- 심각도 (criticality)
- 반응 (reaction)
- 상태 (active/inactive)

**참고**: 분석한 5명 중 알레르기 정보가 있는 환자는 없었습니다.

#### 5. 시술/수술 정보 (Procedure)
- 시술명
- 시행일
- 시술 부위
- 합병증 정보

**예시 시술들:**
- Depression screening
- Assessment of health and social care needs
- Dental procedures
- Medication reconciliation
- Screening for domestic abuse 등

#### 6. 바이탈 사인 (Observation - Vitals)
- 신장 (Body Height)
- 체중 (Body Weight)
- BMI
- 혈압 (Blood pressure)
- 심박수 (Heart rate)
- 호흡수 (Respiratory rate)
- 측정일

#### 7. 검사 결과 (Observation - Labs)
- 혈당 (Glucose)
- HbA1c
- 크레아티닌 (Creatinine)
- 콜레스테롤 (Cholesterol, LDL, HDL)
- 헤모글로빈 (Hemoglobin)
- 검사일

#### 8. 진료 기록 (Encounter)
- 진료 유형 (AMB, IMP 등)
- 진료 종류
- 진료 기간 (시작일 ~ 종료일)
- 진단 정보

#### 9. 예방접종 (Immunization)
- 백신명
- 접종일
- 로트 번호
- 유효기간

**예시 백신:**
- Influenza (독감)
- COVID-19
- Td (파상풍)
- Pneumococcal (폐렴구균)

#### 10. 사회력 (Observation - Social History) ⭐
**흡연 상태:**
- Tobacco smoking status: Never smoked tobacco (대부분)
- 흡연 관련 정보는 있으나, 대부분 "Never smoked"로 기록됨

**⚠️ 부족한 사회력 정보:**
- **음주 습관**: 없음 (Alcohol Use Disorders Identification Test 점수는 있으나 구체적 음주량/빈도 없음)
- **운동량**: 없음
- **직업**: Condition으로 "Full-time employment", "Part-time employment", "Unemployed" 등은 있으나 구체적 직업명 없음
- **식습관**: 없음 (식이 관련 정보 없음)

#### 11. 가족력 (FamilyMemberHistory)
- 가족 관계
- 가족 구성원의 질환 정보
- 사망 여부

**참고**: 분석한 5명 중 가족력 정보가 있는 환자는 없었습니다.

#### 12. 치료 계획 (CarePlan)
- 치료 계획 설명
- 상태 (active, completed)

#### 13. 진단 보고서 (DiagnosticReport)
- 보고서 유형
- 검사 결과
- 결론

#### 14. 기타 관찰 (Observation - Other)
- 통증 점수 (Pain severity)
- 혈액 화학 검사 (Urea nitrogen, Calcium, Sodium, Potassium 등)
- 정신건강 평가 점수 (PHQ-2, AUDIT-C 등)
- PRAPARE (사회적 요인 평가)

---

## ❌ 포함되지 않은 정보

다음 정보들은 **현재 Synthea 데이터에 포함되어 있지 않습니다**:

1. **구체적 직업명**: 직업 유무만 있고 구체적 직업명 없음
2. **운동량/운동 습관**: 운동 관련 정보 없음
3. **식습관/식이 정보**: 식사 습관, 식이 제한 등 없음
4. **음주 상세 정보**: AUDIT-C 점수만 있고 구체적 음주량/빈도 없음
5. **가족력**: 대부분의 환자에서 가족력 정보 없음
6. **알레르기**: 대부분의 환자에서 알레르기 정보 없음

---

## 데이터 통계 (5명 환자 평균)

| 항목 | 평균 개수 |
|------|----------|
| 질환 (Condition) | 45개 |
| 처방약 (MedicationRequest) | 50개 |
| 시술/수술 (Procedure) | 150개 |
| 바이탈 사인 | 80개 |
| 검사 결과 | 100개 |
| 진료 기록 (Encounter) | 45개 |
| 예방접종 | 14개 |
| 사회력 (흡연) | 10개 |
| 가족력 | 0개 (대부분 없음) |
| 알레르기 | 0개 (대부분 없음) |

---

## 결론

### ✅ 강점
1. **의료 정보가 매우 풍부함**: 질환, 약물, 시술, 검사 결과 등이 상세히 기록됨
2. **시간적 추적 가능**: 대부분의 정보에 날짜가 기록되어 시간에 따른 변화 추적 가능
3. **다양한 리소스 타입**: FHIR 표준에 따라 체계적으로 구성됨

### ⚠️ 개선 필요 사항
1. **사회력 정보 부족**: 
   - 흡연 정보는 있으나 대부분 "Never smoked"
   - 음주, 운동, 식습관 정보 없음
   - 직업은 유무만 있고 구체적 직업명 없음

2. **가족력 정보 부족**: 대부분의 환자에서 가족력 정보 없음

3. **알레르기 정보 부족**: 대부분의 환자에서 알레르기 정보 없음

### 💡 권장 사항
의료 AI 에이전트 실험을 위해서는:
- 현재 데이터로도 기본적인 의료 대화 시뮬레이션은 가능
- 사회력, 가족력, 알레르기 정보가 필요한 경우, 추가로 생성하거나 보완 필요
- 식습관, 운동량 등 생활습관 정보는 별도로 생성/추가 필요

---

## 상세 보고서
전체 5명의 환자 상세 정보는 `patient_details_report.txt` 파일에 저장되어 있습니다.

