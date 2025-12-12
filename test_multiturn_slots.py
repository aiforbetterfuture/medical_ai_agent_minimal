"""멀티턴 슬롯 추출 파이프라인 간이 테스트 (AI Agent 모드 전 단계)"""

from extraction.slot_extractor import SlotExtractor


def run_test():
    extractor = SlotExtractor(
        use_medcat2=True,
        use_multilingual=True,
        use_neural_translation=False,  # 사전 기반 우선
        use_dict_translation=True,
    )

    user_turns = [
        "55세 남성입니다.",
        "고혈압 약 먹고 있고 당뇨도 있어요.",
        "메트포르민 하루 두 번 먹습니다.",
        "가끔 가슴이 답답하고 어지럽습니다.",
        "혈압은 140/90 정도 나옵니다.",
    ]

    agg = {
        "conditions": [],
        "symptoms": [],
        "medications": [],
        "vitals": [],
        "labs": [],
        "demographics": {},
        "pregnancy": False,
    }

    for i, text in enumerate(user_turns, 1):
        slots = extractor.extract(text)
        for k in ["conditions", "symptoms", "medications", "vitals", "labs"]:
            agg[k].extend(slots.get(k, []))
        agg["demographics"].update(slots.get("demographics", {}))

        print(f"Turn {i}: {text}")
        print(
            "  conditions:",
            [c.get("name") for c in slots.get("conditions", [])],
        )
        print(
            "  symptoms:",
            [s.get("name") for s in slots.get("symptoms", [])],
        )
        print(
            "  medications:",
            [m.get("name") for m in slots.get("medications", [])],
        )
        print(
            "  vitals:",
            [(v.get("name"), v.get("value"), v.get("unit")) for v in slots.get("vitals", [])],
        )
        print(
            "  labs:",
            [(l.get("name"), l.get("value"), l.get("unit")) for l in slots.get("labs", [])],
        )
        print()

    # 집계 결과 (중복 제거 없이 단순 합산)
    print("=== Aggregated ===")
    print("demographics:", agg["demographics"])
    print("conditions:", {c.get("name") for c in agg["conditions"]})
    print("symptoms:", {s.get("name") for s in agg["symptoms"]})
    print("medications:", {m.get("name") for m in agg["medications"]})
    print("vitals:", agg["vitals"])
    print("labs:", agg["labs"])


if __name__ == "__main__":
    run_test()

