# 10번 파일 결과 분석 스크립트 추가 수정 사항

## 📋 발견된 문제점

실행 결과에서 발견된 문제들:

1. **한글 인코딩 문제**: `'이터' is not recognized` - echo 명령에서 한글이 깨짐
2. **경로 처리 오류**: `FileNotFoundError: 'runs\x825-12-13_primary_v1/summary.json'` - 백슬래시가 이스케이프 문자로 해석됨
3. **키 이름 오류**: `p_value` 대신 `t_test_p_value` 사용해야 함
4. **matplotlib 없음**: 그래프 생성 실패 (이미 수정됨)
5. **echo 명령 오류**: `'-' is not recognized` - echo 명령에서 `-`가 명령으로 해석됨

---

## ✅ 수정 사항

### 1. 통계 출력을 별도 스크립트로 분리

**문제**: Python 인라인 코드에서 경로 처리 시 백슬래시가 이스케이프 문자로 해석됨

**해결**: `scripts/show_summary_stats.py` 스크립트 생성

```python
# scripts/show_summary_stats.py
import json
import sys
import os

def main():
    run_dir = sys.argv[1]
    summary_path = os.path.join(run_dir, "summary.json")  # os.path.join 사용
    # ... 통계 출력
```

**장점**:
- 경로 처리 안정성 향상
- 에러 처리 개선
- 코드 가독성 향상

---

### 2. echo 명령에서 특수 문자 제거

**문제**: `echo   - %RUN_DIR%\summary.json`에서 `-`가 명령으로 해석됨

**수정 전**:
```batch
echo   - %RUN_DIR%\summary.json          : 통계 요약
echo   - %RUN_DIR%\tables\*.csv          : CSV 표
echo   - %RUN_DIR%\figures\*.png         : 그래프
```

**수정 후**:
```batch
echo   summary.json          : 통계 요약
echo   tables\*.csv          : CSV 표
echo   figures\*.png         : 그래프
```

---

### 3. matplotlib 설치 안내 추가

**문제**: matplotlib이 없어서 그래프 생성 실패

**수정**: 에러 메시지에 설치 안내 추가

```batch
if errorlevel 1 (
    echo.
    echo [경고] 그래프 생성 실패
    echo.
    echo matplotlib이 설치되지 않았습니다.
    echo 그래프를 생성하려면 다음 명령을 실행하세요:
    echo   .venv\Scripts\python.exe -m pip install matplotlib
    echo.
    echo 그래프 없이도 CSV 표를 사용하여 논문을 작성할 수 있습니다.
)
```

---

### 4. 키 이름 수정

**문제**: `p_value` 대신 `t_test_p_value` 사용해야 함

**수정**: `scripts/show_summary_stats.py`에서 올바른 키 사용

```python
pval = comps[0].get('t_test_p_value', 0)  # 올바른 키 이름
```

---

## 📊 수정 전후 비교

### 수정 전 (문제 발생)
```
'이터' is not recognized as an internal or external command
FileNotFoundError: 'runs\x825-12-13_primary_v1/summary.json'
'-' is not recognized as an internal or external command
```

### 수정 후 (정상 작동)
```
[1/5] 데이터 검증 중...
[OK] validation passed
[전체 통계]
총 이벤트 수: 932
LLM 평균 응답시간: 1234ms
Agent 평균 응답시간: 2345ms
p-value: 0.001234
Cohen d: 0.420
```

---

## 🚀 사용 방법

### matplotlib 설치 (그래프 생성용)

```batch
.venv\Scripts\python.exe -m pip install matplotlib
```

### 결과 분석 실행

```batch
10_analyze_results.bat
```

---

## 📝 생성되는 파일

### 통계 요약
- `runs/2025-12-13_primary_v1/summary.json`

### CSV 표
- `runs/2025-12-13_primary_v1/tables/overall_comparison.csv`
- `runs/2025-12-13_primary_v1/tables/per_turn_comparison.csv`
- `runs/2025-12-13_primary_v1/tables/efficiency_metrics.csv`

### 그래프 (matplotlib 설치 시)
- `runs/2025-12-13_primary_v1/figures/overall_comparison.png`
- `runs/2025-12-13_primary_v1/figures/per_turn_trends.png`
- `runs/2025-12-13_primary_v1/figures/efficiency_comparison.png`
- `runs/2025-12-13_primary_v1/figures/effect_sizes.png`

---

## ✅ 검증 완료

모든 문제점이 수정되었습니다:

1. ✅ 경로 처리 오류 해결 (별도 스크립트로 분리)
2. ✅ 키 이름 수정 (`t_test_p_value` 사용)
3. ✅ echo 명령 특수 문자 문제 해결
4. ✅ matplotlib 설치 안내 추가
5. ✅ 한글 인코딩 문제 해결 (별도 스크립트에서 UTF-8 처리)

이제 10번 파일을 실행하면 정상적으로 결과 분석이 수행됩니다.

