"""
계층형 메모리 시스템 검증 모듈

3-Tier 메모리 구조 검증:
- Tier 1 (Working Memory): 최근 5턴 원본 저장 확인
- Tier 2 (Compressed Memory): 5턴 도달 시 의학적 요약 확인
- Tier 3 (Semantic Memory): 만성질환/알레르기 저장 확인
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryVerificationResult:
    """메모리 검증 결과"""
    
    def __init__(self, patient_id: str, turn_id: int):
        self.patient_id = patient_id
        self.turn_id = turn_id
        self.timestamp = datetime.now().isoformat()
        
        # Tier 1: Working Memory 검증
        self.working_memory_verified = False
        self.working_memory_size = 0
        self.working_memory_turns = []  # 저장된 턴 ID 리스트
        self.working_memory_originality = True  # 원본 형태로 저장되었는지
        
        # Tier 2: Compressed Memory 검증
        self.compressed_memory_verified = False
        self.compressed_memory_count = 0
        self.compression_triggered = False  # 5턴 도달 시 압축 트리거됨
        self.compression_quality = 0.0  # 요약 품질 점수 (0.0~1.0)
        self.compression_medical_info_preserved = False  # 의학 정보 보존 여부
        
        # Tier 3: Semantic Memory 검증
        self.semantic_memory_verified = False
        self.chronic_conditions_count = 0
        self.chronic_medications_count = 0
        self.allergies_count = 0
        self.semantic_memory_updated = False
        
        # 전체 검증 상태
        self.all_tiers_verified = False
        self.verification_errors = []
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'patient_id': self.patient_id,
            'turn_id': self.turn_id,
            'timestamp': self.timestamp,
            'tier1_working_memory': {
                'verified': self.working_memory_verified,
                'size': self.working_memory_size,
                'turns': self.working_memory_turns,
                'originality': self.working_memory_originality
            },
            'tier2_compressed_memory': {
                'verified': self.compressed_memory_verified,
                'count': self.compressed_memory_count,
                'compression_triggered': self.compression_triggered,
                'quality': self.compression_quality,
                'medical_info_preserved': self.compression_medical_info_preserved
            },
            'tier3_semantic_memory': {
                'verified': self.semantic_memory_verified,
                'chronic_conditions_count': self.chronic_conditions_count,
                'chronic_medications_count': self.chronic_medications_count,
                'allergies_count': self.allergies_count,
                'updated': self.semantic_memory_updated
            },
            'overall': {
                'all_tiers_verified': self.all_tiers_verified,
                'errors': self.verification_errors
            }
        }


class MemoryVerifier:
    """계층형 메모리 검증기"""
    
    def __init__(self):
        self.verification_results: List[MemoryVerificationResult] = []
    
    def verify_tier1_working_memory(
        self,
        hierarchical_memory,
        expected_turns: int = 5
    ) -> Dict[str, Any]:
        """
        Tier 1 (Working Memory) 검증
        
        검증 항목:
        1. 최근 5턴이 모두 저장되어 있는가?
        2. 원본 형태로 저장되어 있는가? (user_query, agent_response 원문 유지)
        3. 턴 ID가 순차적으로 저장되어 있는가?
        """
        result = {
            'verified': False,
            'size': 0,
            'turns': [],
            'originality': True,
            'errors': []
        }
        
        if not hierarchical_memory or not hierarchical_memory.enabled:
            result['errors'].append("Hierarchical Memory가 활성화되지 않았습니다.")
            return result
        
        working_memory = hierarchical_memory.working_memory
        
        # 1. 크기 확인
        result['size'] = len(working_memory)
        if result['size'] < expected_turns:
            result['errors'].append(
                f"Working Memory 크기가 부족합니다. 예상: {expected_turns}, 실제: {result['size']}"
            )
        
        # 2. 턴 ID 확인
        turn_ids = [turn.turn_id for turn in working_memory]
        result['turns'] = turn_ids
        
        # 턴 ID가 순차적인지 확인
        if turn_ids:
            expected_ids = list(range(min(turn_ids), max(turn_ids) + 1))
            if turn_ids != expected_ids:
                result['errors'].append(
                    f"턴 ID가 순차적이지 않습니다. 실제: {turn_ids}"
                )
        
        # 3. 원본 형태 확인 (user_query, agent_response가 비어있지 않은지)
        for turn in working_memory:
            if not turn.user_query or not turn.agent_response:
                result['originality'] = False
                result['errors'].append(
                    f"턴 {turn.turn_id}의 원본이 손상되었습니다."
                )
        
        # 검증 통과
        if not result['errors'] and result['size'] >= expected_turns:
            result['verified'] = True
        
        return result
    
    def verify_tier2_compressed_memory(
        self,
        hierarchical_memory,
        current_turn: int
    ) -> Dict[str, Any]:
        """
        Tier 2 (Compressed Memory) 검증
        
        검증 항목:
        1. 5턴 도달 시 압축이 트리거되었는가?
        2. 요약이 의학적으로 의미 있는가? (의학 키워드 포함 여부)
        3. 핵심 의학 정보가 보존되었는가?
        """
        result = {
            'verified': False,
            'count': 0,
            'compression_triggered': False,
            'quality': 0.0,
            'medical_info_preserved': False,
            'errors': []
        }
        
        if not hierarchical_memory or not hierarchical_memory.enabled:
            result['errors'].append("Hierarchical Memory가 활성화되지 않았습니다.")
            return result
        
        compressing_memory = hierarchical_memory.compressing_memory
        result['count'] = len(compressing_memory)
        
        # 1. 5턴 도달 시 압축 트리거 확인
        if current_turn >= 5:
            # 5턴마다 압축이 수행되어야 함
            expected_compressions = (current_turn // 5)
            if result['count'] < expected_compressions:
                result['errors'].append(
                    f"압축 횟수가 부족합니다. 예상: {expected_compressions}, 실제: {result['count']}"
                )
            else:
                result['compression_triggered'] = True
        
        # 2. 요약 품질 확인 (의학 키워드 포함 여부)
        medical_keywords = [
            '증상', '질환', '약물', '검사', '진단', '치료', '관리',
            'symptom', 'condition', 'medication', 'test', 'diagnosis', 'treatment'
        ]
        
        quality_scores = []
        for compressed in compressing_memory:
            summary = compressed.summary.lower()
            keyword_count = sum(1 for keyword in medical_keywords if keyword in summary)
            quality = min(1.0, keyword_count / 5.0)  # 최소 5개 키워드면 1.0
            quality_scores.append(quality)
        
        if quality_scores:
            result['quality'] = sum(quality_scores) / len(quality_scores)
        else:
            result['quality'] = 0.0
        
        # 3. 핵심 의학 정보 보존 확인
        for compressed in compressing_memory:
            key_info = compressed.key_medical_info
            has_conditions = len(key_info.get('conditions', [])) > 0
            has_medications = len(key_info.get('medications', [])) > 0
            has_symptoms = len(key_info.get('symptoms', [])) > 0
            
            if has_conditions or has_medications or has_symptoms:
                result['medical_info_preserved'] = True
                break
        
        # 검증 통과
        if (result['compression_triggered'] and 
            result['quality'] >= 0.5 and 
            result['medical_info_preserved']):
            result['verified'] = True
        
        return result
    
    def verify_tier3_semantic_memory(
        self,
        hierarchical_memory,
        expected_chronic_conditions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Tier 3 (Semantic Memory) 검증
        
        검증 항목:
        1. 만성 질환이 저장되었는가?
        2. 만성 약물이 저장되었는가?
        3. 알레르기가 저장되었는가?
        4. 예상된 만성 질환이 포함되어 있는가?
        """
        result = {
            'verified': False,
            'chronic_conditions_count': 0,
            'chronic_medications_count': 0,
            'allergies_count': 0,
            'updated': False,
            'errors': []
        }
        
        if not hierarchical_memory or not hierarchical_memory.enabled:
            result['errors'].append("Hierarchical Memory가 활성화되지 않았습니다.")
            return result
        
        semantic_memory = hierarchical_memory.semantic_memory
        
        # 카운트
        result['chronic_conditions_count'] = len(semantic_memory.chronic_conditions)
        result['chronic_medications_count'] = len(semantic_memory.chronic_medications)
        result['allergies_count'] = len(semantic_memory.allergies)
        
        # 업데이트 여부 확인
        if semantic_memory.last_updated:
            result['updated'] = True
        
        # 예상된 만성 질환 확인
        if expected_chronic_conditions:
            stored_conditions = [c['name'] for c in semantic_memory.chronic_conditions]
            missing = [cond for cond in expected_chronic_conditions 
                      if cond not in stored_conditions]
            if missing:
                result['errors'].append(
                    f"예상된 만성 질환이 누락되었습니다: {missing}"
                )
        
        # 검증 통과 (최소 1개 이상의 장기 정보가 저장되어야 함)
        if (result['chronic_conditions_count'] > 0 or 
            result['chronic_medications_count'] > 0 or 
            result['allergies_count'] > 0):
            result['verified'] = True
        
        return result
    
    def verify_all_tiers(
        self,
        hierarchical_memory,
        current_turn: int,
        expected_chronic_conditions: Optional[List[str]] = None
    ) -> MemoryVerificationResult:
        """
        모든 Tier 검증
        
        Args:
            hierarchical_memory: HierarchicalMemorySystem 인스턴스
            current_turn: 현재 턴 번호
            expected_chronic_conditions: 예상되는 만성 질환 리스트 (선택적)
        
        Returns:
            MemoryVerificationResult 객체
        """
        # Tier 1 검증
        tier1_result = self.verify_tier1_working_memory(hierarchical_memory)
        
        # Tier 2 검증
        tier2_result = self.verify_tier2_compressed_memory(hierarchical_memory, current_turn)
        
        # Tier 3 검증
        tier3_result = self.verify_tier3_semantic_memory(
            hierarchical_memory, 
            expected_chronic_conditions
        )
        
        # 결과 통합
        verification_result = MemoryVerificationResult(
            patient_id=getattr(hierarchical_memory, 'user_id', 'unknown'),
            turn_id=current_turn
        )
        
        # Tier 1
        verification_result.working_memory_verified = tier1_result['verified']
        verification_result.working_memory_size = tier1_result['size']
        verification_result.working_memory_turns = tier1_result['turns']
        verification_result.working_memory_originality = tier1_result['originality']
        
        # Tier 2
        verification_result.compressed_memory_verified = tier2_result['verified']
        verification_result.compressed_memory_count = tier2_result['count']
        verification_result.compression_triggered = tier2_result['compression_triggered']
        verification_result.compression_quality = tier2_result['quality']
        verification_result.compression_medical_info_preserved = tier2_result['medical_info_preserved']
        
        # Tier 3
        verification_result.semantic_memory_verified = tier3_result['verified']
        verification_result.chronic_conditions_count = tier3_result['chronic_conditions_count']
        verification_result.chronic_medications_count = tier3_result['chronic_medications_count']
        verification_result.allergies_count = tier3_result['allergies_count']
        verification_result.semantic_memory_updated = tier3_result['updated']
        
        # 전체 검증
        all_errors = (
            tier1_result['errors'] + 
            tier2_result['errors'] + 
            tier3_result['errors']
        )
        verification_result.verification_errors = all_errors
        
        verification_result.all_tiers_verified = (
            tier1_result['verified'] and
            tier2_result['verified'] and
            tier3_result['verified'] and
            len(all_errors) == 0
        )
        
        # 결과 저장
        self.verification_results.append(verification_result)
        
        return verification_result
    
    def save_verification_results(self, filepath: str) -> None:
        """검증 결과를 파일로 저장"""
        try:
            data = {
                'verification_timestamp': datetime.now().isoformat(),
                'total_verifications': len(self.verification_results),
                'results': [r.to_dict() for r in self.verification_results]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"검증 결과 저장 완료: {filepath}")
        
        except Exception as e:
            logger.error(f"검증 결과 저장 실패: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """검증 결과 요약"""
        if not self.verification_results:
            return {'error': '검증 결과가 없습니다.'}
        
        total = len(self.verification_results)
        
        tier1_verified = sum(1 for r in self.verification_results if r.working_memory_verified)
        tier2_verified = sum(1 for r in self.verification_results if r.compressed_memory_verified)
        tier3_verified = sum(1 for r in self.verification_results if r.semantic_memory_verified)
        all_verified = sum(1 for r in self.verification_results if r.all_tiers_verified)
        
        avg_compression_quality = sum(
            r.compression_quality for r in self.verification_results
        ) / total if total > 0 else 0.0
        
        return {
            'total_verifications': total,
            'tier1_working_memory': {
                'verified_count': tier1_verified,
                'verified_rate': tier1_verified / total if total > 0 else 0.0
            },
            'tier2_compressed_memory': {
                'verified_count': tier2_verified,
                'verified_rate': tier2_verified / total if total > 0 else 0.0,
                'avg_quality': avg_compression_quality
            },
            'tier3_semantic_memory': {
                'verified_count': tier3_verified,
                'verified_rate': tier3_verified / total if total > 0 else 0.0
            },
            'all_tiers': {
                'verified_count': all_verified,
                'verified_rate': all_verified / total if total > 0 else 0.0
            }
        }

