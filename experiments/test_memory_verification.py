"""
계층형 메모리 검증 테스트 스크립트

멀티턴 실험 결과를 기반으로 계층형 메모리 시스템 검증:
- Tier 1 (Working Memory): 최근 5턴 원본 저장 확인
- Tier 2 (Compressed Memory): 5턴 도달 시 의학적 요약 확인
- Tier 3 (Semantic Memory): 만성질환/알레르기 저장 확인
"""

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_events_jsonl(events_path: Path) -> List[Dict]:
    """events.jsonl 파일 로드"""
    events = []
    try:
        with open(events_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        logger.info(f"이벤트 로드 완료: {len(events)}개")
    except Exception as e:
        logger.error(f"이벤트 로드 실패: {e}")
    return events


def extract_memory_verification_results(events: List[Dict]) -> List[Dict]:
    """이벤트에서 메모리 검증 결과 추출"""
    verification_results = []
    
    for event in events:
        if event.get('mode') == 'agent' and event.get('memory_verification'):
            verification_results.append({
                'patient_id': event.get('patient_id'),
                'turn_id': event.get('turn_id'),
                'verification': event.get('memory_verification')
            })
    
    logger.info(f"메모리 검증 결과 추출: {len(verification_results)}개")
    return verification_results


def analyze_verification_results(verification_results: List[Dict]) -> Dict[str, Any]:
    """검증 결과 분석"""
    if not verification_results:
        return {'error': '검증 결과가 없습니다.'}
    
    total = len(verification_results)
    
    # Tier별 검증 통과율
    tier1_verified = sum(
        1 for r in verification_results 
        if r['verification'].get('tier1_working_memory', {}).get('verified', False)
    )
    tier2_verified = sum(
        1 for r in verification_results 
        if r['verification'].get('tier2_compressed_memory', {}).get('verified', False)
    )
    tier3_verified = sum(
        1 for r in verification_results 
        if r['verification'].get('tier3_semantic_memory', {}).get('verified', False)
    )
    all_verified = sum(
        1 for r in verification_results 
        if r['verification'].get('overall', {}).get('all_tiers_verified', False)
    )
    
    # 평균 값 계산
    avg_working_memory_size = sum(
        r['verification'].get('tier1_working_memory', {}).get('size', 0)
        for r in verification_results
    ) / total if total > 0 else 0
    
    avg_compressed_memory_count = sum(
        r['verification'].get('tier2_compressed_memory', {}).get('count', 0)
        for r in verification_results
    ) / total if total > 0 else 0
    
    avg_compression_quality = sum(
        r['verification'].get('tier2_compressed_memory', {}).get('quality', 0.0)
        for r in verification_results
    ) / total if total > 0 else 0.0
    
    avg_chronic_conditions = sum(
        r['verification'].get('tier3_semantic_memory', {}).get('chronic_conditions_count', 0)
        for r in verification_results
    ) / total if total > 0 else 0
    
    avg_chronic_medications = sum(
        r['verification'].get('tier3_semantic_memory', {}).get('chronic_medications_count', 0)
        for r in verification_results
    ) / total if total > 0 else 0
    
    avg_allergies = sum(
        r['verification'].get('tier3_semantic_memory', {}).get('allergies_count', 0)
        for r in verification_results
    ) / total if total > 0 else 0
    
    return {
        'total_verifications': total,
        'tier1_working_memory': {
            'verified_count': tier1_verified,
            'verified_rate': tier1_verified / total if total > 0 else 0.0,
            'avg_size': avg_working_memory_size
        },
        'tier2_compressed_memory': {
            'verified_count': tier2_verified,
            'verified_rate': tier2_verified / total if total > 0 else 0.0,
            'avg_count': avg_compressed_memory_count,
            'avg_quality': avg_compression_quality
        },
        'tier3_semantic_memory': {
            'verified_count': tier3_verified,
            'verified_rate': tier3_verified / total if total > 0 else 0.0,
            'avg_chronic_conditions': avg_chronic_conditions,
            'avg_chronic_medications': avg_chronic_medications,
            'avg_allergies': avg_allergies
        },
        'all_tiers': {
            'verified_count': all_verified,
            'verified_rate': all_verified / total if total > 0 else 0.0
        }
    }


def print_analysis_report(analysis: Dict[str, Any]) -> None:
    """분석 리포트 출력"""
    print("=" * 80)
    print("계층형 메모리 검증 결과 분석 리포트")
    print("=" * 80)
    print()
    
    if 'error' in analysis:
        print(f"오류: {analysis['error']}")
        return
    
    print(f"총 검증 횟수: {analysis['total_verifications']}회")
    print()
    
    tier1 = analysis['tier1_working_memory']
    print("Tier 1 (Working Memory):")
    print(f"  - 검증 통과: {tier1['verified_count']}회 ({tier1['verified_rate']*100:.1f}%)")
    print(f"  - 평균 크기: {tier1['avg_size']:.1f}턴")
    print()
    
    tier2 = analysis['tier2_compressed_memory']
    print("Tier 2 (Compressed Memory):")
    print(f"  - 검증 통과: {tier2['verified_count']}회 ({tier2['verified_rate']*100:.1f}%)")
    print(f"  - 평균 압축 메모리 수: {tier2['avg_count']:.1f}개")
    print(f"  - 평균 요약 품질: {tier2['avg_quality']:.2f}")
    print()
    
    tier3 = analysis['tier3_semantic_memory']
    print("Tier 3 (Semantic Memory):")
    print(f"  - 검증 통과: {tier3['verified_count']}회 ({tier3['verified_rate']*100:.1f}%)")
    print(f"  - 평균 만성 질환 수: {tier3['avg_chronic_conditions']:.1f}개")
    print(f"  - 평균 만성 약물 수: {tier3['avg_chronic_medications']:.1f}개")
    print(f"  - 평균 알레르기 수: {tier3['avg_allergies']:.1f}개")
    print()
    
    all_tiers = analysis['all_tiers']
    print("전체 Tier 검증:")
    print(f"  - 모든 Tier 통과: {all_tiers['verified_count']}회 ({all_tiers['verified_rate']*100:.1f}%)")
    print()
    
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='계층형 메모리 검증 결과 분석'
    )
    parser.add_argument(
        '--events',
        type=str,
        default='runs/2025-12-13_primary_v1/events.jsonl',
        help='events.jsonl 파일 경로'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='runs/memory_verification_analysis.json',
        help='분석 결과 저장 경로'
    )
    
    args = parser.parse_args()
    
    # 이벤트 로드
    events_path = Path(args.events)
    if not events_path.exists():
        logger.error(f"이벤트 파일을 찾을 수 없습니다: {events_path}")
        return
    
    events = load_events_jsonl(events_path)
    
    # 메모리 검증 결과 추출
    verification_results = extract_memory_verification_results(events)
    
    if not verification_results:
        logger.warning("메모리 검증 결과가 없습니다. events.jsonl에 memory_verification 필드가 있는지 확인하세요.")
        return
    
    # 분석
    analysis = analyze_verification_results(verification_results)
    
    # 리포트 출력
    print_analysis_report(analysis)
    
    # 결과 저장
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'verification_results': verification_results,
            'analysis': analysis
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"분석 결과 저장 완료: {output_path}")


if __name__ == '__main__':
    main()

