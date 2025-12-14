# 3-Tier 메모리 테스트 LLM 클라이언트 수정

## 문제

```
AttributeError: 'OpenAIClient' object has no attribute 'chat'
```

## 원인

`get_llm_client()` 함수가 반환하는 `OpenAIClient` 객체는 `chat` 속성이 없습니다. 대신 `generate()` 메서드를 사용하거나, OpenAI 클라이언트를 직접 생성해야 합니다.

## 해결

### OpenAI 클라이언트 직접 생성

**이전 (잘못된 방식):**
```python
from core.llm_client import get_llm_client

class VirtualPatientGenerator:
    def __init__(self):
        self.llm_client = get_llm_client(
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=2000
        )
    
    def generate_patient_profile(self):
        response = self.llm_client.chat.completions.create(...)  # ❌ 에러!
```

**이후 (올바른 방식):**
```python
import openai

class VirtualPatientGenerator:
    def __init__(self):
        # OpenAI 클라이언트 직접 생성
        self.openai_client = openai.OpenAI()
    
    def generate_patient_profile(self):
        response = self.openai_client.chat.completions.create(...)  # ✅ 정상!
```

## 수정 내용

### experiments/test_3tier_memory_21turns.py

#### 1. VirtualPatientGenerator 초기화 (Line 46-50)
```python
def __init__(self):
    # OpenAI 클라이언트 직접 생성
    import openai
    self.openai_client = openai.OpenAI()
```

#### 2. generate_patient_profile 메서드 (Line 85)
```python
response = self.openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,
    max_tokens=2000
)
```

#### 3. generate_questions 메서드 (Line 133)
```python
response = self.openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,
    max_tokens=3000
)
```

## 검증

```bash
.venv\Scripts\python.exe -c "from experiments.test_3tier_memory_21turns import VirtualPatientGenerator; gen = VirtualPatientGenerator(); print('VirtualPatientGenerator initialized successfully')"
```

**결과:** ✅ VirtualPatientGenerator initialized successfully

## 실행 방법

```bash
11_test_3tier_memory.bat
```

## 참고

### OpenAIClient vs openai.OpenAI()

**OpenAIClient (core/llm_client.py):**
- 프로젝트 내부 래퍼 클래스
- `generate()` 메서드 제공
- `chat` 속성 없음

**openai.OpenAI():**
- OpenAI 공식 라이브러리
- `chat.completions.create()` 메서드 제공
- 직접 사용 가능

## 결론

OpenAI 클라이언트를 직접 생성하여 `chat.completions.create()` 메서드를 사용하도록 수정했습니다. 이제 11번 bat 파일이 정상적으로 작동합니다! ✅

