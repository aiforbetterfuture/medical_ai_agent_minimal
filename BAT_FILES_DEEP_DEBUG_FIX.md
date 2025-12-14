# Bat 파일 심층 디버깅 및 해결

## 문제 분석

7, 8번 파일이 여전히 실행되지 않는 근본 원인을 찾기 위해 더 깊이 파고들었습니다.

### 발견된 추가 문제점

1. **Python 스크립트 import 실패 가능성**
   - Python 스크립트가 import 단계에서 실패하면 즉시 종료
   - 에러 메시지가 출력되지 않을 수 있음

2. **stderr 출력 누락**
   - Python 스크립트의 에러 메시지가 stderr로 출력되는데 캡처하지 않음
   - `2>&1`을 추가하여 stderr도 함께 출력해야 함

3. **예외 처리 부족**
   - Python 스크립트에서 예외가 발생해도 적절히 처리되지 않을 수 있음
   - `main()` 함수에 try-except 추가 필요

## 적용된 해결책

### 1. Import 테스트 추가

Python 스크립트 실행 전에 import가 성공하는지 확인:

```bat
REM Python 스크립트 import 테스트
echo [디버그] Python 스크립트 import 테스트...
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, r'%CD%'); import experiments.run_multiturn_experiment_v2; print('[확인] Import 성공')" 2>&1
set IMPORT_EXIT=%errorlevel%
if not %IMPORT_EXIT% equ 0 (
    echo.
    echo [오류] Python 스크립트 import 실패!
    echo 상세 에러:
    .venv\Scripts\python.exe -c "import sys; sys.path.insert(0, r'%CD%'); import experiments.run_multiturn_experiment_v2" 2>&1
    pause
    exit /b 1
)
```

### 2. stderr 출력 캡처

Python 스크립트 실행 시 stderr도 함께 출력:

```bat
.venv\Scripts\python.exe experiments\run_multiturn_experiment_v2.py ^
    --config experiments\config.yaml ^
    --max-patients 1 ^
    --max-turns 1 2>&1
```

`2>&1`은 stderr를 stdout으로 리다이렉트하여 모든 출력을 볼 수 있게 합니다.

### 3. Python 스크립트 예외 처리 강화

`run_multiturn_experiment_v2.py`의 `main()` 함수에 예외 처리 추가:

```python
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[중단] 사용자에 의해 실험이 중단되었습니다.")
        sys.exit(130)
    except Exception as e:
        import traceback
        print(f"\n[치명적 오류] 실험 실행 중 예외 발생:")
        print(f"  에러 타입: {type(e).__name__}")
        print(f"  에러 메시지: {e}")
        print(f"\n상세 스택 트레이스:")
        traceback.print_exc()
        sys.exit(1)
```

## 디버깅 단계

### 1단계: Import 테스트

7, 8번 파일을 실행하면 먼저 import 테스트가 실행됩니다:

```
[디버그] Python 스크립트 import 테스트...
[확인] Import 성공
```

만약 import가 실패하면:
```
[오류] Python 스크립트 import 실패!
상세 에러:
(에러 메시지 출력)
```

### 2단계: 실제 실행

Import가 성공하면 실제 스크립트가 실행됩니다:

```
[실행 중] Python 스크립트를 실행합니다...

(Python 스크립트 출력)
```

### 3단계: 종료 코드 확인

```
[디버그] Python 종료 코드: 0
```

## 예상되는 에러 시나리오

### 시나리오 1: Import 실패

**증상**: Import 테스트에서 실패

**가능한 원인**:
- 필수 모듈이 설치되지 않음
- 경로 문제
- Python 버전 호환성 문제

**해결책**:
- `0_setup_env.bat` 실행
- `requirements.txt` 재설치
- Python 버전 확인

### 시나리오 2: 실행 중 예외 발생

**증상**: Import는 성공하지만 실행 중 에러

**가능한 원인**:
- API 키 없음
- 설정 파일 오류
- 데이터 파일 없음

**해결책**:
- `1_check_keys.bat` 실행
- `6_check_data_integrity.bat` 실행
- 설정 파일 확인

### 시나리오 3: 즉시 종료 (종료 코드 0)

**증상**: 스크립트가 실행되지만 즉시 종료되고 종료 코드가 0

**가능한 원인**:
- `main()` 함수가 실행되지 않음
- `if __name__ == "__main__"` 블록이 실행되지 않음

**해결책**:
- Python 스크립트의 `main()` 함수 확인
- 스크립트가 직접 실행되는지 확인

## 테스트 방법

### 1. Import 테스트만 실행

```bat
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, r'%CD%'); import experiments.run_multiturn_experiment_v2; print('Import 성공')"
```

### 2. Help 확인

```bat
.venv\Scripts\python.exe experiments\run_multiturn_experiment_v2.py --help
```

### 3. 전체 디버그 테스트

```bat
test_python_script.bat
```

## 결론

**근본 원인**: 
1. Python 스크립트 import 실패 시 에러 메시지가 보이지 않음
2. stderr 출력이 캡처되지 않음
3. 예외 처리 부족

**해결책**:
1. ✅ Import 테스트 추가
2. ✅ stderr 출력 캡처 (`2>&1`)
3. ✅ Python 스크립트 예외 처리 강화

이제 7, 8번 파일이 실행되면:
- Import 실패 시 명확한 에러 메시지 출력
- 실행 중 에러 발생 시 상세한 스택 트레이스 출력
- 모든 출력(stderr 포함)이 화면에 표시됨

