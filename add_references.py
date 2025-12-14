#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
참고문헌 번호 추가 스크립트
251212_thesis_update_cursor_v1.md와 v2.md 파일에 참고문헌 번호를 추가합니다.
"""

import re
from typing import List, Tuple, Dict, Set

# 참고문헌 매핑 (키워드/패턴 -> 참고문헌 번호 리스트)
# 참고: 251213_thesis_final_v1.md의 참고문헌 번호를 그대로 사용
REF_MAPPINGS = {
    # RAG 관련
    (r'\bRAG\b', r'검색.*증강.*생성'): [1, 15],
    (r'Retrieval-Augmented Generation',): [1, 15],
    (r'Lewis.*2020',): [1],
    (r'검색 증강 생성',): [1, 15],
    
    # MedCAT2
    (r'MedCAT2', r'MedCAT', r'Kraljevic'): [7],
    (r'의학.*개념.*주석', r'의학.*엔티티.*추출'): [7],
    
    # UMLS
    (r'UMLS', r'Unified Medical Language System'): [31],
    (r'CUI', r'표준.*개념'): [31],
    
    # LangGraph
    (r'LangGraph',): [9, 10, 11],
    (r'LangChain', r'Chase'): [9],
    (r'상태.*기반.*워크플로우', r'순환.*아키텍처'): [9, 10],
    
    # Self-Refine
    (r'Self-Refine', r'Madaan.*2023', r'자기개선'): [12],
    (r'품질.*평가.*재작성',): [12],
    
    # CRAG
    (r'CRAG', r'Corrective RAG', r'Yan.*2024'): [13],
    (r'재검색.*품질',): [13],
    
    # RAGAS
    (r'RAGAS', r'Es.*2023'): [14],
    (r'Faithfulness', r'Answer Relevance'): [14],
    (r'근거.*충실성', r'정답.*관련성'): [14],
    
    # BM25
    (r'BM25', r'Robertson.*2009', r'Zaragoza'): [16],
    (r'키워드.*검색', r'TF-IDF'): [16],
    
    # RRF
    (r'RRF', r'Reciprocal Rank Fusion', r'Cormack.*2009'): [17],
    (r'상호.*순위.*융합',): [17],
    
    # FAISS
    (r'FAISS', r'Johnson.*2019'): [18],
    (r'벡터.*검색', r'유사도.*검색'): [18],
    
    # Active Retrieval
    (r'Active Retrieval', r'Jiang.*2023', r'능동적.*검색'): [24],
    (r'동적.*k', r'질의.*복잡도'): [24],
    
    # Synthea
    (r'Synthea', r'Walonoski.*2018', r'가상.*환자'): [32],
    (r'생성.*환자', r'합성.*환자'): [32],
    
    # 의료 LLM
    (r'Med-PaLM', r'메드팜', r'Singhal.*2023'): [8],
    (r'의료.*LLM', r'임상.*지식'): [8],
    
    # 통계
    (r'Cohen.*1988', r'Cohen\'s d'): [39],
    (r'Faul.*2007', r'G\*Power'): [40],
    (r'p < 0\.001', r'통계적.*유의성', r'통계적.*검증'): [39, 40],
    (r't-test',): [39, 40],
    
    # 기타
    (r'BioBERT', r'Lee.*2020'): [5],
    (r'GPT-4', r'Achiam.*2023'): [38],
    (r'Brown.*2020', r'Language Models are Few-Shot Learners'): [37],
    (r'Wei.*2022', r'Chain-of-Thought'): [36],
    (r'Park.*2014', r'KoNLPy'): [34],
    (r'대한고혈압학회.*2022',): [28],
    (r'대한당뇨병학회.*2023',): [29],
    (r'WHO', r'World Health Organization'): [30],
    (r'Perplexity',): [37],
}

def find_references_in_sentence(sentence: str) -> List[int]:
    """문장에서 참고문헌 키워드를 찾아 참고문헌 번호 리스트 반환"""
    found_refs = set()
    
    for patterns, refs in REF_MAPPINGS.items():
        # patterns는 튜플이거나 단일 문자열
        if isinstance(patterns, tuple):
            patterns_list = patterns
        else:
            patterns_list = (patterns,)
        
        # 패턴 중 하나라도 매칭되면 참고문헌 추가
        for pattern in patterns_list:
            if re.search(pattern, sentence, re.IGNORECASE | re.UNICODE):
                found_refs.update(refs)
                break
    
    return sorted(list(found_refs))

def add_references_to_file(content: str, start_ref_num: int = 1) -> Tuple[str, int]:
    """파일 내용에 참고문헌 번호 추가"""
    lines = content.split('\n')
    result_lines = []
    current_ref_num = start_ref_num
    ref_counter = {}  # 참고문헌 번호 카운터
    
    for line in lines:
        # 코드 블록이나 다이어그램 주석은 건너뛰기
        if line.strip().startswith('```') or line.strip().startswith('**[다이어그램') or line.strip().startswith('**['):
            result_lines.append(line)
            continue
        
        # 이미 참고문헌 번호가 있는 줄은 건너뛰기
        if re.search(r'\[\d+\]', line):
            result_lines.append(line)
            continue
        
        # 빈 줄이나 제목은 건너뛰기
        if not line.strip() or line.startswith('#') or line.startswith('##') or line.startswith('###'):
            result_lines.append(line)
            continue
        
        # 문장 단위로 분리 (마침표, 물음표, 느낌표 기준)
        sentences = re.split(r'([.!?。！？]\s*)', line)
        new_line_parts = []
        
        for i in range(0, len(sentences), 2):
            if i >= len(sentences):
                break
            
            sentence = sentences[i]
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]
            
            if not sentence.strip():
                new_line_parts.append(sentence)
                continue
            
            # 참고문헌 찾기
            refs = find_references_in_sentence(sentence)
            
            if refs:
                # 참고문헌 번호 매핑 (전역 번호로 변환)
                mapped_refs = []
                for ref in refs:
                    if ref not in ref_counter:
                        ref_counter[ref] = current_ref_num
                        current_ref_num += 1
                    mapped_refs.append(ref_counter[ref])
                
                # 문장 끝에 참고문헌 번호 추가
                sentence = sentence.rstrip()
                if sentence and not sentence.endswith(('[', ']')):
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

