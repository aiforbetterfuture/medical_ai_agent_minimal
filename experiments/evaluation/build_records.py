"""
events.jsonl에서 평가 레코드 빌드

ChatGPT 제안 코드를 기반으로, 현재 스캐폴드 구조에 맞게 수정
"""

import os
from typing import Any, Dict, List, Tuple, Optional
from .io.jsonl import read_jsonl

RecordKey = Tuple[str, str, int, str]  # (patient_id, mode, turn, q_id)


def _get(d: Dict[str, Any], *keys: str, default=None):
    """중첩된 딕셔너리에서 안전하게 값 가져오기"""
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def build_records_from_events(
    run_dir: str,
    events_file: str = "events.jsonl",
    node_trace_file: Optional[str] = "node_trace.jsonl",
) -> List[Dict[str, Any]]:
    """
    events.jsonl에서 평가 레코드 빌드
    
    현재 스캐폴드의 events.jsonl 구조:
    {
        "schema_version": "events_record.v1",
        "run_id": "...",
        "mode": "llm" | "agent",
        "patient_id": "...",
        "turn_id": 1,
        "question": {"question_id": "T1_Q15", "text": "..."},
        "answer": {"text": "...", "hash_sha256": "..."},
        "metadata": {...},
        "metrics": {...},  # RAGAS 메트릭
        ...
    }
    
    Args:
        run_dir: 실험 실행 디렉토리 (예: "runs/2025-12-13_primary_v1")
        events_file: events.jsonl 파일명
        node_trace_file: node_trace.jsonl 파일명 (선택적, fallback용)
    
    Returns:
        평가 레코드 리스트
        [
            {
                "patient_id": "SYN_0001",
                "mode": "llm",
                "turn": 1,
                "q_id": "T1_Q15",
                "question_text": "...",
                "answer_text": "...",
                "retrieved_docs": [...],
                "slots_state": {...},
                "turn_updates": {...},
                "context_injected": {...},
                "meta": {...}
            },
            ...
        ]
    """
    path = os.path.join(run_dir, events_file)
    if not os.path.exists(path):
        raise FileNotFoundError(f"events.jsonl not found: {path}")
    
    tmp: Dict[RecordKey, Dict[str, Any]] = {}
    
    def ensure(key: RecordKey) -> Dict[str, Any]:
        """레코드 초기화"""
        if key not in tmp:
            pid, mode, turn, qid = key
            tmp[key] = {
                "patient_id": pid,
                "mode": mode,
                "turn": turn,
                "q_id": qid,
                "question_text": None,
                "answer_text": None,
                "retrieved_docs": [],
                "context_injected": {},
                "slots_state": {},
                "turn_updates": {},
                "meta": {},
            }
        return tmp[key]
    
    # events.jsonl 읽기
    for ev in read_jsonl(path):
        # 현재 스캐폴드 구조에 맞게 필드 추출
        pid = ev.get("patient_id")
        mode = ev.get("mode")
        turn = ev.get("turn_id")  # 현재 스캐폴드는 "turn_id"
        qid = ev.get("question", {}).get("question_id") if isinstance(ev.get("question"), dict) else ev.get("question_id")
        
        if pid is None or mode is None or turn is None or qid is None:
            continue
        
        key: RecordKey = (str(pid), str(mode), int(turn), str(qid))
        rec = ensure(key)
        
        # 질문 텍스트
        if ev.get("question"):
            if isinstance(ev["question"], dict):
                rec["question_text"] = ev["question"].get("text") or rec["question_text"]
            else:
                rec["question_text"] = ev["question"]
        
        # 답변 텍스트
        if ev.get("answer"):
            if isinstance(ev["answer"], dict):
                rec["answer_text"] = ev["answer"].get("text") or rec["answer_text"]
            else:
                rec["answer_text"] = ev["answer"]
        
        # 검색된 문서 (metadata에서 추출)
        metadata = ev.get("metadata", {})
        retrieved_docs_count = metadata.get("retrieved_docs_count", 0)
        if retrieved_docs_count > 0 and not rec["retrieved_docs"]:
            # retrieved_docs가 직접 로깅되지 않았으면, metadata에서 추정
            # 실제 문서는 node_trace.jsonl에서 가져와야 함
            rec["retrieved_docs"] = []  # 나중에 node_trace에서 채움
        
        # 슬롯 상태 (metadata에서 추출, 없으면 빈 딕셔너리)
        if "slots_state" in metadata:
            rec["slots_state"] = metadata["slots_state"]
        
        # 턴 업데이트 (metadata에서 추출)
        if "turn_updates" in metadata:
            rec["turn_updates"] = metadata["turn_updates"]
        
        # 컨텍스트 주입 정보 (metadata에서 추출)
        if "context_injected" in metadata:
            rec["context_injected"] = metadata["context_injected"]
        
        # 메타 정보
        if "run_id" in ev:
            rec["meta"]["run_id"] = ev["run_id"]
        if "timestamp_utc" in ev:
            rec["meta"]["timestamp"] = ev["timestamp_utc"]
        if "timestamps" in ev and isinstance(ev["timestamps"], dict):
            rec["meta"]["started_at"] = ev["timestamps"].get("started_at_utc")
            rec["meta"]["ended_at"] = ev["timestamps"].get("ended_at_utc")
    
    # node_trace.jsonl에서 추가 정보 가져오기 (fallback)
    nt_path = os.path.join(run_dir, node_trace_file) if node_trace_file else None
    if nt_path and os.path.exists(nt_path):
        for ev in read_jsonl(nt_path):
            pid = ev.get("patient_id")
            mode = ev.get("mode")
            turn = ev.get("turn_id")
            qid = ev.get("question_id") or ev.get("q_id")
            
            if pid is None or mode is None or turn is None or qid is None:
                continue
            
            key: RecordKey = (str(pid), str(mode), int(turn), str(qid))
            if key not in tmp:
                continue
            
            rec = tmp[key]
            node = ev.get("node") or ev.get("node_name")
            
            # retrieve 노드에서 검색된 문서 가져오기
            if node == "retrieve":
                docs = ev.get("output", {}).get("docs") or ev.get("output", {}).get("retrieved_docs")
                if docs and not rec["retrieved_docs"]:
                    rec["retrieved_docs"] = docs
            
            # assemble_context 노드에서 컨텍스트 주입 정보 가져오기
            if node == "assemble_context" or node == "context_manager":
                context = ev.get("output", {}).get("context") or ev.get("output", {}).get("injected")
                if context and not rec["context_injected"]:
                    rec["context_injected"] = context
    
    return list(tmp.values())

