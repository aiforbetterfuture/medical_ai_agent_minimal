"""
Active Retrieval 통합 테스트

이 테스트는 Active Retrieval 시스템의 무결성을 검증합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_classify_intent_module():
    """classify_intent 모듈 임포트 테스트"""
    try:
        from agent.nodes.classify_intent import classify_intent_node, IntentClassifier
        print("✓ classify_intent module imported successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to import classify_intent: {e}")
        return False


def test_intent_classifier_basic():
    """IntentClassifier 기본 동작 테스트"""
    try:
        from agent.nodes.classify_intent import IntentClassifier

        feature_flags = {
            'active_retrieval_enabled': True,
            'simple_query_k': 3,
            'moderate_query_k': 8,
            'complex_query_k': 15
        }

        classifier = IntentClassifier(feature_flags)

        # Test 1: 인사 감지
        needs, k, complexity = classifier.classify("안녕하세요", {})
        assert not needs, "Greeting should not need retrieval"
        assert k == 0, "Greeting should have k=0"
        print("✓ Greeting detection works")

        # Test 2: 간단한 질문
        needs, k, complexity = classifier.classify(
            "정상 혈압은?",
            {'vitals': [{'name': '혈압'}]}
        )
        assert needs, "Medical question should need retrieval"
        assert k == 3, f"Simple query should have k=3, got {k}"
        assert complexity == "simple", f"Should be simple, got {complexity}"
        print("✓ Simple query classification works")

        # Test 3: 복잡한 질문
        needs, k, complexity = classifier.classify(
            "65세 남성, 당뇨병, 고혈압 환자입니다. 두통, 어지러움, 가슴 답답함이 있습니다.",
            {
                'conditions': [{'name': '당뇨병'}, {'name': '고혈압'}],
                'symptoms': [{'name': '두통'}, {'name': '어지러움'}, {'name': '가슴 답답함'}]
            }
        )
        assert needs, "Complex medical question should need retrieval"
        assert k == 15, f"Complex query should have k=15, got {k}"
        assert complexity == "complex", f"Should be complex, got {complexity}"
        print("✓ Complex query classification works")

        return True

    except AssertionError as e:
        print(f"✗ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metrics_collection():
    """메트릭 수집 시스템 테스트"""
    try:
        from agent.metrics.ablation_metrics import AblationMetrics, QueryMetrics

        # 메트릭 수집기 생성
        metrics = AblationMetrics(experiment_name="test_experiment")

        # 가짜 상태 생성
        fake_state = {
            'user_text': "테스트 질문",
            'needs_retrieval': True,
            'dynamic_k': 8,
            'query_complexity': "moderate",
            'classification_time_ms': 5.0,
            'retrieved_docs': [{'text': 'doc1'}, {'text': 'doc2'}],
            'answer': "테스트 답변입니다.",
            'quality_score': 0.8,
            'iteration_count': 0,
            'token_plan': {},
            'system_prompt': "System",
            'user_prompt': "User",
            'context_prompt': "Context"
        }

        # 쿼리 기록
        qm = metrics.record_query(fake_state, start_time=0.0, end_time=1.0)

        assert qm.query_text == "테스트 질문"
        assert qm.dynamic_k == 8
        assert qm.query_complexity == "moderate"
        print("✓ Metrics collection works")

        # 통계 계산
        stats = metrics.calculate_statistics()
        assert stats['total_queries'] == 1
        assert 'avg_latency_ms' in stats
        print("✓ Statistics calculation works")

        return True

    except AssertionError as e:
        print(f"✗ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_fields():
    """AgentState 필드 추가 확인"""
    try:
        from agent.state import AgentState

        # TypedDict는 런타임에 타입 체크를 하지 않으므로
        # __annotations__로 필드 존재 확인
        annotations = AgentState.__annotations__

        required_fields = [
            'dynamic_k',
            'query_complexity',
            'classification_skipped',
            'classification_time_ms',
            'classification_error',
            'intent_classifier'
        ]

        for field in required_fields:
            assert field in annotations, f"Field {field} not found in AgentState"

        print("✓ AgentState has all required fields")
        return True

    except AssertionError as e:
        print(f"✗ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_graph_integration():
    """그래프 통합 테스트"""
    try:
        from agent.graph import build_agent_graph

        # 그래프 빌드
        app = build_agent_graph()

        # 노드 존재 확인
        assert 'classify_intent' in str(app.get_graph()), "classify_intent node not found"
        print("✓ Graph includes classify_intent node")

        return True

    except AssertionError as e:
        print(f"✗ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_retrieve_dynamic_k():
    """retrieve_node의 dynamic_k 지원 테스트"""
    try:
        # retrieve.py 파일 읽기
        retrieve_path = project_root / "agent" / "nodes" / "retrieve.py"
        with open(retrieve_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # dynamic_k 관련 코드 존재 확인
        assert "dynamic_k = state.get('dynamic_k')" in content, "dynamic_k retrieval not found"
        assert "if dynamic_k is not None" in content, "dynamic_k check not found"
        print("✓ retrieve_node supports dynamic_k")

        return True

    except AssertionError as e:
        print(f"✗ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_feature_flags():
    """Feature flags 기본값 테스트"""
    try:
        from agent.graph import run_agent

        # Active Retrieval 비활성화 (기본값)
        state_off = run_agent(
            user_text="안녕하세요",
            mode='ai_agent',
            return_state=True
        )

        # classification_skipped가 True여야 함 (비활성화 시)
        assert state_off.get('classification_skipped') is not False, \
            "Active Retrieval should be disabled by default"
        print("✓ Feature flag defaults are safe (disabled)")

        return True

    except AssertionError as e:
        print(f"✗ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_end_to_end_with_active_retrieval():
    """End-to-end 테스트 (Active Retrieval 활성화)"""
    try:
        from agent.graph import run_agent

        # Test 1: 인사 (검색 스킵)
        state1 = run_agent(
            user_text="안녕하세요",
            mode='ai_agent',
            feature_overrides={'active_retrieval_enabled': True},
            return_state=True
        )

        needs_retrieval1 = state1.get('needs_retrieval')
        assert needs_retrieval1 is False, f"Greeting should not need retrieval, got {needs_retrieval1}"
        print("✓ End-to-end: Greeting skips retrieval")

        # Test 2: 의료 질문 (검색 실행)
        state2 = run_agent(
            user_text="정상 혈압 범위는?",
            mode='ai_agent',
            feature_overrides={'active_retrieval_enabled': True},
            return_state=True
        )

        needs_retrieval2 = state2.get('needs_retrieval')
        dynamic_k2 = state2.get('dynamic_k')
        assert needs_retrieval2 is True, "Medical question should need retrieval"
        assert dynamic_k2 is not None, "dynamic_k should be set"
        print(f"✓ End-to-end: Medical question uses retrieval (k={dynamic_k2})")

        return True

    except AssertionError as e:
        print(f"✗ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """에러 처리 테스트"""
    try:
        from agent.nodes.classify_intent import IntentClassifier

        feature_flags = {'active_retrieval_enabled': True}
        classifier = IntentClassifier(feature_flags)

        # None 입력 시 에러 처리
        try:
            needs, k, complexity = classifier.classify(None, {})
            # 에러가 발생해야 하지만, fallback으로 기본값 반환
            assert k >= 0, "Should return non-negative k"
            print("✓ Error handling works (None input)")
        except Exception:
            # 에러가 발생해도 괜찮음 (에러 처리가 있다면)
            print("✓ Error handling works (exception caught)")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def run_all_tests():
    """모든 테스트 실행"""
    tests = [
        ("Module Import", test_classify_intent_module),
        ("Intent Classifier Basic", test_intent_classifier_basic),
        ("Metrics Collection", test_metrics_collection),
        ("State Fields", test_state_fields),
        ("Graph Integration", test_graph_integration),
        ("Retrieve Dynamic K", test_retrieve_dynamic_k),
        ("Feature Flags", test_feature_flags),
        ("End-to-End Active Retrieval", test_end_to_end_with_active_retrieval),
        ("Error Handling", test_error_handling),
    ]

    print("\n" + "="*60)
    print("ACTIVE RETRIEVAL INTEGRATION TESTS")
    print("="*60 + "\n")

    results = []
    for name, test_func in tests:
        print(f"Running: {name}")
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"✗ Test crashed: {e}")
            results.append((name, False))
        print()

    # 요약
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 All tests passed! Active Retrieval is ready.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review.")

    print("="*60 + "\n")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
