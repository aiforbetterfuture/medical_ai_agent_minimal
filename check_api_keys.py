"""
API 키 검증 스크립트
.env 파일의 API 키들이 정상적으로 작동하는지 확인합니다.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"[✓] .env 파일 로드 완료: {env_path}")
else:
    print(f"[✗] .env 파일을 찾을 수 없습니다: {env_path}")
    print("\n.env 파일을 생성하고 다음 형식으로 API 키를 설정하세요:")
    print("OPENAI_API_KEY=your_key_here")
    print("GOOGLE_API_KEY=your_key_here  # 선택적")
    print("MEDCAT2_MODEL_PATH=path/to/model.pack  # 선택적")
    sys.exit(1)

print("\n" + "="*60)
print("API 키 검증 시작")
print("="*60 + "\n")

# OpenAI API 키 검증
openai_key = os.getenv('OPENAI_API_KEY')
if openai_key:
    print(f"[✓] OPENAI_API_KEY: 설정됨 ({openai_key[:10]}...{openai_key[-4:]})")
    try:
        import openai
        client = openai.OpenAI(api_key=openai_key)
        # 간단한 테스트 요청 (모델 목록 조회는 무료)
        try:
            models = client.models.list()
            model_count = len(list(models))
            print(f"    → OpenAI API 연결 성공! (사용 가능한 모델 수: {model_count})")
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                print(f"    → [✗] OpenAI API 키가 유효하지 않습니다. (401 Unauthorized)")
            elif "429" in error_msg:
                print(f"    → [⚠] OpenAI API 요청 한도 초과 (429)")
            else:
                print(f"    → [⚠] OpenAI API 연결 오류: {e}")
    except ImportError:
        print(f"    → [⚠] openai 패키지가 설치되지 않았습니다.")
    except Exception as e:
        print(f"    → [✗] OpenAI API 검증 실패: {e}")
else:
    print(f"[✗] OPENAI_API_KEY: 설정되지 않음")

# Google API 키 검증
google_key = os.getenv('GOOGLE_API_KEY')
if google_key:
    print(f"[✓] GOOGLE_API_KEY: 설정됨 ({google_key[:10]}...{google_key[-4:]})")
    try:
        import google.generativeai as genai
        genai.configure(api_key=google_key)
        # 간단한 테스트 (모델 생성 시도)
        try:
            # 간단한 모델 인스턴스 생성으로 테스트
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            # 실제 API 호출 없이 설정만 확인
            print(f"    → Google Gemini API 설정 완료!")
            print(f"    → (실제 API 호출은 첫 사용 시 수행됩니다)")
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg or "API key not valid" in error_msg:
                print(f"    → [✗] Google API 키가 유효하지 않습니다.")
            elif "429" in error_msg:
                print(f"    → [⚠] Google API 요청 한도 초과 (429)")
            else:
                # 패키지 버전 문제일 수 있으므로 경고만 표시
                print(f"    → [⚠] Google Gemini API 초기화 경고: {e}")
                print(f"    → (실제 사용 시 정상 작동할 수 있습니다)")
    except ImportError:
        print(f"    → [⚠] google-generativeai 패키지가 설치되지 않았습니다.")
    except Exception as e:
        print(f"    → [✗] Google Gemini API 검증 실패: {e}")
else:
    print(f"[○] GOOGLE_API_KEY: 설정되지 않음 (선택적)")

# MedCAT2 모델 경로 검증
medcat2_path = os.getenv('MEDCAT2_MODEL_PATH')
if medcat2_path:
    medcat2_path_obj = Path(medcat2_path)
    if medcat2_path_obj.exists():
        print(f"[✓] MEDCAT2_MODEL_PATH: 존재함 ({medcat2_path})")
        try:
            from medcat.cat import CAT
            model = CAT.load_model_pack(str(medcat2_path_obj))
            print(f"    → MedCAT2 모델 로드 성공!")
        except ImportError:
            print(f"    → [⚠] medcat 패키지가 설치되지 않았습니다.")
        except Exception as e:
            print(f"    → [✗] MedCAT2 모델 로드 실패: {e}")
    else:
        print(f"[✗] MEDCAT2_MODEL_PATH: 파일을 찾을 수 없음 ({medcat2_path})")
else:
    print(f"[○] MEDCAT2_MODEL_PATH: 설정되지 않음 (선택적)")

print("\n" + "="*60)
print("검증 완료")
print("="*60)

# 최소 요구사항 확인
if not openai_key:
    print("\n[⚠] 경고: OPENAI_API_KEY가 설정되지 않았습니다.")
    print("    이 프로젝트는 최소한 OpenAI API 키가 필요합니다.")
    sys.exit(1)
else:
    print("\n[✓] 최소 요구사항 충족: OpenAI API 키가 설정되어 있습니다.")

