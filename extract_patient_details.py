#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Synthea 환자 상세 정보 추출 스크립트
5명의 환자를 랜덤으로 선택하여 모든 정보를 상세히 나열
"""

import json
import os
import random
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def extract_all_patient_info(fhir_file):
    """FHIR Bundle에서 모든 환자 정보 추출"""
    with open(fhir_file, 'r', encoding='utf-8') as f:
        bundle = json.load(f)
    
    patient_info = {
        'file_name': os.path.basename(fhir_file),
        'basic_info': {},
        'conditions': [],
        'medications': [],
        'allergies': [],
        'procedures': [],
        'observations': [],
        'vitals': [],
        'labs': [],
        'encounters': [],
        'immunizations': [],
        'care_plans': [],
        'diagnostic_reports': [],
        'family_history': [],
        'social_history': [],
        'extensions': [],
        'all_resources': []
    }
    
    if bundle.get('resourceType') != 'Bundle':
        return patient_info
    
    entries = bundle.get('entry', [])
    
    for entry in entries:
        resource = entry.get('resource', {})
        resource_type = resource.get('resourceType')
        
        # Patient 리소스 - 기본 정보
        if resource_type == 'Patient':
            patient_info['basic_info'] = {
                'id': resource.get('id'),
                'name': extract_name(resource.get('name', [])),
                'gender': resource.get('gender'),
                'birth_date': resource.get('birthDate'),
                'age': calculate_age(resource.get('birthDate')),
                'deceased': bool(resource.get('deceasedDateTime')),
                'deceased_date': resource.get('deceasedDateTime'),
                'marital_status': extract_marital_status(resource.get('maritalStatus')),
                'address': extract_address(resource.get('address', [])),
                'telecom': resource.get('telecom', []),
                'identifier': resource.get('identifier', []),
                'extension': resource.get('extension', []),
                'race': extract_race(resource.get('extension', [])),
                'ethnicity': extract_ethnicity(resource.get('extension', [])),
                'birth_sex': extract_birth_sex(resource.get('extension', [])),
                'mothers_maiden_name': extract_mothers_maiden_name(resource.get('extension', []))
            }
            patient_info['extensions'].extend(resource.get('extension', []))
        
        # Condition - 질환
        elif resource_type == 'Condition':
            condition = {
                'id': resource.get('id'),
                'code': extract_codeable_concept(resource.get('code', {})),
                'clinical_status': extract_codeable_concept(resource.get('clinicalStatus', {})),
                'verification_status': extract_codeable_concept(resource.get('verificationStatus', {})),
                'category': [extract_codeable_concept(c) for c in resource.get('category', [])],
                'severity': extract_codeable_concept(resource.get('severity', {})),
                'onset': resource.get('onsetDateTime') or resource.get('onsetPeriod') or resource.get('onsetAge'),
                'abatement': resource.get('abatementDateTime') or resource.get('abatementPeriod') or resource.get('abatementAge'),
                'recorded_date': resource.get('recordedDate'),
                'recorder': resource.get('recorder', {}).get('reference') if resource.get('recorder') else None,
                'evidence': resource.get('evidence', [])
            }
            patient_info['conditions'].append(condition)
        
        # MedicationRequest - 처방약
        elif resource_type == 'MedicationRequest':
            medication = {
                'id': resource.get('id'),
                'status': resource.get('status'),
                'intent': resource.get('intent'),
                'medication': extract_codeable_concept(resource.get('medicationCodeableConcept', {})),
                'dosage': extract_dosage(resource.get('dosageInstruction', [])),
                'authored_on': resource.get('authoredOn'),
                'requester': resource.get('requester', {}).get('reference') if resource.get('requester') else None,
                'reason_code': [extract_codeable_concept(rc) for rc in resource.get('reasonCode', [])],
                'category': [extract_codeable_concept(c) for c in resource.get('category', [])]
            }
            patient_info['medications'].append(medication)
        
        # AllergyIntolerance - 알레르기
        elif resource_type == 'AllergyIntolerance':
            allergy = {
                'id': resource.get('id'),
                'clinical_status': extract_codeable_concept(resource.get('clinicalStatus', {})),
                'verification_status': extract_codeable_concept(resource.get('verificationStatus', {})),
                'type': resource.get('type'),
                'category': resource.get('category', []),
                'criticality': resource.get('criticality'),
                'code': extract_codeable_concept(resource.get('code', {})),
                'onset': resource.get('onsetDateTime') or resource.get('onsetAge') or resource.get('onsetPeriod'),
                'recorded_date': resource.get('recordedDate'),
                'recorder': resource.get('recorder', {}).get('reference') if resource.get('recorder') else None,
                'reaction': resource.get('reaction', [])
            }
            patient_info['allergies'].append(allergy)
        
        # Procedure - 시술/수술
        elif resource_type == 'Procedure':
            procedure = {
                'id': resource.get('id'),
                'status': resource.get('status'),
                'code': extract_codeable_concept(resource.get('code', {})),
                'performed': resource.get('performedDateTime') or resource.get('performedPeriod') or resource.get('performedAge'),
                'reason_code': [extract_codeable_concept(rc) for rc in resource.get('reasonCode', [])],
                'body_site': [extract_codeable_concept(bs) for bs in resource.get('bodySite', [])],
                'outcome': extract_codeable_concept(resource.get('outcome', {})),
                'complication': [extract_codeable_concept(c) for c in resource.get('complication', [])],
                'follow_up': [extract_codeable_concept(fu) for fu in resource.get('followUp', [])]
            }
            patient_info['procedures'].append(procedure)
        
        # Observation - 관찰/바이탈/검사
        elif resource_type == 'Observation':
            obs = {
                'id': resource.get('id'),
                'status': resource.get('status'),
                'code': extract_codeable_concept(resource.get('code', {})),
                'value': extract_value(resource),
                'effective': resource.get('effectiveDateTime') or resource.get('effectivePeriod'),
                'category': [extract_codeable_concept(c) for c in resource.get('category', [])],
                'interpretation': [extract_codeable_concept(i) for i in resource.get('interpretation', [])],
                'body_site': extract_codeable_concept(resource.get('bodySite', {})),
                'method': extract_codeable_concept(resource.get('method', {})),
                'component': [extract_component(comp) for comp in resource.get('component', [])]
            }
            
            # 바이탈/검사/사회력 분류
            code_text = obs['code'].get('text', '').lower() if obs['code'] and obs['code'].get('text') else ''
            code_display = obs['code'].get('display', '').lower() if obs['code'] and obs['code'].get('display') else ''
            category_text = ' '.join([c.get('text', '').lower() if c and c.get('text') else '' for c in obs.get('category', [])])
            
            # 사회력 (흡연, 음주, 운동, 직업 등)
            if any(x in code_text or x in code_display or x in category_text for x in [
                'smoking', 'tobacco', 'cigarette', 'alcohol', 'drinking', 'exercise', 'physical activity',
                'occupation', 'employment', 'work', 'diet', 'nutrition', 'food', 'eating'
            ]):
                patient_info['social_history'].append(obs)
            # 바이탈
            elif any(x in code_text or x in code_display for x in ['blood pressure', 'heart rate', 'body temperature', 'respiratory rate', 'body height', 'body weight', 'bmi', 'oxygen saturation']):
                patient_info['vitals'].append(obs)
            # 검사
            elif any(x in code_text or x in code_display for x in ['laboratory', 'lab', 'hba1c', 'glucose', 'cholesterol', 'creatinine', 'hemoglobin', 'hematocrit']):
                patient_info['labs'].append(obs)
            else:
                patient_info['observations'].append(obs)
        
        # Encounter - 진료 기록
        elif resource_type == 'Encounter':
            encounter = {
                'id': resource.get('id'),
                'status': resource.get('status'),
                'class': resource.get('class', {}).get('code'),
                'type': [extract_codeable_concept(t) for t in resource.get('type', [])],
                'period': resource.get('period', {}),
                'reason_code': [extract_codeable_concept(rc) for rc in resource.get('reasonCode', [])],
                'diagnosis': resource.get('diagnosis', []),
                'hospitalization': resource.get('hospitalization', {})
            }
            patient_info['encounters'].append(encounter)
        
        # Immunization - 예방접종
        elif resource_type == 'Immunization':
            immunization = {
                'id': resource.get('id'),
                'status': resource.get('status'),
                'vaccine_code': extract_codeable_concept(resource.get('vaccineCode', {})),
                'occurrence': resource.get('occurrenceDateTime') or resource.get('occurrenceString'),
                'primary_source': resource.get('primarySource'),
                'lot_number': resource.get('lotNumber'),
                'expiration_date': resource.get('expirationDate')
            }
            patient_info['immunizations'].append(immunization)
        
        # CarePlan - 치료 계획
        elif resource_type == 'CarePlan':
            care_plan = {
                'id': resource.get('id'),
                'status': resource.get('status'),
                'intent': resource.get('intent'),
                'category': [extract_codeable_concept(c) for c in resource.get('category', [])],
                'description': resource.get('description'),
                'period': resource.get('period', {}),
                'activity': resource.get('activity', [])
            }
            patient_info['care_plans'].append(care_plan)
        
        # DiagnosticReport - 진단 보고서
        elif resource_type == 'DiagnosticReport':
            report = {
                'id': resource.get('id'),
                'status': resource.get('status'),
                'code': extract_codeable_concept(resource.get('code', {})),
                'effective': resource.get('effectiveDateTime') or resource.get('effectivePeriod'),
                'result': [r.get('reference') for r in resource.get('result', [])],
                'conclusion': resource.get('conclusion')
            }
            patient_info['diagnostic_reports'].append(report)
        
        # FamilyMemberHistory - 가족력
        elif resource_type == 'FamilyMemberHistory':
            family = {
                'id': resource.get('id'),
                'status': resource.get('status'),
                'patient': resource.get('patient', {}).get('reference'),
                'relationship': extract_codeable_concept(resource.get('relationship', {})),
                'sex': resource.get('sex', {}).get('code'),
                'born': resource.get('bornPeriod') or resource.get('bornDate') or resource.get('bornString'),
                'age': resource.get('ageAge') or resource.get('ageRange') or resource.get('ageString'),
                'deceased': resource.get('deceasedBoolean') or resource.get('deceasedAge') or resource.get('deceasedRange') or resource.get('deceasedDate') or resource.get('deceasedString'),
                'condition': resource.get('condition', [])
            }
            patient_info['family_history'].append(family)
        
        # 모든 리소스 타입 기록
        patient_info['all_resources'].append({
            'type': resource_type,
            'id': resource.get('id')
        })
    
    return patient_info

def extract_name(names):
    """이름 추출"""
    if not names:
        return None
    name = names[0]
    given = ' '.join(name.get('given', []))
    family = name.get('family', '')
    return f"{given} {family}".strip() if given or family else None

def extract_marital_status(marital_status):
    """혼인 상태 추출"""
    if not marital_status:
        return None
    return marital_status.get('coding', [{}])[0].get('display') or marital_status.get('text')

def extract_address(addresses):
    """주소 추출"""
    if not addresses:
        return None
    addr = addresses[0]
    return {
        'line': addr.get('line', []),
        'city': addr.get('city'),
        'state': addr.get('state'),
        'postal_code': addr.get('postalCode'),
        'country': addr.get('country')
    }

def extract_race(extensions):
    """인종 정보 추출"""
    for ext in extensions:
        if 'us-core-race' in ext.get('url', ''):
            for sub_ext in ext.get('extension', []):
                if sub_ext.get('url') == 'ombCategory':
                    return extract_codeable_concept(sub_ext.get('valueCoding', {}))
    return None

def extract_ethnicity(extensions):
    """민족 정보 추출"""
    for ext in extensions:
        if 'us-core-ethnicity' in ext.get('url', ''):
            for sub_ext in ext.get('extension', []):
                if sub_ext.get('url') == 'ombCategory':
                    return extract_codeable_concept(sub_ext.get('valueCoding', {}))
    return None

def extract_birth_sex(extensions):
    """출생 시 성별 추출"""
    for ext in extensions:
        if 'us-core-birthsex' in ext.get('url', ''):
            return ext.get('valueCode')
    return None

def extract_mothers_maiden_name(extensions):
    """어머니 결혼 전 성 추출"""
    for ext in extensions:
        if 'patient-mothersMaidenName' in ext.get('url', ''):
            return ext.get('valueString')
    return None

def extract_codeable_concept(concept):
    """CodeableConcept 추출"""
    if not concept:
        return None
    return {
        'text': concept.get('text'),
        'coding': concept.get('coding', []),
        'display': concept.get('coding', [{}])[0].get('display') if concept.get('coding') else None
    }

def extract_dosage(dosage_instructions):
    """용법 추출"""
    if not dosage_instructions:
        return None
    dosage = dosage_instructions[0]
    return {
        'text': dosage.get('text'),
        'timing': dosage.get('timing', {}),
        'route': extract_codeable_concept(dosage.get('route', {})),
        'dose': dosage.get('dose', {}),
        'frequency': dosage.get('timing', {}).get('repeat', {}).get('frequency') if dosage.get('timing', {}).get('repeat') else None
    }

def extract_value(observation):
    """Observation 값 추출"""
    if 'valueQuantity' in observation:
        qty = observation['valueQuantity']
        return {
            'type': 'quantity',
            'value': qty.get('value'),
            'unit': qty.get('unit'),
            'system': qty.get('system'),
            'code': qty.get('code')
        }
    elif 'valueCodeableConcept' in observation:
        return {
            'type': 'codeable_concept',
            'value': extract_codeable_concept(observation['valueCodeableConcept'])
        }
    elif 'valueString' in observation:
        return {'type': 'string', 'value': observation['valueString']}
    elif 'valueBoolean' in observation:
        return {'type': 'boolean', 'value': observation['valueBoolean']}
    elif 'valueDateTime' in observation:
        return {'type': 'dateTime', 'value': observation['valueDateTime']}
    return None

def extract_component(component):
    """Observation component 추출"""
    return {
        'code': extract_codeable_concept(component.get('code', {})),
        'value': extract_value(component)
    }

def calculate_age(birth_date_str):
    """나이 계산"""
    if not birth_date_str:
        return None
    try:
        birth_date = datetime.strptime(birth_date_str.split('T')[0], '%Y-%m-%d')
        age = datetime.now().year - birth_date.year
        if (datetime.now().month, datetime.now().day) < (birth_date.month, birth_date.day):
            age -= 1
        return age
    except:
        return None

def format_patient_info(patient_info):
    """환자 정보를 읽기 쉬운 형식으로 포맷팅"""
    output = []
    output.append("=" * 100)
    output.append(f"환자 ID: {patient_info['basic_info'].get('id', 'N/A')}")
    output.append(f"파일명: {patient_info['file_name']}")
    output.append("=" * 100)
    
    # 기본 정보
    basic = patient_info['basic_info']
    output.append("\n【기본 정보】")
    output.append(f"  이름: {basic.get('name', 'N/A')}")
    output.append(f"  성별: {basic.get('gender', 'N/A')}")
    output.append(f"  생년월일: {basic.get('birth_date', 'N/A')}")
    output.append(f"  나이: {basic.get('age', 'N/A')}세")
    output.append(f"  사망 여부: {'사망' if basic.get('deceased') else '생존'}")
    if basic.get('deceased_date'):
        output.append(f"  사망일: {basic.get('deceased_date')}")
    output.append(f"  혼인 상태: {basic.get('marital_status', 'N/A')}")
    if basic.get('race'):
        output.append(f"  인종: {basic.get('race').get('display', 'N/A')}")
    if basic.get('ethnicity'):
        output.append(f"  민족: {basic.get('ethnicity').get('display', 'N/A')}")
    if basic.get('birth_sex'):
        output.append(f"  출생 시 성별: {basic.get('birth_sex')}")
    if basic.get('mothers_maiden_name'):
        output.append(f"  어머니 결혼 전 성: {basic.get('mothers_maiden_name')}")
    if basic.get('address'):
        addr = basic['address']
        output.append(f"  주소: {', '.join(addr.get('line', []))}, {addr.get('city', '')}, {addr.get('state', '')} {addr.get('postal_code', '')}")
    
    # 질환
    if patient_info['conditions']:
        output.append(f"\n【질환】 ({len(patient_info['conditions'])}개)")
        for i, cond in enumerate(patient_info['conditions'], 1):
            cond_name = 'Unknown'
            if cond.get('code'):
                cond_name = cond['code'].get('display', cond['code'].get('text', 'Unknown'))
            output.append(f"  {i}. {cond_name}")
            if cond.get('clinical_status'):
                output.append(f"      상태: {cond['clinical_status'].get('display', 'N/A')}")
            if cond.get('onset'):
                output.append(f"      발병일: {cond['onset']}")
            if cond.get('severity'):
                output.append(f"      심각도: {cond['severity'].get('display', 'N/A')}")
    
    # 약물
    if patient_info['medications']:
        output.append(f"\n【처방약】 ({len(patient_info['medications'])}개)")
        for i, med in enumerate(patient_info['medications'], 1):
            med_name = 'Unknown'
            if med.get('medication'):
                med_name = med['medication'].get('display', med['medication'].get('text', 'Unknown'))
            output.append(f"  {i}. {med_name}")
            output.append(f"      상태: {med.get('status', 'N/A')}")
            if med.get('dosage'):
                output.append(f"      용법: {med['dosage'].get('text', 'N/A')}")
    
    # 알레르기
    if patient_info['allergies']:
        output.append(f"\n【알레르기】 ({len(patient_info['allergies'])}개)")
        for i, allergy in enumerate(patient_info['allergies'], 1):
            allergy_name = 'Unknown'
            if allergy.get('code'):
                allergy_name = allergy['code'].get('display', allergy['code'].get('text', 'Unknown'))
            output.append(f"  {i}. {allergy_name}")
            output.append(f"      심각도: {allergy.get('criticality', 'N/A')}")
            if allergy.get('reaction'):
                output.append(f"      반응: {', '.join([r.get('manifestation', [{}])[0].get('text', 'N/A') for r in allergy['reaction']])}")
    else:
        output.append("\n【알레르기】 없음")
    
    # 시술/수술
    if patient_info['procedures']:
        output.append(f"\n【시술/수술】 ({len(patient_info['procedures'])}개)")
        for i, proc in enumerate(patient_info['procedures'][:10], 1):  # 최대 10개만
            proc_name = 'Unknown'
            if proc.get('code'):
                proc_name = proc['code'].get('display', proc['code'].get('text', 'Unknown'))
            output.append(f"  {i}. {proc_name}")
            if proc.get('performed'):
                output.append(f"      시행일: {proc['performed']}")
    
    # 바이탈
    if patient_info['vitals']:
        output.append(f"\n【바이탈 사인】 ({len(patient_info['vitals'])}개)")
        for i, vital in enumerate(patient_info['vitals'][:10], 1):  # 최대 10개만
            code_display = 'Unknown'
            if vital.get('code'):
                code_display = vital['code'].get('display', vital['code'].get('text', 'Unknown'))
            value_str = format_value(vital.get('value'))
            output.append(f"  {i}. {code_display}: {value_str}")
            if vital.get('effective'):
                output.append(f"      측정일: {vital['effective']}")
    
    # 검사 결과
    if patient_info['labs']:
        output.append(f"\n【검사 결과】 ({len(patient_info['labs'])}개)")
        for i, lab in enumerate(patient_info['labs'][:10], 1):  # 최대 10개만
            code_display = 'Unknown'
            if lab.get('code'):
                code_display = lab['code'].get('display', lab['code'].get('text', 'Unknown'))
            value_str = format_value(lab.get('value'))
            output.append(f"  {i}. {code_display}: {value_str}")
            if lab.get('effective'):
                output.append(f"      검사일: {lab['effective']}")
    
    # 진료 기록
    if patient_info['encounters']:
        output.append(f"\n【진료 기록】 ({len(patient_info['encounters'])}개)")
        for i, enc in enumerate(patient_info['encounters'][:10], 1):  # 최대 10개만
            output.append(f"  {i}. 유형: {enc.get('class', 'N/A')}")
            if enc.get('type'):
                output.append(f"      종류: {', '.join([t.get('display', 'N/A') for t in enc['type']])}")
            if enc.get('period'):
                output.append(f"      기간: {enc['period'].get('start', 'N/A')} ~ {enc['period'].get('end', 'N/A')}")
    
    # 예방접종
    if patient_info['immunizations']:
        output.append(f"\n【예방접종】 ({len(patient_info['immunizations'])}개)")
        for i, imm in enumerate(patient_info['immunizations'][:10], 1):
            vaccine_name = 'Unknown'
            if imm.get('vaccine_code'):
                vaccine_name = imm['vaccine_code'].get('display', imm['vaccine_code'].get('text', 'Unknown'))
            output.append(f"  {i}. {vaccine_name}")
            if imm.get('occurrence'):
                output.append(f"      접종일: {imm['occurrence']}")
    
    # 사회력 (흡연, 음주, 운동, 직업, 식습관 등)
    if patient_info['social_history']:
        output.append(f"\n【사회력】 ({len(patient_info['social_history'])}개)")
        for i, social in enumerate(patient_info['social_history'], 1):
            code_display = 'Unknown'
            if social.get('code'):
                code_display = social['code'].get('display', social['code'].get('text', 'Unknown'))
            value_str = format_value(social.get('value'))
            output.append(f"  {i}. {code_display}: {value_str}")
            if social.get('effective'):
                output.append(f"      기록일: {social['effective']}")
    else:
        output.append("\n【사회력】 없음 (흡연, 음주, 운동, 직업, 식습관 등)")
    
    # 가족력
    if patient_info['family_history']:
        output.append(f"\n【가족력】 ({len(patient_info['family_history'])}개)")
        for i, family in enumerate(patient_info['family_history'], 1):
            rel = 'N/A'
            if family.get('relationship'):
                rel = family['relationship'].get('display', 'N/A')
            output.append(f"  {i}. 관계: {rel}")
            if family.get('condition'):
                for cond in family['condition']:
                    cond_code = extract_codeable_concept(cond.get('code', {}))
                    output.append(f"      질환: {cond_code.get('display', 'N/A') if cond_code else 'N/A'}")
    else:
        output.append("\n【가족력】 없음")
    
    # 치료 계획
    if patient_info['care_plans']:
        output.append(f"\n【치료 계획】 ({len(patient_info['care_plans'])}개)")
        for i, plan in enumerate(patient_info['care_plans'], 1):
            output.append(f"  {i}. {plan.get('description', 'N/A')}")
            output.append(f"      상태: {plan.get('status', 'N/A')}")
    
    # 진단 보고서
    if patient_info['diagnostic_reports']:
        output.append(f"\n【진단 보고서】 ({len(patient_info['diagnostic_reports'])}개)")
        for i, report in enumerate(patient_info['diagnostic_reports'][:5], 1):
            report_name = 'Unknown'
            if report.get('code'):
                report_name = report['code'].get('display', report['code'].get('text', 'Unknown'))
            output.append(f"  {i}. {report_name}")
            if report.get('conclusion'):
                output.append(f"      결론: {report['conclusion']}")
    
    # 기타 관찰
    if patient_info['observations']:
        output.append(f"\n【기타 관찰】 ({len(patient_info['observations'])}개)")
        for i, obs in enumerate(patient_info['observations'][:10], 1):
            code_display = 'Unknown'
            if obs.get('code'):
                code_display = obs['code'].get('display', obs['code'].get('text', 'Unknown'))
            value_str = format_value(obs.get('value'))
            output.append(f"  {i}. {code_display}: {value_str}")
    
    # 리소스 통계
    resource_counts = defaultdict(int)
    for res in patient_info['all_resources']:
        resource_counts[res['type']] += 1
    
    output.append(f"\n【리소스 통계】")
    for res_type, count in sorted(resource_counts.items()):
        output.append(f"  {res_type}: {count}개")
    
    output.append("\n" + "=" * 100 + "\n")
    
    return "\n".join(output)

def format_value(value):
    """값 포맷팅"""
    if not value:
        return "N/A"
    if isinstance(value, dict):
        if value.get('type') == 'quantity':
            return f"{value.get('value', 'N/A')} {value.get('unit', '')}"
        elif value.get('type') == 'codeable_concept':
            return value.get('value', {}).get('display', 'N/A') if isinstance(value.get('value'), dict) else 'N/A'
        elif value.get('type') == 'string':
            return value.get('value', 'N/A')
        elif value.get('type') == 'boolean':
            return '예' if value.get('value') else '아니오'
        else:
            return str(value.get('value', 'N/A'))
    return str(value)

def main():
    """메인 함수"""
    import sys
    import io
    # Windows 콘솔 인코딩 설정
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    base_dir = Path(__file__).parent
    fhir_dir = base_dir / "synthea" / "output" / "fhir"
    
    # FHIR 파일 목록 가져오기 (practitioner, hospital, organization 제외)
    fhir_files = [
        f for f in fhir_dir.glob("*.json")
        if not any(x in f.name.lower() for x in ['practitioner', 'hospital', 'organization'])
    ]
    
    if not fhir_files:
        print("FHIR 파일을 찾을 수 없습니다.")
        return
    
    # 5명 랜덤 선택
    selected_files = random.sample(fhir_files, min(5, len(fhir_files)))
    
    print(f"\n총 {len(fhir_files)}명의 환자 중 5명을 랜덤으로 선택했습니다.\n")
    
    all_output = []
    for i, fhir_file in enumerate(selected_files, 1):
        print(f"[{i}/5] 처리 중: {fhir_file.name}...")
        try:
            patient_info = extract_all_patient_info(str(fhir_file))
            formatted = format_patient_info(patient_info)
            all_output.append(formatted)
        except Exception as e:
            print(f"  오류 발생: {e}")
            import traceback
            traceback.print_exc()
    
    # 결과 출력
    print("\n" + "=" * 100)
    print("환자 상세 정보")
    print("=" * 100)
    print("\n".join(all_output))
    
    # 파일로 저장
    output_file = base_dir / "patient_details_report.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(all_output))
    
    print(f"\n결과가 '{output_file}'에 저장되었습니다.")

if __name__ == "__main__":
    main()

