"""
Synthea FHIR → Profile Card 변환 스크립트
80명의 Synthea 환자 데이터를 실험용 Profile Card로 변환
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import random

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def load_synthea_fhir(fhir_path: str) -> Dict:
    """Synthea FHIR Bundle 로드"""
    with open(fhir_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_patient_demographics(bundle: Dict) -> Dict:
    """환자 인구통계 정보 추출"""
    patient_resource = next(
        (entry['resource'] for entry in bundle.get('entry', [])
         if entry['resource']['resourceType'] == 'Patient'),
        None
    )

    if not patient_resource:
        raise ValueError("Patient resource not found in bundle")

    birth_date = patient_resource.get('birthDate', '')
    birth_year = int(birth_date.split('-')[0]) if birth_date else 1960
    age_years = datetime.now().year - birth_year

    gender = patient_resource.get('gender', 'unknown')
    sex = 'M' if gender == 'male' else 'F'

    return {
        "name_masked": f"Patient_{patient_resource['id']}",
        "sex": sex,
        "age_years": age_years,
        "birth_year": birth_year,
        "language": "ko",
        "country": "KR",
        "region": "Seoul",
        "height_cm": 170,  # Default
        "weight_kg": 70,   # Default
        "bmi": 24.2,       # Default
        "smoking_status": "never",
        "pregnant": False
    }


def extract_conditions(bundle: Dict) -> List[Dict]:
    """질환 정보 추출"""
    conditions = []

    for entry in bundle.get('entry', []):
        resource = entry.get('resource', {})
        if resource.get('resourceType') == 'Condition':
            condition_info = {
                "name": resource.get('code', {}).get('text', 'Unknown'),
                "icd10": "",
                "snomed": "",
                "status": resource.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', 'active'),
                "onset_date": resource.get('onsetDateTime', '')[:10],
                "last_updated": datetime.now().isoformat()[:10],
                "is_chronic": True
            }

            # SNOMED code 추출
            for coding in resource.get('code', {}).get('coding', []):
                if 'snomed' in coding.get('system', '').lower():
                    condition_info['snomed'] = coding.get('code', '')

            conditions.append(condition_info)

    return conditions[:2]  # 최대 2개만


def extract_medications(bundle: Dict) -> List[Dict]:
    """약물 정보 추출"""
    medications = []

    for entry in bundle.get('entry', []):
        resource = entry.get('resource', {})
        if resource.get('resourceType') == 'MedicationRequest':
            med_info = {
                "name": resource.get('medicationCodeableConcept', {}).get('text', 'Unknown'),
                "rxnorm": "",
                "dose": "Unknown",
                "frequency": "QD",
                "route": "PO",
                "status": resource.get('status', 'active'),
                "start_date": resource.get('authoredOn', '')[:10]
            }

            # RxNorm code 추출
            for coding in resource.get('medicationCodeableConcept', {}).get('coding', []):
                if 'rxnorm' in coding.get('system', '').lower():
                    med_info['rxnorm'] = coding.get('code', '')

            medications.append(med_info)

    return medications[:2]  # 최대 2개만


def extract_allergies(bundle: Dict) -> List[Dict]:
    """알레르기 정보 추출"""
    allergies = []

    for entry in bundle.get('entry', []):
        resource = entry.get('resource', {})
        if resource.get('resourceType') == 'AllergyIntolerance':
            allergy_info = {
                "substance": resource.get('code', {}).get('text', 'Unknown'),
                "reaction": "rash",  # Default
                "severity": resource.get('criticality', 'mild'),
                "status": resource.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', 'active')
            }
            allergies.append(allergy_info)

    return allergies[:1]  # 최대 1개


def extract_vitals(bundle: Dict) -> List[Dict]:
    """바이탈 정보 추출"""
    vitals = []

    for entry in bundle.get('entry', []):
        resource = entry.get('resource', {})
        if resource.get('resourceType') == 'Observation':
            code = resource.get('code', {}).get('text', '')

            if 'blood pressure' in code.lower():
                components = resource.get('component', [])
                if len(components) >= 2:
                    systolic = components[0].get('valueQuantity', {}).get('value', 120)
                    diastolic = components[1].get('valueQuantity', {}).get('value', 80)
                    vitals.append({
                        "type": "blood_pressure",
                        "value": f"{systolic}/{diastolic}",
                        "unit": "mmHg",
                        "measured_at": resource.get('effectiveDateTime', datetime.now().isoformat())
                    })

            elif 'heart rate' in code.lower():
                vitals.append({
                    "type": "heart_rate",
                    "value": resource.get('valueQuantity', {}).get('value', 75),
                    "unit": "bpm",
                    "measured_at": resource.get('effectiveDateTime', datetime.now().isoformat())
                })

    return vitals[:2]  # 최대 2개


def extract_labs(bundle: Dict) -> List[Dict]:
    """검사 결과 추출"""
    labs = []

    for entry in bundle.get('entry', []):
        resource = entry.get('resource', {})
        if resource.get('resourceType') == 'Observation':
            code = resource.get('code', {}).get('text', '')

            if 'hba1c' in code.lower() or 'hemoglobin a1c' in code.lower():
                value = resource.get('valueQuantity', {}).get('value', 6.0)
                labs.append({
                    "name": "HbA1c",
                    "value": value,
                    "unit": "%",
                    "measured_at": resource.get('effectiveDateTime', datetime.now().isoformat()),
                    "flag": "high" if value > 7.0 else "normal"
                })

    return labs[:2]  # 최대 2개


def generate_chief_complaint(conditions: List[Dict], vitals: List[Dict]) -> Dict:
    """주호소 생성"""
    complaints = [
        {"complaint": "가슴 답답함", "duration": "3일", "severity": "moderate", "context": "운동 후 악화"},
        {"complaint": "두통", "duration": "2일", "severity": "mild", "context": "아침에 심함"},
        {"complaint": "숨참", "duration": "1주일", "severity": "severe", "context": "계단 오를 때"},
        {"complaint": "복통", "duration": "1일", "severity": "moderate", "context": "식후 악화"},
        {"complaint": "어지러움", "duration": "5일", "severity": "mild", "context": "일어날 때"}
    ]

    return random.choice(complaints)


def generate_turn_injection_fields(chief_complaint: Dict, conditions: List[Dict],
                                   medications: List[Dict], vitals: List[Dict]) -> Dict:
    """턴별 주입 필드 생성"""
    # T3 업데이트용 새로운 바이탈
    new_vital = {
        "type": "blood_pressure",
        "value": "170/105",
        "unit": "mmHg"
    } if vitals and vitals[0]['type'] == 'blood_pressure' else {
        "type": "heart_rate",
        "value": 105,
        "unit": "bpm"
    }

    # T4 마이너 추가
    otc_options = [
        "어제 이부프로펜 1회 복용함",
        "진통제를 먹었음",
        "감기약을 복용함",
        "두통약을 먹었음"
    ]

    return {
        "T1_must_include": ["age_years", "sex", "conditions[0..1]", "medications[0..1]"],
        "T2_must_omit": ["medications[0]"] if medications else [],
        "T3_update_event": {
            "type": "new_measurement",
            "payload": {
                "vital": new_vital,
                "symptom_change": "어지러움이 추가됨"
            }
        },
        "T4_minor_addition": {
            "type": "otc_or_behavior",
            "payload": random.choice(otc_options)
        }
    }


def create_profile_card(patient_id: str, bundle: Dict) -> Dict:
    """Profile Card 생성"""
    demographics = extract_patient_demographics(bundle)
    conditions = extract_conditions(bundle)
    medications = extract_medications(bundle)
    allergies = extract_allergies(bundle)
    vitals = extract_vitals(bundle)
    labs = extract_labs(bundle)
    chief_complaint = generate_chief_complaint(conditions, vitals)

    profile_card = {
        "schema_version": "synthea_profile_card.v1",
        "patient_id": patient_id,
        "source": {
            "generator": "Synthea",
            "synthea_version": "3.x.x",
            "generation_seed": 123456,
            "export_format": "FHIR",
            "export_timestamp_utc": datetime.now().isoformat()
        },
        "demographics": demographics,
        "clinical_summary": {
            "chief_complaint_seed": chief_complaint,
            "conditions": conditions,
            "medications": medications,
            "allergies": allergies,
            "vitals_recent": vitals,
            "labs_recent": labs
        },
        "turn_injection_fields": generate_turn_injection_fields(
            chief_complaint, conditions, medications, vitals
        ),
        "notes_for_generation": {
            "korean_aliases": {
                "sex": {"M": "남성", "F": "여성"},
                "conditions": {
                    "Type 2 Diabetes Mellitus": "당뇨병",
                    "Hypertension": "고혈압",
                    "Asthma": "천식",
                    "COPD": "만성폐쇄성폐질환"
                }
            },
            "safety_constraints": [
                "진단 단정 금지",
                "응급 신호/주의 문구 포함 요구 가능(턴5)"
            ]
        }
    }

    return profile_card


def main():
    """메인 실행 함수"""
    # 경로 설정
    base_dir = Path(__file__).parent.parent
    synthea_output_dir = base_dir / "synthea" / "output" / "fhir"
    profile_cards_dir = base_dir / "data" / "patients" / "profile_cards"

    # Profile Cards 디렉토리 생성
    profile_cards_dir.mkdir(parents=True, exist_ok=True)

    # Synthea FHIR 파일이 없으면 샘플 생성
    if not synthea_output_dir.exists() or not list(synthea_output_dir.glob("*.json")):
        print("WARNING: Synthea FHIR files not found. Creating sample profile cards...")

        # 샘플 Profile Card 80개 생성
        for i in range(1, 81):
            patient_id = f"SYN_{i:04d}"

            # 기본 샘플 데이터
            sample_bundle = {
                "resourceType": "Bundle",
                "entry": [
                    {
                        "resource": {
                            "resourceType": "Patient",
                            "id": patient_id,
                            "gender": random.choice(["male", "female"]),
                            "birthDate": f"{random.randint(1940, 2000)}-01-01"
                        }
                    }
                ]
            }

            profile_card = create_profile_card(patient_id, sample_bundle)

            # 저장
            output_path = profile_cards_dir / f"{patient_id}.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(profile_card, f, ensure_ascii=False, indent=2)

            print(f"Created: {output_path}")

    else:
        # Synthea FHIR 파일 처리
        fhir_files = sorted(synthea_output_dir.glob("*.json"))[:80]

        for idx, fhir_file in enumerate(fhir_files, start=1):
            patient_id = f"SYN_{idx:04d}"

            try:
                bundle = load_synthea_fhir(str(fhir_file))
                profile_card = create_profile_card(patient_id, bundle)

                # 저장
                output_path = profile_cards_dir / f"{patient_id}.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(profile_card, f, ensure_ascii=False, indent=2)

                print(f"Converted: {fhir_file.name} -> {patient_id}.json")

            except Exception as e:
                print(f"ERROR processing {fhir_file.name}: {e}")

    print(f"\nCompleted! Generated {len(list(profile_cards_dir.glob('*.json')))} profile cards")


if __name__ == "__main__":
    main()
