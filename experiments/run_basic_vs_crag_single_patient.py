"""
Basic RAG vs Corrective RAG 단일 환자 비교 실험

목적:
- Synthea 환자 1명 선택
- 5턴 멀티턴 대화 실행
- Basic RAG vs CRAG 성능 비교

실험 설정:
- Basic RAG: self_refine_enabled=False (baseline)
- Corrective RAG: self_refine_enabled=True + LLM 품질 평가 + 동적 재작성
"""

import json
import random
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent.graph import run_agent


# ============================================================
# 실험 설정
# ============================================================

EXPERIMENT_CONFIG = {
    'experiment_id': f'basic_vs_crag_{datetime.now():%Y%m%d_%H%M%S}',
    'description': 'Single patient, 5-turn comparison: Basic RAG vs Corrective RAG',
    'random_seed': 42,
    'num_turns': 5,
}

# Basic RAG 설정 (baseline)
BASIC_RAG_CONFIG = {
    'self_refine_enabled': False,           # Self-Refine 비활성화
    'quality_check_enabled': False,         # 품질 검사 비활성화
    'llm_based_quality_check': False,       # LLM 평가 비활성화
    'dynamic_query_rewrite': False,         # 동적 재작성 비활성화
    'duplicate_detection': False,           # 중복 감지 비활성화
    'progress_monitoring': False,           # 진행도 모니터링 비활성화
    'response_cache_enabled': False,        # 캐시 비활성화 (순수 성능 측정)
}

# Corrective RAG 설정 (treatment)
CORRECTIVE_RAG_CONFIG = {
    'self_refine_enabled': True,            # ✅ Self-Refine 활성화
    'quality_check_enabled': True,          # ✅ 품질 검사 활성화
    'llm_based_quality_check': True,        # ✅ LLM 평가 활성화
    'dynamic_query_rewrite': True,          # ✅ 동적 재작성 활성화
    'duplicate_detection': True,            # ✅ 중복 감지 활성화
    'progress_monitoring': True,            # ✅ 진행도 모니터링 활성화
    'max_refine_iterations': 2,             # 최대 2회 재검색
    'quality_threshold': 0.5,               # 품질 임계값 0.5
    'response_cache_enabled': False,        # 캐시 비활성화 (순수 성능 측정)
}


# ============================================================
# 헬퍼 함수
# ============================================================

def load_patient_list(patient_list_path: Path) -> List[Dict]:
    """환자 리스트 로드"""
    with open(patient_list_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['patients']


def load_profile_card(profile_card_path: Path) -> Dict:
    """환자 프로필 카드 로드"""
    with open(profile_card_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_question_bank(question_bank_path: Path) -> Dict:
    """질문 뱅크 로드"""
    with open(question_bank_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def select_random_patient(patients: List[Dict], seed: int = 42) -> Dict:
    """환자 1명 랜덤 선택"""
    random.seed(seed)
    selected = random.choice(patients)
    print(f"\n[선택된 환자] {selected['patient_id']}")
    return selected


def get_questions_for_patient(
    patient_id: str,
    question_bank: Dict,
    num_turns: int = 5
) -> List[Dict]:
    """
    환자에 대한 5턴 질문 생성

    question_bank의 items에서 턴별로 질문 선택
    """
    questions = []
    items = question_bank.get('items', [])

    for turn_id in range(1, num_turns + 1):
        # 해당 턴의 질문들 필터링
        turn_questions = [q for q in items if q.get('turn_id') == turn_id]

        if turn_questions:
            # 환자 ID 기반으로 일관된 질문 선택 (SHA256 시뮬레이션)
            hash_val = hash(f"{patient_id}:{turn_id}")
            selected_q = turn_questions[hash_val % len(turn_questions)]

            questions.append({
                'turn_id': turn_id,
                'question_template': selected_q.get('template_text', ''),
                'question_id': selected_q.get('id', f'T{turn_id}_Q01'),
                'required_fields': selected_q.get('required_fields', []),
                'must_omit': selected_q.get('must_omit', []),
            })
        else:
            # 기본 질문 (해당 턴의 질문이 없을 경우)
            questions.append({
                'turn_id': turn_id,
                'question_template': f"턴 {turn_id}의 일반적인 건강 질문입니다.",
                'question_id': f'T{turn_id}_DEFAULT',
                'required_fields': [],
                'must_omit': [],
            })

    return questions


def resolve_placeholders(
    question_template: str,
    profile_card: Dict
) -> str:
    """
    질문 템플릿의 플레이스홀더를 환자 프로필로 대체

    Synthea 프로필 카드 구조에 맞게 데이터 추출
    """
    question = question_template

    # Demographics 추출
    demographics = profile_card.get('demographics', {})
    clinical = profile_card.get('clinical_summary', {})
    korean_aliases = profile_card.get('notes_for_generation', {}).get('korean_aliases', {})

    # ============================================================
    # 기본 정보
    # ============================================================

    # 나이
    age = demographics.get('age_years', '?')
    question = question.replace('{AGE}', str(age))

    # 성별 (한국어 변환)
    sex_code = demographics.get('sex', 'M')
    sex_ko_map = korean_aliases.get('sex', {'M': '남성', 'F': '여성'})
    sex_ko = sex_ko_map.get(sex_code, sex_code)
    question = question.replace('{SEX_KO}', sex_ko)

    # ============================================================
    # 질환 (Conditions)
    # ============================================================
    conditions = clinical.get('conditions', [])

    if conditions and len(conditions) > 0:
        # 첫 번째 질환
        cond1_name = conditions[0].get('name', '질환1')
        # 한국어 별칭이 있으면 사용
        cond1_ko = korean_aliases.get('conditions', {}).get(cond1_name, cond1_name)
        question = question.replace('{COND1_KO}', cond1_ko)

        # 두 번째 질환
        if len(conditions) > 1:
            cond2_name = conditions[1].get('name', '질환2')
            cond2_ko = korean_aliases.get('conditions', {}).get(cond2_name, cond2_name)
            question = question.replace('{COND2_KO}', cond2_ko)
    else:
        # 질환이 없으면 기본값
        question = question.replace('{COND1_KO}', '기저질환')
        question = question.replace('{COND2_KO}', '다른질환')

    # ============================================================
    # 약물 (Medications)
    # ============================================================
    medications = clinical.get('medications', [])

    if medications and len(medications) > 0:
        # 첫 번째 약물
        med1_name = medications[0].get('name', '약물1')
        question = question.replace('{MED1_KO}', med1_name)

        # 두 번째 약물
        if len(medications) > 1:
            med2_name = medications[1].get('name', '약물2')
            question = question.replace('{MED2_KO}', med2_name)
    else:
        # 약물이 없으면 기본값
        question = question.replace('{MED1_KO}', '복용약')
        question = question.replace('{MED2_KO}', '다른약')

    # ============================================================
    # 알레르기
    # ============================================================
    allergies = clinical.get('allergies', [])

    if allergies and len(allergies) > 0:
        allergy_text = allergies[0].get('name', '알레르기')
        question = question.replace('{ALLERGY_KO}', allergy_text)
    else:
        question = question.replace('{ALLERGY_KO}', '특정 알레르기')

    # ============================================================
    # Chief Complaint & Duration
    # ============================================================
    chief_complaint_seed = clinical.get('chief_complaint_seed', {})

    cc = chief_complaint_seed.get('complaint', '증상')
    dur = chief_complaint_seed.get('duration', '며칠')
    trigger = chief_complaint_seed.get('context', '특정 상황')

    question = question.replace('{CC}', cc)
    question = question.replace('{DUR}', dur)
    question = question.replace('{TRIGGER}', trigger)

    # ============================================================
    # Vitals (최근 측정값)
    # ============================================================
    vitals = clinical.get('vitals_recent', [])

    if vitals and len(vitals) > 0:
        # 첫 번째 vital (보통 혈압)
        vital = vitals[0]
        vital_name = vital.get('type', '혈압').replace('_', ' ')
        vital_value = str(vital.get('value', '140/90'))
        vital_unit = vital.get('unit', 'mmHg')

        question = question.replace('{VITAL_NAME}', vital_name)
        question = question.replace('{VITAL_VALUE}', vital_value)
        question = question.replace('{VITAL_UNIT}', vital_unit)
    else:
        question = question.replace('{VITAL_NAME}', '혈압')
        question = question.replace('{VITAL_VALUE}', '140/90')
        question = question.replace('{VITAL_UNIT}', 'mmHg')

    # ============================================================
    # Labs (최근 검사 결과)
    # ============================================================
    labs = clinical.get('labs_recent', [])

    if labs and len(labs) > 0:
        # 첫 번째 lab (보통 HbA1c)
        lab = labs[0]
        lab_name = lab.get('name', '혈당')
        lab_value = str(lab.get('value', '180'))
        lab_unit = lab.get('unit', 'mg/dL')

        question = question.replace('{LAB_NAME}', lab_name)
        question = question.replace('{LAB_VALUE}', lab_value)
        question = question.replace('{LAB_UNIT}', lab_unit)
    else:
        question = question.replace('{LAB_NAME}', '혈당')
        question = question.replace('{LAB_VALUE}', '180')
        question = question.replace('{LAB_UNIT}', 'mg/dL')

    # ============================================================
    # 기타 플레이스홀더 (턴별 특수값)
    # ============================================================

    # T4 턴용: OTC 약물
    turn_injection = profile_card.get('turn_injection_fields', {})
    t4_addition = turn_injection.get('T4_minor_addition', {})
    otc_text = t4_addition.get('payload', '타이레놀')
    question = question.replace('{OTC}', otc_text)

    # T3 턴용: 새로운 증상
    t3_update = turn_injection.get('T3_update_event', {}).get('payload', {})
    symptom_change = t3_update.get('symptom_change', '새로운 증상')
    question = question.replace('{NEW_INFO}', symptom_change)

    # ADD_SYM (추가 증상) - chief complaint의 severity나 context 활용
    add_sym = chief_complaint_seed.get('severity', '추가 증상')
    question = question.replace('{ADD_SYM}', add_sym)

    return question


def run_single_turn(
    query: str,
    strategy_name: str,
    feature_config: Dict,
    turn_id: int,
    conversation_history: str = None
) -> Dict:
    """
    단일 턴 실행

    Args:
        query: 사용자 질문
        strategy_name: 'basic_rag' 또는 'corrective_rag'
        feature_config: feature flags
        turn_id: 턴 번호
        conversation_history: 대화 이력

    Returns:
        턴 결과 딕셔너리
    """
    print(f"\n  [{strategy_name}] Turn {turn_id}: {query[:50]}...")

    start_time = time.time()

    try:
        result = run_agent(
            user_text=query,
            mode='ai_agent',
            conversation_history=conversation_history,
            feature_overrides=feature_config,
            return_state=True
        )

        elapsed = time.time() - start_time

        # 메트릭 추출
        metrics = {
            'turn_id': turn_id,
            'query': query,
            'answer': result.get('answer', ''),
            'strategy': strategy_name,
            'success': True,

            # 성능 메트릭
            'quality_score': result.get('quality_score', 0.0),
            'iteration_count': result.get('iteration_count', 0),
            'num_docs_retrieved': len(result.get('retrieved_docs', [])),
            'elapsed_sec': elapsed,

            # 비용 메트릭
            'total_tokens': result.get('total_tokens', 0),
            'estimated_cost_usd': result.get('estimated_cost_usd', 0.0),

            # Self-Refine 메트릭
            'refine_logs': result.get('refine_iteration_logs', []),
        }

        print(f"    ✓ Quality={metrics['quality_score']:.3f}, "
              f"Iterations={metrics['iteration_count']}, "
              f"Docs={metrics['num_docs_retrieved']}, "
              f"Time={elapsed:.1f}s")

        return metrics

    except Exception as e:
        print(f"    ✗ 오류: {str(e)}")
        elapsed = time.time() - start_time

        return {
            'turn_id': turn_id,
            'query': query,
            'strategy': strategy_name,
            'success': False,
            'error': str(e),
            'elapsed_sec': elapsed,
        }


def run_multiturn_experiment(
    patient_id: str,
    profile_card: Dict,
    questions: List[Dict],
    strategy_name: str,
    feature_config: Dict
) -> List[Dict]:
    """
    멀티턴 대화 실험 실행

    Args:
        patient_id: 환자 ID
        profile_card: 환자 프로필
        questions: 질문 리스트
        strategy_name: 전략 이름
        feature_config: feature flags

    Returns:
        턴별 결과 리스트
    """
    print(f"\n{'='*60}")
    print(f"[실험 시작] {strategy_name.upper()}")
    print(f"환자: {patient_id}")
    print(f"{'='*60}")

    results = []
    conversation_history = ""

    for turn_data in questions:
        turn_id = turn_data['turn_id']
        question_template = turn_data['question_template']

        # 플레이스홀더 해결
        query = resolve_placeholders(question_template, profile_card)

        # 턴 실행
        turn_result = run_single_turn(
            query=query,
            strategy_name=strategy_name,
            feature_config=feature_config,
            turn_id=turn_id,
            conversation_history=conversation_history
        )

        results.append(turn_result)

        # 대화 이력 업데이트
        if turn_result['success']:
            conversation_history += f"User: {query}\nAssistant: {turn_result['answer']}\n\n"

    return results


def calculate_summary_stats(results: List[Dict]) -> Dict:
    """결과 요약 통계 계산"""
    successful = [r for r in results if r.get('success', False)]

    if not successful:
        return {'error': '모든 턴 실패'}

    return {
        'total_turns': len(results),
        'successful_turns': len(successful),
        'avg_quality_score': sum(r['quality_score'] for r in successful) / len(successful),
        'avg_iteration_count': sum(r['iteration_count'] for r in successful) / len(successful),
        'avg_docs_retrieved': sum(r['num_docs_retrieved'] for r in successful) / len(successful),
        'avg_elapsed_sec': sum(r['elapsed_sec'] for r in successful) / len(successful),
        'total_tokens': sum(r.get('total_tokens', 0) for r in successful),
        'total_cost_usd': sum(r.get('estimated_cost_usd', 0.0) for r in successful),
    }


# ============================================================
# 메인 실험
# ============================================================

def main():
    print("="*80)
    print("Basic RAG vs Corrective RAG 비교 실험")
    print("="*80)
    print(f"실험 ID: {EXPERIMENT_CONFIG['experiment_id']}")
    print(f"Random Seed: {EXPERIMENT_CONFIG['random_seed']}")
    print(f"멀티턴 수: {EXPERIMENT_CONFIG['num_turns']}")
    print("="*80)

    # 1. 환자 리스트 로드
    patient_list_path = project_root / "data" / "patients" / "patient_list_80.json"
    patients = load_patient_list(patient_list_path)
    print(f"\n✓ 환자 리스트 로드: {len(patients)}명")

    # 2. 환자 1명 랜덤 선택
    selected_patient = select_random_patient(patients, EXPERIMENT_CONFIG['random_seed'])
    patient_id = selected_patient['patient_id']

    # 3. 프로필 카드 로드
    profile_card_path = project_root / selected_patient['profile_card_path']
    profile_card = load_profile_card(profile_card_path)
    print(f"✓ 프로필 카드 로드: {profile_card_path.name}")

    # 4. 질문 뱅크 로드
    question_bank_path = project_root / "experiments" / "question_bank" / "question_bank_5x15.v1.json"
    question_bank = load_question_bank(question_bank_path)
    print(f"✓ 질문 뱅크 로드: {question_bank_path.name}")

    # 5. 환자에 대한 5턴 질문 생성
    questions = get_questions_for_patient(
        patient_id,
        question_bank,
        EXPERIMENT_CONFIG['num_turns']
    )
    print(f"✓ 질문 생성: {len(questions)}개")

    # 6. Basic RAG 실험
    basic_rag_results = run_multiturn_experiment(
        patient_id=patient_id,
        profile_card=profile_card,
        questions=questions,
        strategy_name='basic_rag',
        feature_config=BASIC_RAG_CONFIG
    )

    # 7. Corrective RAG 실험
    corrective_rag_results = run_multiturn_experiment(
        patient_id=patient_id,
        profile_card=profile_card,
        questions=questions,
        strategy_name='corrective_rag',
        feature_config=CORRECTIVE_RAG_CONFIG
    )

    # 8. 결과 요약
    basic_summary = calculate_summary_stats(basic_rag_results)
    crag_summary = calculate_summary_stats(corrective_rag_results)

    print("\n" + "="*80)
    print("실험 결과 요약")
    print("="*80)

    print("\n[Basic RAG]")
    for key, value in basic_summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")

    print("\n[Corrective RAG]")
    for key, value in crag_summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")

    # 9. 개선율 계산
    if 'error' not in basic_summary and 'error' not in crag_summary:
        print("\n[개선율]")
        quality_improvement = ((crag_summary['avg_quality_score'] - basic_summary['avg_quality_score'])
                               / basic_summary['avg_quality_score'] * 100)
        time_increase = ((crag_summary['avg_elapsed_sec'] - basic_summary['avg_elapsed_sec'])
                        / basic_summary['avg_elapsed_sec'] * 100)
        cost_increase = ((crag_summary['total_cost_usd'] - basic_summary['total_cost_usd'])
                        / (basic_summary['total_cost_usd'] + 0.0001) * 100)

        print(f"  품질 점수: {quality_improvement:+.1f}%")
        print(f"  실행 시간: {time_increase:+.1f}%")
        print(f"  비용: {cost_increase:+.1f}%")

    # 10. 결과 저장
    output_dir = project_root / "runs" / "basic_vs_crag"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{EXPERIMENT_CONFIG['experiment_id']}.json"

    output_data = {
        'experiment_config': EXPERIMENT_CONFIG,
        'patient_id': patient_id,
        'profile_card_path': str(profile_card_path),
        'questions': questions,
        'basic_rag': {
            'config': BASIC_RAG_CONFIG,
            'results': basic_rag_results,
            'summary': basic_summary,
        },
        'corrective_rag': {
            'config': CORRECTIVE_RAG_CONFIG,
            'results': corrective_rag_results,
            'summary': crag_summary,
        },
        'timestamp': datetime.now().isoformat(),
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 결과 저장: {output_file}")
    print(f"   디렉토리: {output_dir}")

    print("\n" + "="*80)
    print("실험 완료! 🎉")
    print("="*80)


if __name__ == "__main__":
    main()