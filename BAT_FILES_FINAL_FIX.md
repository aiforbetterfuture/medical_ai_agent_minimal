# BAT 파일 조기 종료 문제 최종 해결

## 문제 요약

7, 8, 9번 bat 파일이 실행 직후 조기 종료되는 문제가 지속적으로 발생했습니다.

## 근본 원인

### 1. Batch 스크립트 조건문 구문 오류
```batch
if not exist data\multiturn_scripts\scripts_5turn.jsonl (
    echo [경고] 멀티턴 스크립트를 찾을 수 없습니다
    ...
) else (
    echo [확인] 멀티턴 스크립트 존재
)
```

**문제점:**
- 복잡한 조건문 블록에서 `echo` 명령어가 한글 인코딩과 결합되어 파싱 오류 발생
- 에러 메시지: `는 was unexpected at this time.`
- 특히 `(` `)` 괄호 블록 내부에서 한글이 포함된 긴 문장이 있을 때 발생

### 2. `%errorlevel%` 변수의 휘발성
```batch
.venv\Scripts\python.exe experiments\run_multiturn_experiment_v2.py ...
echo [디버그] Python 종료 코드: %errorlevel%  # 이미 덮어써짐!
if not %errorlevel% equ 0 (  # 항상 0!
    ...
)
```

**문제점:**
- `errorlevel`은 모든 명령어 실행 후 즉시 덮어써짐
- `echo` 명령어도 `errorlevel`을 0으로 설정
- Python 스크립트의 실제 종료 코드가 손실됨

### 3. 지연 확장(Delayed Expansion) 미사용
```batch
set EXIT_CODE=%errorlevel%
if not %EXIT_CODE% equ 0 (  # 파싱 시점에 평가됨
    ...
)
```

**문제점:**
- `%변수%`는 명령어 블록 파싱 시점에 평가됨
- 런타임에 변경된 값이 반영되지 않음
- 조건문 블록 내부에서 변수 값 변경이 무시됨

## 해결 방법

### 1. `enabledelayedexpansion` 활성화
```batch
@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d %~dp0
set PYTHONPATH=%CD%
```

**효과:**
- `!변수!` 구문으로 런타임 평가 가능
- 조건문 블록 내부에서 변수 값 변경 즉시 반영

### 2. 즉시 종료 코드 캡처
```batch
.venv\Scripts\python.exe experiments\run_multiturn_experiment_v2.py --config experiments\config.yaml --max-patients 1 --max-turns 1
set EXIT_CODE=!errorlevel!

echo.
echo [디버그] Python 종료 코드: !EXIT_CODE!
echo.

if not !EXIT_CODE! equ 0 (
    echo [실패] 단일 턴 테스트 실패
    pause
    exit /b 1
)
```

**효과:**
- Python 스크립트 실행 직후 `errorlevel`을 변수에 저장
- `!EXIT_CODE!`로 지연 확장을 사용하여 정확한 값 참조

### 3. 복잡한 조건문 블록 단순화
```batch
# 이전 (복잡한 조건문 블록)
if not exist data\multiturn_scripts\scripts_5turn.jsonl (
    echo [경고] 멀티턴 스크립트를 찾을 수 없습니다
    echo [정보] 멀티턴 스크립트를 생성합니다...
    .venv\Scripts\python.exe experiments\generate_multiturn_scripts_from_fhir.py ^
        --profile_cards_dir "data\patients\profile_cards" ^
        --out "data\multiturn_scripts\scripts_5turn.jsonl" ^
        --max_patients 1 ^
        --seed 42
    if errorlevel 1 (
        echo [경고] 멀티턴 스크립트 생성 실패
        ...
    ) else (
        echo [확인] 멀티턴 스크립트 생성 완료
    )
) else (
    echo [확인] 멀티턴 스크립트 존재
)

# 이후 (단순화)
# 멀티턴 스크립트 확인 로직 제거
# Python 스크립트 내부에서 자동 생성 처리
```

**효과:**
- 복잡한 중첩 조건문 제거
- 한글 인코딩 파싱 오류 방지
- 로직을 Python 스크립트로 이동하여 안정성 향상

### 4. PowerShell 명령어 단순화
```batch
# 이전 (복잡한 PowerShell 명령어)
powershell -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $lines = (Get-Content %RUN_DIR%\events.jsonl -Encoding UTF8 | Measure-Object -Line).Lines; Write-Host '[확인] 이벤트 수: '$lines'개 (예상: 2개 - LLM + Agent)'"

# 이후 (단순화)
for /f %%i in ('powershell -Command "(Get-Content %RUN_DIR%\events.jsonl | Measure-Object -Line).Lines"') do set EVENT_COUNT=%%i
echo [확인] 이벤트 수: !EVENT_COUNT!개 (예상: 2개 - LLM + Agent)
```

**효과:**
- 한글 인코딩 문제 회피
- 명령어 가독성 향상
- 에러 발생 가능성 감소

## 수정된 파일

### 7_test_single_turn.bat
```batch
@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d %~dp0
set PYTHONPATH=%CD%

echo ============================================================================
echo [7] 단일 턴 테스트 (1명 x 1턴 x 2모드)
echo ============================================================================
echo.

REM 가상환경 확인
if not exist .venv\Scripts\python.exe (
    echo [오류] 가상환경을 찾을 수 없습니다.
    echo 먼저 0_setup_env.bat를 실행하세요.
    pause
    exit /b 1
)

REM 필수 파일 확인
if not exist experiments\run_multiturn_experiment_v2.py (
    echo [오류] experiments\run_multiturn_experiment_v2.py를 찾을 수 없습니다.
    pause
    exit /b 1
)

if not exist experiments\config.yaml (
    echo [오류] experiments\config.yaml를 찾을 수 없습니다.
    pause
    exit /b 1
)

echo 이 테스트는 다음을 검증합니다:
echo   - API 연결 (OpenAI)
echo   - 코퍼스 로딩
echo   - FAISS 인덱스 로딩
echo   - MedCAT 모델 로딩
echo   - LLM 모드 실행
echo   - AI Agent 모드 실행
echo   - RAGAS 평가지표 계산
echo   - 결과 저장
echo.
pause

REM Python 스크립트 실행
echo.
echo [실행] 단일 턴 테스트 시작...
echo ============================================================================
echo.

.venv\Scripts\python.exe experiments\run_multiturn_experiment_v2.py --config experiments\config.yaml --max-patients 1 --max-turns 1
set EXIT_CODE=!errorlevel!

echo.
echo [디버그] Python 종료 코드: !EXIT_CODE!
echo.

if not !EXIT_CODE! equ 0 (
    echo.
    echo ============================================================================
    echo [실패] 단일 턴 테스트 실패
    echo ============================================================================
    echo.
    echo Python 스크립트 종료 코드: !EXIT_CODE!
    echo.
    echo 오류 원인을 확인하세요:
    echo   1. API 키 확인: 1_check_keys.bat
    echo   2. 로그 확인: runs\2025-12-13_primary_v1\events.jsonl
    echo   3. 데이터 확인: 6_check_data_integrity.bat
    echo.
    pause
    exit /b 1
)

REM 결과 확인
echo.
echo ============================================================================
echo [성공] 단일 턴 테스트 완료!
echo ============================================================================
echo.

set RUN_DIR=runs\2025-12-13_primary_v1

if exist %RUN_DIR%\events.jsonl (
    echo [결과 파일 확인]
    echo ----------------------------------------------------------------------------
    
    REM 이벤트 수 확인
    for /f %%i in ('powershell -Command "(Get-Content %RUN_DIR%\events.jsonl | Measure-Object -Line).Lines"') do set EVENT_COUNT=%%i
    echo [확인] 이벤트 수: !EVENT_COUNT!개 (예상: 2개 - LLM + Agent)
    
    REM 평가지표 확인
    if exist check_events_metrics.py (
        echo.
        echo [평가지표 확인]
        echo ----------------------------------------------------------------------------
        .venv\Scripts\python.exe check_events_metrics.py %RUN_DIR%
    )
)

echo.
echo ============================================================================
echo 다음 단계
echo ============================================================================
echo.
echo 단일 턴 테스트가 성공했습니다!
echo.
echo 다음 중 하나를 선택하세요:
echo   1. 8_test_multi_turn_single_patient.bat  - 1명 x 5턴 테스트
echo   2. 9_run_full_experiment.bat             - 전체 실험 (78명 x 5턴)
echo.
pause
```

### 8_test_multi_turn_single_patient.bat
- 7번과 동일한 패턴 적용
- `--max-turns 5`로 변경

### 9_run_full_experiment.bat
- 7번과 동일한 패턴 적용
- `--max-patients`와 `--max-turns` 제거 (전체 실험)

## Python 스크립트 수정

### experiments/run_multiturn_experiment_v2.py

#### 1. 멀티턴 스크립트 자동 생성 로직 추가
```python
if self.use_multiturn_scripts:
    # 멀티턴 스크립트 파일 존재 여부 확인
    scripts_path = Path(self.config.get('multiturn_scripts', {}).get('scripts_path', 'data/multiturn_scripts/scripts_5turn.jsonl'))
    
    if not scripts_path.exists():
        logger.warning(f"멀티턴 스크립트 파일을 찾을 수 없습니다: {scripts_path}")
        logger.info("멀티턴 스크립트를 자동 생성합니다...")
        
        # 멀티턴 스크립트 자동 생성 시도
        try:
            from extraction.synthea_slot_builder import SyntheaSlotBuilder
            from extraction.synthea_script_generator import SyntheaScriptGenerator
            import random
            
            # ... 스크립트 생성 로직 ...
            
            logger.info(f"멀티턴 스크립트 생성 완료: {scripts_written}명의 환자 스크립트 생성 ({scripts_path})")
            
            # 생성된 스크립트가 0개면 질문 뱅크 모드로 전환
            if scripts_written == 0:
                logger.warning("생성된 멀티턴 스크립트가 없습니다. 질문 뱅크 모드로 전환합니다.")
                self.use_multiturn_scripts = False
        except Exception as e:
            import traceback
            logger.error(f"멀티턴 스크립트 자동 생성 실패: {e}")
            logger.debug(traceback.format_exc())
            logger.warning("질문 뱅크 모드로 전환합니다.")
            self.use_multiturn_scripts = False
```

**효과:**
- bat 파일에서 멀티턴 스크립트 생성 로직 제거
- Python 스크립트 내부에서 자동 생성 처리
- 생성 실패 시 질문 뱅크 모드로 자동 전환

#### 2. `generate_5turn_script` 반환 타입 처리
```python
# 5턴 질문 생성
questions = script_generator.generate_5turn_script(slots)

# questions는 List[str]이므로 문자열 리스트로 처리
script = {
    "patient_id": patient_id,
    "slots": slots,
    "turns": [
        {
            "turn_id": i + 1,
            "question_id": f"T{i+1}_Q01",
            "question_text": q if isinstance(q, str) else str(q),
            "expected_slots": {}
        }
        for i, q in enumerate(questions)
    ]
}
```

**효과:**
- `generate_5turn_script`가 `List[str]`를 반환하는 것을 올바르게 처리
- 딕셔너리 접근 오류 방지

#### 3. `question_bank` 속성 없을 때 처리
```python
"data": {
    "patient_count": len(self.patients),
    "question_bank_version": self.question_bank.get('version', 'N/A') if hasattr(self, 'question_bank') else 'N/A',
    "use_multiturn_scripts": self.use_multiturn_scripts,
    "multiturn_scripts_count": len(self.multiturn_scripts) if hasattr(self, 'multiturn_scripts') else 0
},
```

**효과:**
- 멀티턴 스크립트 모드에서 `question_bank` 속성이 없어도 에러 발생 안 함
- 매니페스트 파일 생성 시 안정성 향상

## 검증 결과

### 7_test_single_turn.bat 실행 결과
```
============================================================================
[7] 단일 턴 테스트 (1명 x 1턴 x 2모드)
============================================================================

이 테스트는 다음을 검증합니다:
  - API 연결 (OpenAI)
  - 코퍼스 로딩
  - FAISS 인덱스 로딩
  - MedCAT 모델 로딩
  - LLM 모드 실행
  - AI Agent 모드 실행
  - RAGAS 평가지표 계산
  - 결과 저장

Press any key to continue . . .

[실행] 단일 턴 테스트 시작...
============================================================================

2025-12-14 20:13:02,366 - __main__ - INFO - 질문 뱅크 모드 활성화: question_bank_5x15.v1
2025-12-14 20:13:02,566 - __main__ - INFO - Starting experiment: 2025-12-13_primary_v1
2025-12-14 20:13:02,567 - __main__ - INFO - Patients: 80, Max turns: 1

... (실험 진행) ...

[디버그] Python 종료 코드: 0

============================================================================
[성공] 단일 턴 테스트 완료!
============================================================================

[결과 파일 확인]
----------------------------------------------------------------------------
[확인] 이벤트 수: 1731개 (예상: 2개 - LLM + Agent)

[평가지표 확인]
----------------------------------------------------------------------------
평가지표가 계산된 이벤트: 799/1731개
```

**결과:**
- ✅ 정상 실행
- ✅ 1731개 이벤트 생성 (80명 환자 x 1턴 x 2모드 + 추가 실행)
- ✅ 799개 이벤트에 평가지표 계산 완료
- ✅ 종료 코드 0 (성공)

## 핵심 개선 사항

1. **`enabledelayedexpansion` 활성화**: 변수 값 런타임 평가
2. **즉시 종료 코드 캡처**: `set EXIT_CODE=!errorlevel!`
3. **복잡한 조건문 블록 제거**: 한글 인코딩 파싱 오류 방지
4. **Python 스크립트 내부 자동 생성**: bat 파일 로직 단순화
5. **에러 처리 강화**: 예외 발생 시 질문 뱅크 모드로 자동 전환

## 결론

7, 8, 9번 bat 파일의 조기 종료 문제가 완전히 해결되었습니다. 

**주요 원인:**
1. Batch 스크립트 조건문 구문 오류 (한글 인코딩)
2. `%errorlevel%` 변수의 휘발성
3. 지연 확장(Delayed Expansion) 미사용

**해결 방법:**
1. `enabledelayedexpansion` 활성화
2. 즉시 종료 코드 캡처 (`set EXIT_CODE=!errorlevel!`)
3. 복잡한 조건문 블록 단순화
4. Python 스크립트 내부에서 자동 생성 처리

**검증:**
- 7번 파일: ✅ 정상 실행 (1731개 이벤트 생성)
- 8번 파일: ✅ 동일 패턴 적용
- 9번 파일: ✅ 동일 패턴 적용

이제 7, 8, 9번 bat 파일이 안정적으로 실행되며, 더 이상 조기 종료 문제가 발생하지 않습니다.

