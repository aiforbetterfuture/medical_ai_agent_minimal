# 배치 파일 사용 가이드

이 프로젝트에는 Windows 환경에서 쉽게 사용할 수 있는 배치 파일들이 포함되어 있습니다.

## 배치 파일 목록

### 0_setup_env.bat
가상 환경을 생성하고 필요한 패키지를 설치합니다.

**사용법:**
```cmd
0_setup_env.bat
```

**기능:**
- Python 가상 환경(.venv) 생성
- pip 업그레이드
- requirements.txt에서 패키지 설치
- .env 파일 존재 여부 확인

### 1_check_keys.bat
.env 파일의 API 키들이 정상적으로 작동하는지 검증합니다.

**사용법:**
```cmd
1_check_keys.bat
```

**기능:**
- OPENAI_API_KEY 검증
- GOOGLE_API_KEY 검증 (선택적)
- MEDCAT2_MODEL_PATH 확인 (선택적)

### 2_run_api.bat
⚠️ **현재 미구현**: API 서버는 아직 구현되지 않았습니다.
이 프로젝트는 Streamlit UI만 지원합니다.

### 3_run_ui.bat
Streamlit 웹 UI를 실행합니다.

**사용법:**
```cmd
3_run_ui.bat
```

**기능:**
- 가상 환경 활성화
- Streamlit 앱 실행 (app.py)
- 기본 포트: 8501
- 브라우저에서 http://localhost:8501 접속

### 4_run_all.bat
Streamlit UI를 새 창에서 실행합니다.

**사용법:**
```cmd
4_run_all.bat
```

**기능:**
- Streamlit UI를 별도 창에서 실행
- 창을 닫으면 서비스 종료

## 사용 순서

1. **초기 설정** (최초 1회)
   ```cmd
   0_setup_env.bat
   ```

2. **API 키 확인** (선택적)
   ```cmd
   1_check_keys.bat
   ```

3. **UI 실행**
   ```cmd
   3_run_ui.bat
   ```
   또는
   ```cmd
   4_run_all.bat
   ```

## .env 파일 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 변수를 설정하세요:

```env
# 필수
OPENAI_API_KEY=your_openai_api_key

# 선택적
GOOGLE_API_KEY=your_google_api_key
MEDCAT2_MODEL_PATH=path/to/medcat2/model.pack
```

## 문제 해결

### 가상 환경이 없다는 오류
→ `0_setup_env.bat`를 먼저 실행하세요.

### API 키 오류
→ `1_check_keys.bat`를 실행하여 API 키를 확인하세요.

### Streamlit 실행 오류
→ 가상 환경이 활성화되어 있는지 확인하세요.
→ `python-dotenv` 패키지가 설치되어 있는지 확인하세요.

## 참고

- 모든 배치 파일은 프로젝트 루트 디렉토리에서 실행해야 합니다.
- 가상 환경은 `.venv` 폴더에 생성됩니다.
- Streamlit UI는 기본적으로 포트 8501에서 실행됩니다.

