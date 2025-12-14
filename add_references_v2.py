#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
참고문헌 번호 추가 스크립트 (개선 버전)
251212_thesis_update_cursor_v1.md와 v2.md 파일에 참고문헌 번호를 추가합니다.
"""

import re
from typing import List, Tuple, Set

# 참고문헌 매핑 (원래 번호 그대로 사용)
# 251213_thesis_final_v1.md의 참고문헌 번호 기준
REF_MAPPINGS = {
    # RAG 관련
    (r'\bRAG\b', r'검색.*증강.*생성', r'Retrieval-Augmented Generation'): [1, 15],
    (r'Lewis.*2020',): [1],
    
    # MedCAT2
    (r'MedCAT2', r'MedCAT', r'Kraljevic.*2021'): [7],
    (r'의학.*개념.*주석', r'의학.*엔티티.*추출'): [7],
    
    # UMLS
    (r'UMLS', r'Unified Medical Language System'): [31],
    (r'CUI',): [31],
    
    # LangGraph
    (r'LangGraph',): [9, 10, 11],
    (r'LangChain', r'Chase.*2022'): [9],
    (r'상태.*기반.*워크플로우', r'순환.*아키텍처'): [9, 10],
    
    # Self-Refine
    (r'Self-Refine', r'Madaan.*2023', r'자기개선'): [12],
    (r'품질.*평가.*재작성',): [12],
    
    # CRAG
    (r'CRAG', r'Corrective RAG', r'Yan.*2024'): [13],
    (r'재검색.*품질',): [13],
    
    # RAGAS
    (r'RAGAS', r'Es.*2023'): [14],
    (r'Faithfulness',): [14],
    (r'Answer Relevance',): [14],
    (r'근거.*충실성', r'정답.*관련성'): [14],
    
    # BM25
    (r'BM25', r'Robertson.*2009', r'Zaragoza'): [16],
    (r'키워드.*검색',): [16],
    
    # RRF
    (r'RRF', r'Reciprocal Rank Fusion', r'Cormack.*2009'): [17],
    (r'상호.*순위.*융합',): [17],
    
    # FAISS
    (r'FAISS', r'Johnson.*2019'): [18],
    (r'벡터.*검색',): [18],
    
    # Active Retrieval
    (r'Active Retrieval', r'Jiang.*2023', r'능동적.*검색'): [24],
    (r'동적.*k', r'질의.*복잡도'): [24],
    
    # Synthea
    (r'Synthea', r'Walonoski.*2018', r'가상.*환자'): [32],
    (r'생성.*환자', r'합성.*환자'): [32],
    
    # 의료 LLM
    (r'Med-PaLM', r'메드팜', r'Singhal.*2023'): [8],
    (r'의료.*LLM',): [8],
    
    # 통계
    (r'Cohen.*1988', r'Cohen\'s d'): [39],
    (r'Faul.*2007', r'G\*Power'): [40],
    (r'p < 0\.001', r'통계적.*유의성', r'통계적.*검증'): [39, 40],
    (r't-test',): [39, 40],
    
    # 기타
    (r'BioBERT', r'Lee.*2020'): [5],
    (r'GPT-4', r'Achiam.*2023'): [38],
    (r'Brown.*2020',): [37],
    (r'Wei.*2022', r'Chain-of-Thought'): [36],
    (r'Park.*2014', r'KoNLPy'): [34],
    (r'대한고혈압학회.*2022',): [28],
    (r'대한당뇨병학회.*2023',): [29],
    (r'WHO', r'World Health Organization'): [30],
    (r'Perplexity',): [37],
}

def find_references_in_sentence(sentence: str) -> Set[int]:
    """문장에서 참고문헌 키워드를 찾아 참고문헌 번호 집합 반환"""
    found_refs = set()
    
    for patterns, refs in REF_MAPPINGS.items():
        for pattern in patterns:
            if re.search(pattern, sentence, re.IGNORECASE | re.UNICODE):
                found_refs.update(refs)
                break
    
    return found_refs

def split_sentences_safely(text: str) -> List[str]:
    """문장을 안전하게 분리 (숫자 중간의 마침표 제외)"""
    # 숫자.숫자 패턴을 보호
    protected = []
    pattern = r'\d+\.\d+'
    matches = list(re.finditer(pattern, text))
    
    if not matches:
        # 일반 문장 분리
        parts = re.split(r'([.!?。！？]\s+)', text)
        result = []
        for i in range(0, len(parts), 2):
            if i < len(parts):
                sent = parts[i]
                if i + 1 < len(parts):
                    sent += parts[i + 1]
                if sent.strip():
                    result.append(sent)
        return result
    
    # 숫자 패턴을 임시로 치환
    placeholders = {}
    protected_text = text
    for i, match in enumerate(matches):
        placeholder = f"__NUM_{i}__"
        placeholders[placeholder] = match.group()
        protected_text = protected_text.replace(match.group(), placeholder)
    
    # 문장 분리
    parts = re.split(r'([.!?。！？]\s+)', protected_text)
    result = []
    for i in range(0, len(parts), 2):
        if i < len(parts):
            sent = parts[i]
            if i + 1 < len(parts):
                sent += parts[i + 1]
            # 원래 숫자 복원
            for ph, num in placeholders.items():
                sent = sent.replace(ph, num)
            if sent.strip():
                result.append(sent)
    
    return result

def add_references_to_file(content: str, start_ref_num: int = 1) -> Tuple[str, int]:
    """파일 내용에 참고문헌 번호 추가 (원래 번호 유지)"""
    lines = content.split('\n')
    result_lines = []
    used_refs = set()  # 사용된 참고문헌 번호 추적
    ref_num_map = {}  # 원래 번호 -> 새로운 순차 번호 매핑
    current_ref_num = start_ref_num
    
    for line in lines:
        # 코드 블록이나 다이어그램 주석은 건너뛰기
        if (line.strip().startswith('```') or 
            line.strip().startswith('**[다이어그램') or 
            line.strip().startswith('**[') or
            line.strip().startswith('|') and '|' in line[1:]):  # 표는 건너뛰기
            result_lines.append(line)
            continue
        
        # 이미 참고문헌 번호가 있는 줄은 건너뛰기
        if re.search(r'\[\d+\]', line):
            result_lines.append(line)
            continue
        
        # 빈 줄이나 제목은 건너뛰기
        if not line.strip() or line.startswith('#'):
            result_lines.append(line)
            continue
        
        # 문장 단위로 분리
        sentences = split_sentences_safely(line)
        new_line_parts = []
        
        for sentence in sentences:
            if not sentence.strip():
                new_line_parts.append(sentence)
                continue
            
            # 참고문헌 찾기
            refs = find_references_in_sentence(sentence)
            
            if refs:
                # 원래 참고문헌 번호를 순차 번호로 매핑
                mapped_refs = []
                for ref in sorted(refs):
                    if ref not in ref_num_map:
                        ref_num_map[ref] = current_ref_num
                        current_ref_num += 1
                    mapped_refs.append(ref_num_map[ref])
                
                # 문장 끝에 참고문헌 번호 추가 (숫자 중간이 아닌 실제 문장 끝에만)
                sentence = sentence.rstrip()
                # 숫자로 끝나지 않는 경우에만 추가
                if sentence and not re.search(r'\d$', sentence):
                    # 문장 끝 구두점 확인
                    if sentence and sentence[-1] in '.!?。！？':
                        ref_str = '[' + ']['.join(map(str, sorted(set(mapped_refs)))) + ']'
                        sentence = sentence[:-1] + ref_str + sentence[-1]
                    else:
                        ref_str = '[' + ']['.join(map(str, sorted(set(mapped_refs)))) + ']'
                        sentence += ref_str
            
            new_line_parts.append(sentence)
        
        result_lines.append(''.join(new_line_parts))
    
    return '\n'.join(result_lines), current_ref_num

def main():
    # v1 파일 처리
    print("Processing v1 file...")
    with open('251212_thesis_update_cursor_v1.md', 'r', encoding='utf-8') as f:
        content_v1 = f.read()
    
    content_v1_new, next_ref_num = add_references_to_file(content_v1, start_ref_num=1)
    
    with open('251213_thesis_update_cursor_appendix_v1.md', 'w', encoding='utf-8') as f:
        f.write(content_v1_new)
    
    print(f"v1 file processed. Next reference number: {next_ref_num}")
    
    # v2 파일 처리
    print("Processing v2 file...")
    with open('251212_thesis_update_cursor_v2.md', 'r', encoding='utf-8') as f:
        content_v2 = f.read()
    
    content_v2_new, _ = add_references_to_file(content_v2, start_ref_num=next_ref_num)
    
    with open('251213_thesis_update_cursor_appendix_v2.md', 'w', encoding='utf-8') as f:
        f.write(content_v2_new)
    
    print("v2 file processed.")
    print("Done!")

if __name__ == '__main__':
    main()

