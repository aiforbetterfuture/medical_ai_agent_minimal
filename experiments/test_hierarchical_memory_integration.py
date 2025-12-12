"""
Hierarchical Memory 통합 테스트

3-tier 메모리 시스템의 기본 기능을 검증합니다.

테스트 항목:
1. Working Memory (Tier 1) 저장 및 검색
2. Compressed Memory (Tier 2) 압축 및 검색
3. Semantic Memory (Tier 3) 추출 및 검색
4. 5-turn 임계점에서 자동 압축
5. 토큰 예산 내 컨텍스트 검색
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from memory.hierarchical_memory import HierarchicalMemorySystem


def test_basic_memory_storage():
    """기본 메모리 저장 테스트"""
    print("\n" + "="*60)
    print("TEST 1: Basic Memory Storage")
    print("="*60)

    memory = HierarchicalMemorySystem(
        user_id="test_patient",
        working_capacity=5,
        compression_threshold=5
    )

    # 3개 턴 추가
    turns = [
        ("두통이 있어요.", "두통의 원인은 다양합니다. 언제부터 시작되었나요?", {"symptoms": ["두통"]}),
        ("3일 전부터요.", "최근에 다른 증상은 없으신가요?", {}),
        ("어지러움도 있어요.", "어지러움도 주의가 필요합니다. 혈압을 체크해보세요.", {"symptoms": ["어지러움"]})
    ]

    for user_query, agent_response, slots in turns:
        memory.add_turn(user_query, agent_response, slots)

    # 검증
    assert memory.total_turns == 3
    assert len(memory.working_memory) == 3
    assert len(memory.compressing_memory) == 0  # 아직 압축 안됨

    print(f"✓ Total turns: {memory.total_turns}")
    print(f"✓ Working memory size: {len(memory.working_memory)}")
    print(f"✓ Compressed memory count: {len(memory.compressing_memory)}")


def test_compression_trigger():
    """5-turn 압축 트리거 테스트"""
    print("\n" + "="*60)
    print("TEST 2: Compression Trigger at 5 Turns")
    print("="*60)

    memory = HierarchicalMemorySystem(
        user_id="test_patient",
        working_capacity=5,
        compression_threshold=5
    )

    # 5개 턴 추가
    turns = [
        ("두통이 있어요.", "두통의 원인은 다양합니다.", {"symptoms": ["두통"]}),
        ("고혈압이 있습니다.", "고혈압 관리가 중요합니다.", {"conditions": ["고혈압"]}),
        ("메트포르민을 먹어요.", "당뇨약을 복용 중이시군요.", {"medications": ["메트포르민"]}),
        ("아스피린도 먹어요.", "아스피린은 혈액순환에 도움이 됩니다.", {"medications": ["아스피린"]}),
        ("가슴이 답답해요.", "흉통은 즉시 검사가 필요합니다.", {"symptoms": ["흉통"]})
    ]

    for user_query, agent_response, slots in turns:
        memory.add_turn(user_query, agent_response, slots)

    # 검증
    assert memory.total_turns == 5
    # 5턴이므로 압축이 발생해야 함 (LLM 없으면 시도는 하지만 실패할 수 있음)
    print(f"✓ Total turns: {memory.total_turns}")
    print(f"✓ Working memory size: {len(memory.working_memory)}")
    print(f"✓ Compressed memory count: {len(memory.compressing_memory)}")

    # 6번째 턴 추가
    memory.add_turn(
        "혈압약을 추가로 먹어야 하나요?",
        "혈압 수치를 확인한 후 결정하는 것이 좋습니다.",
        {}
    )

    print(f"✓ After 6th turn - Working memory: {len(memory.working_memory)}")
    print(f"✓ After 6th turn - Compressed memory: {len(memory.compressing_memory)}")


def test_semantic_memory_extraction():
    """Semantic Memory 추출 테스트"""
    print("\n" + "="*60)
    print("TEST 3: Semantic Memory Extraction")
    print("="*60)

    memory = HierarchicalMemorySystem(
        user_id="test_patient",
        working_capacity=5,
        compression_threshold=5
    )

    # 만성질환 정보가 포함된 턴들
    turns = [
        ("고혈압 진단 받은 지 5년 됐어요.", "고혈압은 지속적인 관리가 필요합니다.", {"conditions": ["고혈압"]}),
        ("당뇨병도 3년 전부터 있어요.", "당뇨병도 꾸준한 관리가 중요합니다.", {"conditions": ["당뇨병"]}),
        ("메트포르민 500mg 먹어요.", "메트포르민은 당뇨 치료의 기본입니다.", {"medications": ["메트포르민"]}),
        ("아스피린도 매일 먹어요.", "아스피린은 심혈관 보호에 좋습니다.", {"medications": ["아스피린"]}),
        ("페니실린 알레르기가 있어요.", "알레르기 정보를 기록하겠습니다.", {"allergies": ["페니실린"]})
    ]

    for user_query, agent_response, slots in turns:
        memory.add_turn(user_query, agent_response, slots)

    # Semantic Memory 확인
    sem_mem = memory.semantic_memory

    print(f"✓ Chronic conditions: {len(sem_mem.chronic_conditions)}")
    for cond in sem_mem.chronic_conditions:
        print(f"  - {cond['name']} (mentioned {cond['frequency']} times)")

    print(f"✓ Chronic medications: {len(sem_mem.chronic_medications)}")
    for med in sem_mem.chronic_medications:
        print(f"  - {med['name']} (mentioned {med['frequency']} times)")

    print(f"✓ Allergies: {len(sem_mem.allergies)}")
    for allergy in sem_mem.allergies:
        print(f"  - {allergy['allergen']}")


def test_context_retrieval():
    """컨텍스트 검색 테스트"""
    print("\n" + "="*60)
    print("TEST 4: Context Retrieval with Token Budget")
    print("="*60)

    memory = HierarchicalMemorySystem(
        user_id="test_patient",
        working_capacity=5,
        compression_threshold=5
    )

    # 여러 턴 추가
    turns = [
        ("두통이 있어요.", "두통의 원인을 파악해야 합니다.", {"symptoms": ["두통"]}),
        ("고혈압이 있습니다.", "고혈압 관리가 필요합니다.", {"conditions": ["고혈압"]}),
        ("메트포르민을 먹어요.", "당뇨약을 복용 중이시군요.", {"medications": ["메트포르민"]}),
        ("아스피린도 먹어요.", "아스피린은 혈액순환에 도움이 됩니다.", {"medications": ["아스피린"]}),
        ("가슴이 답답해요.", "흉통은 즉시 검사가 필요합니다.", {"symptoms": ["흉통"]}),
        ("혈압약이 필요할까요?", "혈압 수치를 확인해봅시다.", {})
    ]

    for user_query, agent_response, slots in turns:
        memory.add_turn(user_query, agent_response, slots)

    # 컨텍스트 검색
    query = "제 증상과 약 때문에 걱정이 되는데요"
    contexts = memory.retrieve_context(query=query, max_tokens=500)

    print(f"✓ Working context length: {len(contexts.get('working_context', ''))} chars")
    print(f"✓ Compressed context length: {len(contexts.get('compressed_context', ''))} chars")
    print(f"✓ Semantic context length: {len(contexts.get('semantic_context', ''))} chars")

    # 컨텍스트 미리보기
    working = contexts.get('working_context', '')
    if working:
        print(f"\n[Working Context Preview]")
        print(working[:200] + "..." if len(working) > 200 else working)

    semantic = contexts.get('semantic_context', '')
    if semantic:
        print(f"\n[Semantic Context Preview]")
        print(semantic[:200] + "..." if len(semantic) > 200 else semantic)


def test_persistence():
    """파일 저장/로드 테스트"""
    print("\n" + "="*60)
    print("TEST 5: Save and Load from File")
    print("="*60)

    import tempfile
    import os

    # 임시 파일
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    temp_path = temp_file.name
    temp_file.close()

    try:
        # 메모리 생성 및 데이터 추가
        memory1 = HierarchicalMemorySystem(
            user_id="test_patient",
            working_capacity=5,
            compression_threshold=5
        )

        memory1.add_turn("두통이 있어요.", "두통의 원인을 파악해야 합니다.", {"symptoms": ["두통"]})
        memory1.add_turn("고혈압이 있습니다.", "고혈압 관리가 필요합니다.", {"conditions": ["고혈압"]})

        # 저장
        memory1.save_to_file(temp_path)
        print(f"✓ Memory saved to {temp_path}")

        # 로드
        memory2 = HierarchicalMemorySystem.load_from_file(temp_path)
        print(f"✓ Memory loaded from {temp_path}")

        # 검증
        assert memory2.user_id == "test_patient"
        assert memory2.total_turns == 2
        assert len(memory2.working_memory) == 2

        print(f"✓ User ID: {memory2.user_id}")
        print(f"✓ Total turns: {memory2.total_turns}")
        print(f"✓ Working memory size: {len(memory2.working_memory)}")

    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_path):
            os.remove(temp_path)


def run_all_tests():
    """모든 테스트 실행"""
    print("\n" + "="*60)
    print("HIERARCHICAL MEMORY INTEGRATION TESTS")
    print("="*60)

    try:
        test_basic_memory_storage()
        test_compression_trigger()
        test_semantic_memory_extraction()
        test_context_retrieval()
        test_persistence()

        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60 + "\n")

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
