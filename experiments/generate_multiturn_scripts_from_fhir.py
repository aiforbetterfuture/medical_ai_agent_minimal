"""
Synthea 프로필 카드에서 5턴 멀티턴 질문 스크립트 자동 생성
80명 환자에 대해 각각 5턴 질문 스크립트 생성
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any
import random

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 상대 경로 import
sys.path.insert(0, str(Path(__file__).parent.parent))

from extraction.synthea_slot_builder import SyntheaSlotBuilder
from extraction.synthea_script_generator import SyntheaScriptGenerator


def load_profile_card(profile_path: Path) -> Dict:
    """프로필 카드 로드"""
    with open(profile_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_script_for_patient(
    patient_id: str,
    profile_card: Dict,
    slot_builder: SyntheaSlotBuilder,
    script_generator: SyntheaScriptGenerator
) -> Dict[str, Any]:
    """환자 1명에 대한 5턴 스크립트 생성"""
    # 슬롯 추출
    slots = slot_builder.build_slots(profile_card)
    
    # 5턴 질문 생성
    questions = script_generator.generate_5turn_script(slots)
    
    return {
        "patient_id": patient_id,
        "slots": slots,
        "turns": [
            {
                "turn_id": i + 1,
                "question": q
            }
            for i, q in enumerate(questions)
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Synthea 프로필 카드에서 5턴 멀티턴 스크립트 생성")
    parser.add_argument(
        "--profile_cards_dir",
        type=str,
        default="data/patients/profile_cards",
        help="프로필 카드 디렉토리"
    )
    parser.add_argument(
        "--out",
        type=str,
        default="data/multiturn_scripts/scripts_5turn.jsonl",
        help="출력 파일 경로 (jsonl 형식)"
    )
    parser.add_argument(
        "--max_patients",
        type=int,
        default=80,
        help="최대 환자 수"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="랜덤 시드"
    )
    
    args = parser.parse_args()
    
    # 시드 설정
    random.seed(args.seed)
    
    # 디렉토리 생성
    profile_cards_dir = Path(args.profile_cards_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 초기화
    slot_builder = SyntheaSlotBuilder()
    script_generator = SyntheaScriptGenerator()
    
    # 프로필 카드 파일 찾기
    profile_files = sorted(profile_cards_dir.glob("SYN_*.json"))[:args.max_patients]
    
    if not profile_files:
        print(f"❌ 프로필 카드 파일을 찾을 수 없습니다: {profile_cards_dir}")
        return
    
    print(f"📋 {len(profile_files)}명의 환자에 대해 스크립트 생성 시작...")
    
    # 각 환자에 대해 스크립트 생성
    generated_count = 0
    with open(out_path, 'w', encoding='utf-8') as f:
        for profile_file in profile_files:
            try:
                patient_id = profile_file.stem  # SYN_0001
                profile_card = load_profile_card(profile_file)
                
                script = generate_script_for_patient(
                    patient_id,
                    profile_card,
                    slot_builder,
                    script_generator
                )
                
                # JSONL 형식으로 저장
                f.write(json.dumps(script, ensure_ascii=False) + '\n')
                generated_count += 1
                
                if generated_count % 10 == 0:
                    print(f"  ✓ {generated_count}명 완료...")
            
            except Exception as e:
                print(f"  ⚠ {profile_file.name} 처리 중 오류: {e}")
                continue
    
    print(f"\n✅ 완료: {generated_count}명의 환자 스크립트 생성")
    print(f"📁 출력 파일: {out_path}")
    
    # 샘플 출력
    if generated_count > 0:
        print("\n📝 샘플 스크립트 (첫 번째 환자):")
        with open(out_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            sample = json.loads(first_line)
            print(f"  환자 ID: {sample['patient_id']}")
            print(f"  Primary Condition: {sample['slots'].get('primary_condition', 'N/A')}")
            for turn in sample['turns']:
                print(f"  Turn {turn['turn_id']}: {turn['question'][:60]}...")


if __name__ == "__main__":
    main()

