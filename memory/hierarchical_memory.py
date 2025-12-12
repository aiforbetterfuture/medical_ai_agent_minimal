"""
3-Tier Hierarchical Memory System

단일 환자(사용자) 중심의 계층적 메모리 구조:
- Tier 1 (Working Memory): 최근 3-5턴 대화 원문 (즉시 접근)
- Tier 2 (Compressing Memory): 5턴 이상 시 중요 핵심 요약 저장
- Tier 3 (Semantic Memory): 장기 메모리 (만성질환, 알레르기 등)

특징:
- 1명의 환자 중심 (user_id 기반)
- MedCAT2 연동으로 의료 정보 추출 강화
- 자동 통합 및 요약
- Ablation study 지원
"""

from collections import deque
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json


@dataclass
class DialogueTurn:
    """단일 대화 턴"""
    turn_id: int
    user_query: str
    agent_response: str
    extracted_slots: Dict[str, Any]
    timestamp: str
    importance: float = 0.5

    def to_dict(self):
        return asdict(self)


@dataclass
class CompressedMemory:
    """압축된 메모리 (Tier 2)"""
    memory_id: int
    summary: str  # LLM 요약
    key_medical_info: Dict[str, Any]  # 핵심 의료 정보
    turn_range: tuple  # (start_turn, end_turn)
    timestamp: str
    importance: float = 0.7

    def to_dict(self):
        return asdict(self)


@dataclass
class SemanticMemory:
    """장기 메모리 (Tier 3)"""
    # 만성 질환
    chronic_conditions: List[Dict[str, Any]]

    # 만성 약물
    chronic_medications: List[Dict[str, Any]]

    # 알레르기
    allergies: List[Dict[str, Any]]

    # 장기적 건강 패턴
    health_patterns: Dict[str, Any]

    # 업데이트 타임스탬프
    last_updated: str

    def to_dict(self):
        return asdict(self)


class HierarchicalMemorySystem:
    """
    3-Tier 계층적 메모리 시스템

    단일 환자를 위한 메모리 관리:
    - Working Memory (Tier 1): 최근 5턴
    - Compressing Memory (Tier 2): 요약된 과거 대화
    - Semantic Memory (Tier 3): 장기 의료 정보

    안전성:
    - 초기화 실패 시 빈 메모리 사용
    - 압축 실패 시 원본 유지
    - 메트릭 수집으로 효과 추적
    """

    def __init__(
        self,
        user_id: str,
        working_capacity: int = 5,
        compression_threshold: int = 5,
        llm_client=None,
        medcat_adapter=None,
        feature_flags: Dict[str, Any] = None
    ):
        self.user_id = user_id
        self.working_capacity = working_capacity
        self.compression_threshold = compression_threshold
        self.llm_client = llm_client
        self.medcat_adapter = medcat_adapter
        self.feature_flags = feature_flags or {}

        # 설정
        self.enabled = self.feature_flags.get('hierarchical_memory_enabled', False)

        # Tier 1: Working Memory (최근 5턴)
        self.working_memory: deque = deque(maxlen=working_capacity)

        # Tier 2: Compressing Memory (요약된 과거)
        self.compressing_memory: List[CompressedMemory] = []

        # Tier 3: Semantic Memory (장기 메모리)
        self.semantic_memory = SemanticMemory(
            chronic_conditions=[],
            chronic_medications=[],
            allergies=[],
            health_patterns={},
            last_updated=datetime.now().isoformat()
        )

        # 카운터
        self.turn_counter = 0
        self.memory_counter = 0

        # 메트릭
        self.metrics = {
            'total_turns': 0,
            'compressions_performed': 0,
            'semantic_updates': 0,
            'avg_compression_time_ms': 0.0,
            'working_memory_hits': 0,
            'compressing_memory_hits': 0,
            'semantic_memory_hits': 0
        }

    def add_turn(
        self,
        user_query: str,
        agent_response: str,
        extracted_slots: Dict[str, Any]
    ) -> None:
        """
        새 턴 추가

        Args:
            user_query: 사용자 질문
            agent_response: 에이전트 답변
            extracted_slots: 추출된 슬롯 정보
        """
        if not self.enabled:
            return

        try:
            # 턴 중요도 계산
            importance = self._calculate_turn_importance(extracted_slots)

            # DialogueTurn 생성
            turn = DialogueTurn(
                turn_id=self.turn_counter,
                user_query=user_query,
                agent_response=agent_response,
                extracted_slots=extracted_slots,
                timestamp=datetime.now().isoformat(),
                importance=importance
            )

            # Working Memory에 추가
            self.working_memory.append(turn)
            self.turn_counter += 1
            self.metrics['total_turns'] += 1

            # 5턴 이상 시 압축 수행
            if self.turn_counter >= self.compression_threshold:
                # 매 5턴마다 압축
                if self.turn_counter % 5 == 0:
                    self._compress_to_tier2()

                # 매 5턴마다 Semantic Memory 업데이트
                if self.turn_counter % 5 == 0:
                    self._update_semantic_memory()

        except Exception as e:
            print(f"[WARNING] Failed to add turn to hierarchical memory: {e}")

    def _calculate_turn_importance(self, slots: Dict[str, Any]) -> float:
        """
        턴 중요도 계산

        기준:
        - 추출된 슬롯 개수
        - 만성 질환/약물 언급 여부
        - 알레르기 언급 여부
        """
        importance = 0.5  # 기본값

        # 슬롯 개수 기반
        slot_count = sum(
            len(v) if isinstance(v, list) else 1
            for v in slots.values()
            if v
        )
        importance += min(0.3, slot_count / 10.0)

        # 만성 질환 언급 (중요도 높음)
        chronic_keywords = ['당뇨', '고혈압', '심장', '신장', '간', '암', 'diabetes', 'hypertension']
        conditions = slots.get('conditions', [])
        for cond in conditions:
            cond_name = cond.get('name', '').lower()
            if any(keyword in cond_name for keyword in chronic_keywords):
                importance += 0.2
                break

        # 알레르기 언급 (중요도 높음)
        if 'allergies' in slots or 'allergy' in str(slots).lower():
            importance += 0.2

        return min(1.0, importance)

    def _compress_to_tier2(self) -> None:
        """
        Working Memory → Compressing Memory 압축

        5턴이 모이면 LLM으로 요약하여 Tier 2에 저장
        """
        if not self.llm_client or len(self.working_memory) == 0:
            return

        try:
            import time
            start_time = time.time()

            # Working Memory의 모든 턴을 텍스트로 변환
            turns_text = self._format_turns_for_compression(list(self.working_memory))

            # LLM으로 요약
            summary_prompt = f"""다음은 환자와의 최근 {len(self.working_memory)}턴 대화입니다.
이를 200 토큰 이내로 요약하되, 다음 정보를 우선 포함하세요:
1. 환자가 호소한 주요 증상
2. 진단되거나 의심되는 질환
3. 처방되거나 복용 중인 약물
4. 중요한 검사 수치
5. 향후 관리 계획

대화:
{turns_text}

요약 (한국어, 200 토큰 이내):"""

            summary = self.llm_client.generate(
                prompt=summary_prompt,
                max_tokens=200
            )

            # 핵심 의료 정보 추출
            key_medical_info = self._extract_key_medical_info(list(self.working_memory))

            # CompressedMemory 생성
            compressed = CompressedMemory(
                memory_id=self.memory_counter,
                summary=summary,
                key_medical_info=key_medical_info,
                turn_range=(
                    self.working_memory[0].turn_id,
                    self.working_memory[-1].turn_id
                ),
                timestamp=datetime.now().isoformat(),
                importance=self._calculate_compressed_importance(list(self.working_memory))
            )

            # Tier 2에 추가
            self.compressing_memory.append(compressed)
            self.memory_counter += 1
            self.metrics['compressions_performed'] += 1

            # 메트릭 업데이트
            elapsed_ms = (time.time() - start_time) * 1000
            self._update_compression_time(elapsed_ms)

            print(f"[Hierarchical Memory] Compressed turns {compressed.turn_range} to Tier 2")

        except Exception as e:
            print(f"[ERROR] Compression to Tier 2 failed: {e}")

    def _format_turns_for_compression(self, turns: List[DialogueTurn]) -> str:
        """턴 리스트를 LLM용 텍스트로 변환"""
        lines = []
        for turn in turns:
            lines.append(f"Turn {turn.turn_id}:")
            lines.append(f"환자: {turn.user_query}")
            lines.append(f"의사: {turn.agent_response[:200]}...")  # 답변은 200자로 제한
            lines.append("")
        return "\n".join(lines)

    def _extract_key_medical_info(self, turns: List[DialogueTurn]) -> Dict[str, Any]:
        """
        턴들에서 핵심 의료 정보 추출

        Returns:
            {
                'conditions': [...],
                'medications': [...],
                'symptoms': [...],
                'vitals': [...]
            }
        """
        key_info = {
            'conditions': [],
            'medications': [],
            'symptoms': [],
            'vitals': []
        }

        for turn in turns:
            slots = turn.extracted_slots

            # Conditions
            for cond in slots.get('conditions', []):
                if cond not in key_info['conditions']:
                    key_info['conditions'].append(cond)

            # Medications
            for med in slots.get('medications', []):
                if med not in key_info['medications']:
                    key_info['medications'].append(med)

            # Symptoms (중요한 것만)
            for symp in slots.get('symptoms', []):
                if symp.get('severity') in ['severe', 'moderate'] or turn.importance > 0.7:
                    if symp not in key_info['symptoms']:
                        key_info['symptoms'].append(symp)

            # Vitals
            for vital in slots.get('vitals', []):
                if vital not in key_info['vitals']:
                    key_info['vitals'].append(vital)

        return key_info

    def _calculate_compressed_importance(self, turns: List[DialogueTurn]) -> float:
        """압축된 메모리의 중요도 (평균)"""
        if not turns:
            return 0.5
        return sum(t.importance for t in turns) / len(turns)

    def _update_semantic_memory(self) -> None:
        """
        Tier 1 + Tier 2 → Tier 3 (Semantic Memory) 업데이트

        만성 질환, 만성 약물, 알레르기 등 장기적으로 중요한 정보 추출
        MedCAT2 연동으로 정교함 강화
        """
        try:
            # Working Memory + Compressing Memory의 모든 슬롯 수집
            all_slots = []

            # Working Memory에서 수집
            for turn in self.working_memory:
                all_slots.append(turn.extracted_slots)

            # Compressing Memory에서 수집
            for compressed in self.compressing_memory:
                all_slots.append(compressed.key_medical_info)

            # 만성 질환 추출 (MedCAT2 활용)
            self._extract_chronic_conditions(all_slots)

            # 만성 약물 추출
            self._extract_chronic_medications(all_slots)

            # 알레르기 추출
            self._extract_allergies(all_slots)

            # 건강 패턴 분석
            self._analyze_health_patterns(all_slots)

            # 업데이트 타임스탬프
            self.semantic_memory.last_updated = datetime.now().isoformat()
            self.metrics['semantic_updates'] += 1

            print(f"[Hierarchical Memory] Semantic Memory updated")

        except Exception as e:
            print(f"[ERROR] Semantic Memory update failed: {e}")

    def _extract_chronic_conditions(self, all_slots: List[Dict[str, Any]]) -> None:
        """
        만성 질환 추출 (MedCAT2 연동)

        기준:
        - 2회 이상 언급된 질환
        - '만성', '지속', '오래' 등의 키워드
        - MedCAT2로 검증된 만성 질환
        """
        condition_freq = {}

        for slots in all_slots:
            for cond in slots.get('conditions', []):
                cond_name = cond.get('name', '')
                if cond_name:
                    condition_freq[cond_name] = condition_freq.get(cond_name, 0) + 1

        # 만성 질환 키워드
        chronic_keywords = [
            '당뇨', '고혈압', '심장', '신장', '간', '암', '천식', '관절염',
            'diabetes', 'hypertension', 'heart', 'kidney', 'liver', 'cancer', 'asthma', 'arthritis'
        ]

        # 2회 이상 언급되거나 만성 키워드 포함
        for cond_name, freq in condition_freq.items():
            is_chronic = (
                freq >= 2 or
                any(keyword in cond_name.lower() for keyword in chronic_keywords)
            )

            if is_chronic:
                # 이미 존재하는지 확인
                if not any(c.get('name') == cond_name for c in self.semantic_memory.chronic_conditions):
                    self.semantic_memory.chronic_conditions.append({
                        'name': cond_name,
                        'first_mentioned': datetime.now().isoformat(),
                        'frequency': freq,
                        'verified_by': 'frequency' if freq >= 2 else 'keyword'
                    })

                    # MedCAT2로 추가 검증 (선택적)
                    if self.medcat_adapter:
                        self._verify_with_medcat(cond_name, 'condition')

    def _extract_chronic_medications(self, all_slots: List[Dict[str, Any]]) -> None:
        """
        만성 약물 추출

        기준:
        - 2회 이상 언급된 약물
        - '매일', '장기', '복용 중' 등의 키워드
        """
        med_freq = {}

        for slots in all_slots:
            for med in slots.get('medications', []):
                med_name = med.get('name', '')
                if med_name:
                    med_freq[med_name] = med_freq.get(med_name, 0) + 1

        # 2회 이상 언급
        for med_name, freq in med_freq.items():
            if freq >= 2:
                if not any(m.get('name') == med_name for m in self.semantic_memory.chronic_medications):
                    self.semantic_memory.chronic_medications.append({
                        'name': med_name,
                        'first_mentioned': datetime.now().isoformat(),
                        'frequency': freq
                    })

    def _extract_allergies(self, all_slots: List[Dict[str, Any]]) -> None:
        """
        알레르기 추출 (중요 - 1회 언급도 저장)
        """
        for slots in all_slots:
            # 슬롯에서 알레르기 정보 찾기
            # (현재 슬롯 구조에 allergies 필드가 없다면 추가 필요)
            allergies = slots.get('allergies', [])
            for allergy in allergies:
                allergy_name = allergy.get('name', '')
                if allergy_name:
                    if not any(a.get('name') == allergy_name for a in self.semantic_memory.allergies):
                        self.semantic_memory.allergies.append({
                            'name': allergy_name,
                            'first_mentioned': datetime.now().isoformat(),
                            'severity': allergy.get('severity', 'unknown')
                        })

    def _analyze_health_patterns(self, all_slots: List[Dict[str, Any]]) -> None:
        """
        건강 패턴 분석

        예: 평균 혈압, 평균 혈당, 증상 빈도 등
        """
        # 혈압 패턴
        sbp_values = []
        dbp_values = []

        for slots in all_slots:
            for vital in slots.get('vitals', []):
                if vital.get('name') == 'SBP':
                    sbp_values.append(vital.get('value'))
                elif vital.get('name') == 'DBP':
                    dbp_values.append(vital.get('value'))

        if sbp_values:
            self.semantic_memory.health_patterns['avg_sbp'] = sum(sbp_values) / len(sbp_values)
        if dbp_values:
            self.semantic_memory.health_patterns['avg_dbp'] = sum(dbp_values) / len(dbp_values)

        # 증상 빈도
        symptom_freq = {}
        for slots in all_slots:
            for symp in slots.get('symptoms', []):
                symp_name = symp.get('name', '')
                if symp_name:
                    symptom_freq[symp_name] = symptom_freq.get(symp_name, 0) + 1

        self.semantic_memory.health_patterns['frequent_symptoms'] = [
            {'name': name, 'frequency': freq}
            for name, freq in sorted(symptom_freq.items(), key=lambda x: x[1], reverse=True)[:3]
        ]

    def _verify_with_medcat(self, entity_name: str, entity_type: str) -> None:
        """
        MedCAT2로 의료 엔티티 검증 (선택적)

        Args:
            entity_name: 엔티티 이름
            entity_type: 'condition' 또는 'medication'
        """
        try:
            if not self.medcat_adapter:
                return

            # MedCAT2로 검증
            result = self.medcat_adapter.extract(entity_name)

            # 신뢰도 높은 경우에만 검증 마크
            if result and len(result) > 0:
                top_result = result[0]
                if top_result.get('confidence', 0) > 0.7:
                    print(f"[MedCAT2] Verified '{entity_name}' as {entity_type}")

        except Exception as e:
            print(f"[WARNING] MedCAT2 verification failed: {e}")

    def retrieve_context(
        self,
        query: str,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        계층별 컨텍스트 검색

        Args:
            query: 사용자 쿼리
            max_tokens: 최대 토큰 수

        Returns:
            {
                'working': str,      # Tier 1 컨텍스트
                'compressed': str,   # Tier 2 컨텍스트
                'semantic': str,     # Tier 3 컨텍스트
                'metrics': dict      # 검색 메트릭
            }
        """
        if not self.enabled:
            return {
                'working': '',
                'compressed': '',
                'semantic': '',
                'metrics': {}
            }

        try:
            # 예산 할당
            budgets = self._allocate_budget(max_tokens)

            # Tier 1: Working Memory (전체 포함)
            working_context = self._format_working_memory(budgets['working'])

            # Tier 2: Compressing Memory (관련도 높은 것만)
            compressed_context = self._format_compressing_memory(query, budgets['compressed'])

            # Tier 3: Semantic Memory (프로필 요약)
            semantic_context = self._format_semantic_memory(budgets['semantic'])

            # 메트릭 업데이트
            if working_context:
                self.metrics['working_memory_hits'] += 1
            if compressed_context:
                self.metrics['compressing_memory_hits'] += 1
            if semantic_context:
                self.metrics['semantic_memory_hits'] += 1

            return {
                'working': working_context,
                'compressed': compressed_context,
                'semantic': semantic_context,
                'metrics': {
                    'working_turns': len(self.working_memory),
                    'compressed_memories': len(self.compressing_memory),
                    'chronic_conditions': len(self.semantic_memory.chronic_conditions),
                    'chronic_medications': len(self.semantic_memory.chronic_medications)
                }
            }

        except Exception as e:
            print(f"[ERROR] Context retrieval failed: {e}")
            return {
                'working': '',
                'compressed': '',
                'semantic': '',
                'metrics': {}
            }

    def _allocate_budget(self, total: int) -> Dict[str, int]:
        """
        계층별 토큰 예산 할당

        - Working: 50% (최근 대화 중요)
        - Compressed: 30% (과거 요약)
        - Semantic: 20% (장기 프로필)
        """
        return {
            'working': int(total * 0.5),
            'compressed': int(total * 0.3),
            'semantic': int(total * 0.2)
        }

    def _format_working_memory(self, budget: int) -> str:
        """Working Memory를 텍스트로 변환"""
        if not self.working_memory:
            return ""

        lines = []
        for turn in reversed(self.working_memory):
            line = f"User: {turn.user_query}\nAgent: {turn.agent_response[:200]}...\n"
            # 간단한 토큰 추정 (단어 수 / 0.75)
            estimated_tokens = len(line.split()) / 0.75
            if estimated_tokens > budget:
                break
            lines.append(line)
            budget -= estimated_tokens

        return "\n".join(reversed(lines)) if lines else ""

    def _format_compressing_memory(self, query: str, budget: int) -> str:
        """Compressing Memory에서 관련도 높은 것만 선택"""
        if not self.compressing_memory:
            return ""

        # 중요도 순 정렬 (간단하게 importance 기준)
        sorted_memories = sorted(
            self.compressing_memory,
            key=lambda m: m.importance,
            reverse=True
        )

        lines = []
        for mem in sorted_memories:
            line = f"[요약 {mem.memory_id}] {mem.summary}\n"
            estimated_tokens = len(line.split()) / 0.75
            if estimated_tokens > budget:
                break
            lines.append(line)
            budget -= estimated_tokens

        return "\n".join(lines) if lines else ""

    def _format_semantic_memory(self, budget: int) -> str:
        """Semantic Memory를 텍스트로 변환"""
        parts = []

        # 만성 질환
        if self.semantic_memory.chronic_conditions:
            conds = [c['name'] for c in self.semantic_memory.chronic_conditions]
            parts.append(f"만성 질환: {', '.join(conds)}")

        # 만성 약물
        if self.semantic_memory.chronic_medications:
            meds = [m['name'] for m in self.semantic_memory.chronic_medications]
            parts.append(f"복용 약물: {', '.join(meds)}")

        # 알레르기
        if self.semantic_memory.allergies:
            allergies = [a['name'] for a in self.semantic_memory.allergies]
            parts.append(f"알레르기: {', '.join(allergies)}")

        # 건강 패턴
        if self.semantic_memory.health_patterns:
            patterns = []
            if 'avg_sbp' in self.semantic_memory.health_patterns:
                patterns.append(f"평균 혈압: {self.semantic_memory.health_patterns['avg_sbp']:.0f}/{self.semantic_memory.health_patterns.get('avg_dbp', 0):.0f}")
            if patterns:
                parts.append(", ".join(patterns))

        result = "\n".join(parts)

        # 예산 초과 시 절삭
        estimated_tokens = len(result.split()) / 0.75
        if estimated_tokens > budget:
            words = result.split()
            max_words = int(budget * 0.75)
            result = " ".join(words[:max_words]) + "..."

        return result

    def _update_compression_time(self, elapsed_ms: float):
        """압축 시간 메트릭 업데이트"""
        n = self.metrics['compressions_performed']
        if n == 0:
            return
        current_avg = self.metrics['avg_compression_time_ms']
        self.metrics['avg_compression_time_ms'] = (
            (current_avg * (n - 1) + elapsed_ms) / n
        )

    def get_metrics(self) -> Dict[str, Any]:
        """메트릭 반환"""
        return self.metrics.copy()

    def save_to_file(self, filepath: str) -> None:
        """메모리를 파일로 저장"""
        try:
            data = {
                'user_id': self.user_id,
                'turn_counter': self.turn_counter,
                'memory_counter': self.memory_counter,
                'working_memory': [turn.to_dict() for turn in self.working_memory],
                'compressing_memory': [mem.to_dict() for mem in self.compressing_memory],
                'semantic_memory': self.semantic_memory.to_dict(),
                'metrics': self.metrics
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"[Hierarchical Memory] Saved to {filepath}")

        except Exception as e:
            print(f"[ERROR] Failed to save memory: {e}")

    def load_from_file(self, filepath: str) -> None:
        """파일에서 메모리 로드"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.turn_counter = data['turn_counter']
            self.memory_counter = data['memory_counter']

            # Working Memory 복원
            self.working_memory = deque(
                [DialogueTurn(**turn) for turn in data['working_memory']],
                maxlen=self.working_capacity
            )

            # Compressing Memory 복원
            self.compressing_memory = [
                CompressedMemory(**mem) for mem in data['compressing_memory']
            ]

            # Semantic Memory 복원
            self.semantic_memory = SemanticMemory(**data['semantic_memory'])

            # 메트릭 복원
            self.metrics = data['metrics']

            print(f"[Hierarchical Memory] Loaded from {filepath}")

        except Exception as e:
            print(f"[ERROR] Failed to load memory: {e}")
