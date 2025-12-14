"""
통합 테스트 스크립트
기존 스캐폴드와의 통합이 올바르게 되었는지 검증
"""

import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """필수 모듈 임포트 테스트"""
    print("=" * 60)
    print("1. Import Test")
    print("=" * 60)

    try:
        from agent.graph import run_agent, get_agent_graph
        print("[OK] agent.graph import success")
    except ImportError as e:
        print(f"[FAIL] agent.graph import failed: {e}")
        return False

    try:
        from core.llm_client import get_llm_client
        print("[OK] core.llm_client import success")
    except ImportError as e:
        print(f"[FAIL] core.llm_client import failed: {e}")
        return False

    try:
        from core.config import get_llm_config, get_agent_config
        print("[OK] core.config import success")
    except ImportError as e:
        print(f"[FAIL] core.config import failed: {e}")
        return False

    try:
        from memory.profile_store import ProfileStore
        print("[OK] memory.profile_store import success")
    except ImportError as e:
        print(f"[FAIL] memory.profile_store import failed: {e}")
        return False

    print("\nAll imports successful!\n")
    return True


def test_agent_graph():
    """Agent 그래프 빌드 테스트"""
    print("=" * 60)
    print("2. Agent Graph Build Test")
    print("=" * 60)

    try:
        from agent.graph import get_agent_graph

        graph = get_agent_graph()
        print(f"[OK] Agent 그래프 빌드 성공")
        print(f"  그래프 타입: {type(graph)}")

        return True

    except Exception as e:
        print(f"[FAIL] Agent 그래프 빌드 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_client():
    """LLM 클라이언트 초기화 테스트"""
    print("=" * 60)
    print("3. LLM Client Test")
    print("=" * 60)

    try:
        from core.llm_client import get_llm_client
        import os

        # API 키 확인
        if not os.getenv('OPENAI_API_KEY'):
            print("[WARN] OPENAI_API_KEY가 설정되지 않았습니다.")
            print("  .env 파일에 API 키를 설정하세요.")
            return False

        client = get_llm_client(
            provider='openai',
            model='gpt-4o-mini',
            temperature=0.2
        )
        print("[OK] OpenAI 클라이언트 초기화 성공")

        return True

    except Exception as e:
        print(f"[FAIL] LLM 클라이언트 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_run_agent():
    """run_agent 함수 간단 테스트"""
    print("=" * 60)
    print("4. run_agent Function Test")
    print("=" * 60)

    try:
        from agent import graph as agent_graph_module
        import os

        # Clear graph cache to ensure latest code is used
        agent_graph_module._agent_graph_cache = None

        if not os.getenv('OPENAI_API_KEY'):
            print("[WARN] OPENAI_API_KEY가 없어 스킵합니다.")
            return True

        # 간단한 테스트 쿼리
        answer = agent_graph_module.run_agent(
            user_text="안녕하세요",
            mode='llm',
            conversation_history=None,
            return_state=False
        )

        print(f"[OK] run_agent (LLM 모드) 실행 성공")
        print(f"  답변 길이: {len(answer)} 문자")

        return True

    except Exception as e:
        print(f"[FAIL] run_agent 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_experiment_config():
    """실험 설정 파일 검증"""
    print("=" * 60)
    print("5. Experiment Config Test")
    print("=" * 60)

    try:
        import yaml
        from pathlib import Path

        config_path = Path("experiments/config.yaml")
        if not config_path.exists():
            print(f"[FAIL] 설정 파일이 없습니다: {config_path}")
            return False

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 필수 키 확인
        required_keys = ['run', 'reproducibility', 'modes', 'llm', 'agent']
        for key in required_keys:
            if key not in config:
                print(f"[FAIL] 필수 키 누락: {key}")
                return False

        print("[OK] 실험 설정 파일 검증 성공")
        print(f"  Run ID: {config['run']['run_id']}")
        print(f"  Modes: {config['modes']['run_order']}")

        return True

    except Exception as e:
        print(f"[FAIL] 설정 파일 검증 실패: {e}")
        return False


def test_question_bank():
    """질문 뱅크 검증"""
    print("=" * 60)
    print("6. Question Bank Test")
    print("=" * 60)

    try:
        import json
        from pathlib import Path

        qb_path = Path("experiments/question_bank/question_bank_5x15.v1.json")
        if not qb_path.exists():
            print(f"[FAIL] 질문 뱅크 파일이 없습니다: {qb_path}")
            return False

        with open(qb_path, 'r', encoding='utf-8') as f:
            qb = json.load(f)

        # 검증
        if 'items' not in qb:
            print("[FAIL] 'items' 키가 없습니다")
            return False

        items = qb['items']
        if len(items) != 75:
            print(f"[FAIL] 질문 개수가 75개가 아닙니다: {len(items)}개")
            return False

        # 턴별 개수 확인
        turn_counts = {}
        for item in items:
            turn_id = item['turn_id']
            turn_counts[turn_id] = turn_counts.get(turn_id, 0) + 1

        print("[OK] 질문 뱅크 검증 성공")
        print(f"  총 질문 수: {len(items)}개")
        for turn_id in sorted(turn_counts.keys()):
            print(f"  Turn {turn_id}: {turn_counts[turn_id]}개")

        return True

    except Exception as e:
        print(f"[FAIL] 질문 뱅크 검증 실패: {e}")
        return False


def test_patient_data():
    """환자 데이터 검증"""
    print("=" * 60)
    print("7. Patient Data Test")
    print("=" * 60)

    try:
        import json
        from pathlib import Path

        # patient_list 확인
        patient_list_path = Path("data/patients/patient_list_80.json")
        if not patient_list_path.exists():
            print(f"[FAIL] 환자 리스트 파일이 없습니다: {patient_list_path}")
            return False

        with open(patient_list_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        patients = data.get('patients', [])
        print(f"[OK] 환자 리스트 로드 성공: {len(patients)}명")

        # 프로파일 카드 확인
        profile_dir = Path("data/patients/profile_cards")
        if not profile_dir.exists():
            print(f"[FAIL] 프로파일 카드 디렉토리가 없습니다: {profile_dir}")
            return False

        profile_count = len(list(profile_dir.glob("SYN_*.json")))
        print(f"[OK] 프로파일 카드: {profile_count}개")

        if profile_count < 1:
            print("[WARN] 프로파일 카드가 부족합니다. scripts/generate_synthea_profiles.py를 실행하세요.")

        return True

    except Exception as e:
        print(f"[FAIL] 환자 데이터 검증 실패: {e}")
        return False


def main():
    """모든 테스트 실행"""
    print("\n" + "=" * 60)
    print(" 멀티턴 실험 통합 테스트")
    print("=" * 60 + "\n")

    tests = [
        ("Import Test", test_imports),
        ("Agent Graph Test", test_agent_graph),
        ("LLM Client Test", test_llm_client),
        ("run_agent Test", test_run_agent),
        ("Config Test", test_experiment_config),
        ("Question Bank Test", test_question_bank),
        ("Patient Data Test", test_patient_data),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[FAIL] {name} 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

        print()  # 빈 줄

    # 결과 요약
    print("=" * 60)
    print(" 테스트 결과 요약")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{status}: {name}")

    print(f"\n통과: {passed}/{total}")

    if passed == total:
        print("\n[SUCCESS] 모든 테스트 통과! 실험 실행 준비가 완료되었습니다.")
        return 0
    else:
        print("\n[WARN] 일부 테스트 실패. 위 오류 메시지를 확인하세요.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
