# 멀티턴 테스트 문제 해결 가이드

## 🔍 발생한 문제들

### 1. ❌ Google Gemini API 할당량 초과

**에러 메시지**:
```
429 You exceeded your current quota
Quota exceeded for metric: generate_content_free_tier_input_token_count, limit: 0
```

**원인**: Gemini Free Tier 일일/분당 할당량 소진

**해결**: ✅ OpenAI로 전환 완료

### 2. ❌ 한글 깨짐 현상

**원인**: Windows 콘솔 기본 인코딩 (CP949 vs UTF-8)

**해결**: ✅ UTF-8 인코딩 설정 추가

### 3. ❌ 검색 실패 (에러 메시지 불명확)

**에러 메시지**:
```
[ERROR] 검색 실패:
```

**원인**: `query_vector`가 `None`일 때 FAISS 검색 실패

**해결**: ✅ 에러 메시지 개선 및 None 체크 추가

---

## ✅ 적용된 수정사항

### 1. API 제공자 변경: Gemini → OpenAI

#### 파일: `experiments/config.yaml`
```yaml
llm:
  provider: "openai"  # 변경: gemini → openai
  model: "gpt-4o-mini"
  
agent:
  provider: "openai"
  model: "gpt-4o-mini"
```

#### 파일: `config/model_config.yaml`
```yaml
llm:
  provider: openai  # 변경: gemini → openai
  model: gpt-4o-mini
  llm_fallback:
    provider: gemini  # Fallback으로 변경
    model: gemini-2.0-flash-exp
```

### 2. 한글 인코딩 수정

#### 파일: `experiments/run_multiturn_experiment_v2.py`
```python
# Windows 콘솔 인코딩 설정 추가
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
```

#### 파일: `scripts/generate_synthea_profiles.py`
```python
# 동일한 인코딩 설정 추가
```

### 3. 검색 실패 에러 메시지 개선

#### 파일: `retrieval/faiss_index.py`
```python
def search(self, query_vector: List[float], k: int = 10):
    if not HAS_FAISS or self.index is None:
        return []
    
    # None 체크 추가
    if query_vector is None:
        print("[ERROR] FAISS 검색 실패: query_vector가 None입니다 (임베딩 생성 실패)")
        return []
    
    try:
        # ... 검색 로직
    except Exception as e:
        print(f"[ERROR] FAISS 검색 실패: {e}")
        import traceback
        traceback.print_exc()  # 상세 에러 출력
        return []
```

---

## 🎯 수정 후 실행 방법

### 1. 환경 확인

```cmd
# API 키 확인
1_check_keys.bat
```

`.env` 파일에 `OPENAI_API_KEY`가 설정되어 있는지 확인하세요:
```env
OPENAI_API_KEY=sk-...
```

### 2. 실험 실행

```cmd
5_run_multiturn_test.bat
```

또는 수동 실행:

```cmd
.venv\Scripts\python.exe experiments\run_multiturn_experiment_v2.py ^
    --config experiments\config.yaml ^
    --max-patients 78 ^
    --max-turns 5
```

---

## 📊 예상 결과

### OpenAI (GPT-4o-mini) 기준

- **환자 수**: 78명
- **턴 수**: 5턴
- **모드**: 2가지 (LLM, AI Agent)
- **총 API 호출**: 780회
- **예상 시간**: 2-3시간
- **예상 비용**: $3-8

### 비용 계산

```
GPT-4o-mini 요금:
- Input: $0.150 / 1M tokens
- Output: $0.600 / 1M tokens

예상 토큰 사용량 (턴당):
- Input: ~1,500 tokens
- Output: ~500 tokens

총 비용:
= 780 turns × (1,500 × 0.150 + 500 × 0.600) / 1,000,000
= 780 × (0.000225 + 0.0003)
= 780 × 0.000525
= $0.41 × 10 (안전 여유)
= ~$4-8
```

---

## ⚠️ 주의사항

### 1. API 할당량 관리

**OpenAI 할당량**:
- Tier 1 (Free): 3 RPM, 200 RPD
- Tier 2 ($5+): 500 RPM, 10,000 RPD

**권장**: 최소 Tier 2 이상 (유료 결제 필요)

### 2. 실행 중 오류 발생 시

```cmd
# 로그 확인
type runs\2025-12-13_primary_v1\events.jsonl | findstr "error"

# 마지막 이벤트 확인
powershell "Get-Content runs\2025-12-13_primary_v1\events.jsonl -Tail 5"
```

### 3. 중단 및 재개

실험이 중단된 경우:
- 기존 `events.jsonl`은 유효
- 재실행 시 처음부터 다시 시작 (중복 방지 로직 없음)
- 부분 결과 분석 가능

---

## 🐛 추가 문제 해결

### Q1: "OPENAI_API_KEY가 설정되지 않았습니다"

```cmd
# .env 파일 확인
type .env

# API 키 설정
echo OPENAI_API_KEY=sk-... >> .env
```

### Q2: "임베딩 생성 실패"

OpenAI 임베딩 API 호출 실패:
- API 키 확인
- 할당량 확인
- 네트워크 연결 확인

### Q3: "검색 실패: query_vector가 None입니다"

임베딩 생성이 실패한 경우:
1. OpenAI API 키 확인
2. `config/model_config.yaml`에서 임베딩 모델 확인
3. 네트워크 연결 확인

### Q4: 한글이 여전히 깨짐

PowerShell에서 직접 실행:
```powershell
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
.\5_run_multiturn_test.bat
```

---

## 📝 변경 이력

### 2025-12-13 19:30
- **문제**: Gemini API 할당량 초과
- **해결**: OpenAI로 전환
- **영향**: 모든 LLM 호출이 OpenAI로 변경

### 2025-12-13 19:35
- **문제**: 한글 깨짐 (CP949 인코딩)
- **해결**: UTF-8 인코딩 설정 추가
- **영향**: 콘솔 출력 정상화

### 2025-12-13 19:40
- **문제**: 검색 실패 에러 메시지 불명확
- **해결**: None 체크 및 상세 에러 출력
- **영향**: 디버깅 용이성 향상

---

## ✅ 최종 체크리스트

실험 실행 전 확인:

- [ ] `.env` 파일에 `OPENAI_API_KEY` 설정
- [ ] OpenAI 계정 유료 결제 (Tier 2 이상 권장)
- [ ] 환자 데이터 78개 확인 (`data/patients/profile_cards/`)
- [ ] 질문 뱅크 75개 확인 (`experiments/question_bank/`)
- [ ] 디스크 공간 최소 1GB 확보
- [ ] 네트워크 연결 안정성 확인

모든 항목 확인 후:

```cmd
5_run_multiturn_test.bat
```

---

**문서 작성**: 2025-12-13  
**마지막 업데이트**: 2025-12-13 19:45

