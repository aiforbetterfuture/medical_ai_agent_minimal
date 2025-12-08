"""
데이터 스키마 정의 (Pydantic)
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Condition:
    """질환"""
    name: str
    cui: str = ""
    confirmed: bool = True
    timestamp: Optional[float] = None


@dataclass
class Symptom:
    """증상"""
    name: str
    negated: bool = False
    cui: str = ""
    timestamp: Optional[float] = None


@dataclass
class ValueWithUnit:
    """수치 (vitals, labs)"""
    name: str
    value: float
    unit: str = ""
    timestamp: Optional[float] = None


@dataclass
class Medication:
    """약물"""
    name: str
    cui: str = ""
    dose: Optional[str] = None
    frequency: Optional[str] = None
    timestamp: Optional[float] = None


@dataclass
class Profile:
    """환자 프로필"""
    conditions: List[Condition] = field(default_factory=list)
    symptoms: List[Symptom] = field(default_factory=list)
    vitals: List[ValueWithUnit] = field(default_factory=list)
    labs: List[ValueWithUnit] = field(default_factory=list)
    meds: List[Medication] = field(default_factory=list)
    demographics: Dict[str, Any] = field(default_factory=dict)

