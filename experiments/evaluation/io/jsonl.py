"""
JSONL 파일 I/O 유틸리티
"""

from typing import Any, Dict, Iterator
import json


def read_jsonl(path: str) -> Iterator[Dict[str, Any]]:
    """
    JSONL 파일 읽기
    
    Args:
        path: JSONL 파일 경로
    
    Yields:
        각 라인의 JSON 객체
    """
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                # JSON 파싱 오류는 로깅하고 계속 진행
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"JSON 파싱 오류 (라인 스킵): {e}")
                continue


def write_jsonl(path: str, rows: list[Dict[str, Any]]) -> None:
    """
    JSONL 파일 쓰기
    
    Args:
        path: JSONL 파일 경로
        rows: 쓰기할 딕셔너리 리스트
    """
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

