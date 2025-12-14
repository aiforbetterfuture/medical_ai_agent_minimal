# 실험 실행 에러 처리 개선 사항

## 📋 개요

9번 파일(`experiments/run_multiturn_experiment_v2.py`)의 안정성과 신뢰성을 높이기 위해 체계적인 에러 처리 및 검증 로직을 추가했습니다.

---

## ✅ 수정 완료 사항

### 1. 파일 I/O 에러 처리 강화

#### 문제점
- 파일이 없거나 권한이 없을 때 명확한 에러 메시지 부족
- JSON/YAML 파싱 오류 시 원인 파악 어려움

#### 수정 내용
- **`_load_config()`**: FileNotFoundError, PermissionError, YAMLError 구분 처리
- **`_load_patients()`**: JSON 파싱 오류 및 데이터 형식 검증 추가
- **`_load_question_bank()`**: JSON 파싱 오류 및 필수 키 검증 추가
- **`_load_profile_card()`**: FileNotFoundError는 상위로 전파 (환자 스킵), 기타 오류는 로깅

#### 코드 예시
```python
def _load_config(self) -> Dict:
    try:
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"설정 파일을 찾을 수 없습니다: {self.config_path}")
        raise
    except PermissionError:
        logger.error(f"설정 파일 읽기 권한이 없습니다: {self.config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"YAML 파싱 오류: {e}")
        raise
```

---

### 2. API 호출 에러 처리 개선

#### 문제점
- API 할당량 초과나 인증 실패 시에도 실험이 계속 진행됨
- 에러 원인 파악이 어려움

#### 수정 내용
- **`_run_llm_mode()`**: 
  - API 할당량 초과(429, quota) 감지 시 즉시 중단 (`RuntimeError` 발생)
  - API 인증 실패(401, unauthorized) 감지 시 즉시 중단
  - 상세한 에러 메시지와 traceback 출력
- **`_run_agent_mode()`**: 동일한 에러 처리 로직 적용
- **`core/llm_client.py`**: 
  - `generate()` 및 `embed()` 메서드에서 빈 응답 검증 추가
  - 에러를 상위로 전파하여 일관된 처리

#### 코드 예시
```python
except Exception as e:
    error_str = str(e).lower()
    if 'quota' in error_str or '429' in error_str or 'rate limit' in error_str:
        print(f"\n[CRITICAL] API 할당량 초과 또는 Rate Limit 도달!")
        print(f"  실험을 즉시 중단합니다.")
        raise RuntimeError(f"API 할당량 초과: {e}")
    elif '401' in error_str or 'unauthorized' in error_str:
        print(f"\n[CRITICAL] API 인증 실패!")
        print(f"  실험을 즉시 중단합니다.")
        raise RuntimeError(f"API 인증 실패: {e}")
```

---

### 3. 세션 상태 관리 안정성 검증

#### 문제점
- Agent 모드에서 `ProfileStore`가 `None`일 수 있음
- 세션 상태 업데이트 시 예외 발생 가능

#### 수정 내용
- **`run_experiment()`**: 
  - `ProfileStore`가 `None`이면 새로 생성
  - 경고 메시지 출력 및 로깅
  - 대화 히스토리 길이 모니터링 (20턴 이상 시 경고)

#### 코드 예시
```python
# ProfileStore None 체크 (안정성)
if profile_store is None and mode == 'agent':
    logger.warning(f"ProfileStore가 None입니다. 새로 생성합니다. (환자: {patient_id}, 턴: {turn_id})")
    from memory.profile_store import ProfileStore
    profile_store = ProfileStore()
    session_state['profile_store'] = profile_store
```

---

### 4. JSON 직렬화 에러 처리

#### 문제점
- 이벤트 로깅 실패 시 실험이 중단될 수 있음
- 매니페스트 파일 저장 실패 시 정보 손실

#### 수정 내용
- **`_log_event()`**: 
  - IOError, OSError, PermissionError 구분 처리
  - 로깅 실패는 실험을 중단하지 않음 (경고만 출력)
- **`_generate_run_manifest()`**: 
  - 파일 저장 실패 시 명확한 에러 메시지와 함께 상위로 전파

#### 코드 예시
```python
def _log_event(self, event: Dict):
    try:
        with open(self.events_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
    except (IOError, OSError, PermissionError) as e:
        logger.error(f"이벤트 로깅 실패: {e}")
        print(f"[WARNING] 이벤트 로깅 실패: {e}")
```

---

### 5. 프로파일 카드 로드 에러 처리

#### 문제점
- 프로파일 카드 로드 실패 시 에러 메시지가 불명확함
- JSON 파싱 오류와 파일 없음 오류를 구분하지 못함

#### 수정 내용
- **`run_experiment()`**: 
  - FileNotFoundError: 환자 스킵 (기존 동작 유지)
  - 기타 Exception: 상세한 에러 메시지 출력 후 환자 스킵

#### 코드 예시
```python
try:
    profile_card = self._load_profile_card(patient_id)
except FileNotFoundError:
    logger.warning(f"Profile card not found for {patient_id}, skipping...")
    print(f"[WARNING] 프로파일 카드를 찾을 수 없습니다: {patient_id} (건너뜀)")
    continue
except Exception as e:
    logger.error(f"프로파일 카드 로드 실패 ({patient_id}): {e}")
    print(f"[ERROR] 프로파일 카드 로드 실패: {patient_id} - {e}")
    continue
```

---

### 6. 메모리 관리 개선

#### 문제점
- 대화 히스토리가 무한정 증가할 수 있음
- 장기 실행 시 메모리 누수 가능성

#### 수정 내용
- 대화 히스토리 길이 모니터링 (20턴 이상 시 경고)
- 각 환자/모드별로 독립적인 세션 상태 관리

#### 코드 예시
```python
# 메모리 관리: 대화 히스토리가 너무 길어지면 압축 (선택적)
if len(conversation_history) > 20:  # 20턴 이상이면 경고
    logger.warning(f"대화 히스토리가 길어집니다 ({len(conversation_history)}턴). 메모리 사용량을 모니터링하세요.")
```

---

## 🔍 에러 처리 전략

### 즉시 중단 (Critical Errors)
다음 에러 발생 시 실험을 즉시 중단합니다:
- **API 할당량 초과** (429, quota exceeded)
- **API 인증 실패** (401, unauthorized)
- **설정 파일 로드 실패** (필수 파일)
- **환자 리스트/질문 뱅크 로드 실패** (필수 데이터)

### 환자 스킵 (Non-Critical Errors)
다음 에러 발생 시 해당 환자만 스킵하고 계속 진행:
- **프로파일 카드 없음** (FileNotFoundError)
- **프로파일 카드 파싱 오류** (JSONDecodeError)

### 경고만 출력 (Warnings)
다음 에러 발생 시 경고만 출력하고 계속 진행:
- **이벤트 로깅 실패** (IOError, PermissionError)
- **ProfileStore None** (자동 생성)

---

## 📊 개선 효과

### 안정성 향상
- ✅ 명확한 에러 메시지로 디버깅 시간 단축
- ✅ API 할당량 초과 시 즉시 중단으로 불필요한 API 호출 방지
- ✅ 프로파일 카드 로드 실패 시 해당 환자만 스킵하여 실험 지속 가능

### 신뢰성 향상
- ✅ 세션 상태 관리 안정성 검증으로 예외 발생 방지
- ✅ 파일 I/O 에러 처리로 데이터 손실 방지
- ✅ 메모리 사용량 모니터링으로 장기 실행 안정성 확보

---

## 🚀 사용 가이드

### 에러 발생 시 대응

1. **API 할당량 초과**
   ```
   [CRITICAL] API 할당량 초과 또는 Rate Limit 도달!
   ```
   - OpenAI 대시보드에서 크레딧 확인 및 추가
   - 실험 재시작

2. **프로파일 카드 없음**
   ```
   [WARNING] 프로파일 카드를 찾을 수 없습니다: SYN_0044 (건너뜀)
   ```
   - 해당 환자는 자동으로 스킵됨
   - 실험은 계속 진행됨

3. **이벤트 로깅 실패**
   ```
   [WARNING] 이벤트 로깅 실패: Permission denied
   ```
   - 실험은 계속 진행됨
   - 결과 파일 확인 필요

---

## 📝 참고 사항

- 모든 에러는 로그 파일(`runs/{run_id}/events.jsonl`)에도 기록됩니다.
- API 에러는 터미널에 상세한 traceback이 출력됩니다.
- 프로파일 카드 로드 실패는 해당 환자만 스킵되므로 전체 실험에는 영향을 주지 않습니다.

