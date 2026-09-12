# -*- coding: utf-8 -*-
"""
서·논술형 문항 자동 채점 웹앱 (Streamlit)
- 세트1: 사회적 촉진/억제
- 세트2: 정전기
- 세트3: 인공지능 예술

채점 원칙
1) 조건에서 허용한 방법의 '의미'가 담기면 용어 없이도 인정 (term_required=False인 required_groups)
2) 특정 설명 방법을 선택했으면 그 방법의 특성(예: 비교와 대조 -> 두 대상의 대비)이 실제로 드러나야 함
3) 선택지(빈칸/요소)가 있는 문항은 인정 가능한 모범 답안을 모두 화면에 제시
4) 오개념 방지: 반대 개념의 특성 키워드가 등장하면 '오답 의심'으로 별도 표시
5) 결론 방향 확인: is_conclusion=True로 표시된 항목은 결론 방향이 뒤집히면 명확히 감점
"""

import streamlit as st

# =========================================================
# 0. 공통 유틸
# =========================================================

def norm(text: str) -> str:
    """공백 제거 등 간단 정규화"""
    if text is None:
        return ""
    return text.replace(" ", "").replace("\n", " ").strip()


def group_hit(text: str, group: list) -> bool:
    """키워드 그룹 중 하나라도 포함되면 True (공백 무시 비교)"""
    t = norm(text)
    return any(norm(kw) in t for kw in group)


def groups_status(text: str, groups: list):
    """여러 그룹에 대해 각각 매칭 여부 리스트 반환"""
    return [group_hit(text, g) for g in groups]


def score_from_groups(text: str, required_groups: list, forbidden_groups: list):
    """
    required_groups: [[동의어들], [동의어들], ...]  -> 각 그룹 중 1개 이상 매칭되어야 만족
    forbidden_groups: [[반대개념 키워드들], ...] -> 매칭되면 오개념 의심
    반환: (충족 그룹 수, 전체 그룹 수, 오개념 여부, 상세 리스트)
    """
    req_status = groups_status(text, required_groups) if required_groups else []
    forb_status = groups_status(text, forbidden_groups) if forbidden_groups else []
    hit_count = sum(req_status)
    total = len(required_groups)
    misconception = any(forb_status)
    return hit_count, total, misconception, req_status, forb_status


def verdict_label(hit, total, misconception):
    if total == 0:
        base = "PASS"
    elif hit == total and not misconception:
        base = "PASS"
    elif hit == 0:
        base = "FAIL"
    else:
        base = "PARTIAL"
    if misconception:
        return f"{base} (오개념 의심 ⚠)"
    return base


# =========================================================
# 1. 세트별 채점 기준 (RUBRIC)
# =========================================================

RUBRIC = {

    # =====================================================
    # 세트 1 : 사회적 촉진 / 사회적 억제
    # =====================================================
    "세트1": {
        "title": "사회적 촉진과 사회적 억제",
        "q1_blank": {
            "label": "[서논술형 1] 표 빈칸 채우기",
            "items": {
                "⊙ (과제의 특성)": {
                    "required_groups": [
                        ["쉬운", "비교적쉬운", "쉽", "간단한", "취미", "노력이필요없는"],
                    ],
                    "forbidden_groups": [
                        ["어렵", "도전이필요"],
                    ],
                    "is_conclusion": False,
                    "model_answers": [
                        "비교적 쉬운 과제",
                        "큰 노력을 들일 필요가 없는 과제(취미 생활 등)",
                    ],
                },
                "ⓒ (효율적인 환경 및 방법)": {
                    "required_groups": [
                        ["혼자"],
                        ["연습", "익숙해질때까지", "익숙"],
                    ],
                    "forbidden_groups": [
                        ["함께", "모임", "커피숍", "도서관"],
                    ],
                    "is_conclusion": False,
                    "model_answers": [
                        "충분히 연습하며 익숙해질 때까지 혼자 차분하게 집중하는 시간을 가짐",
                    ],
                },
                "ⓔ (관련 심리 현상)": {
                    "required_groups": [
                        ["사회적억제"],
                    ],
                    "forbidden_groups": [
                        ["사회적촉진"],
                    ],
                    "is_conclusion": True,
                    "term_required": True,
                    "model_answers": [
                        "사회적 억제",
                    ],
                },
            },
        },
        "q2_sentence": {
            "label": "[서논술형 2] 조건에 맞는 문장 작성",
            "items": {
                "(1) 문장": {
                    "allowed_methods": ["비교와 대조", "비교", "대조"],
                    "method_feature_groups": {
                        # 비교와 대조 특성: 두 대상(쉬운/어려운 과제)의 대비가 모두 드러나야 함
                        "비교와 대조": [
                            ["쉬운", "쉽"],
                            ["함께", "모임", "커피숍", "도서관"],
                            ["어렵", "도전"],
                            ["혼자"],
                        ]
                    },
                    "required_groups": [
                        ["쉬운", "쉽"],
                        ["함께", "모임", "커피숍", "도서관"],
                        ["어렵", "도전"],
                        ["혼자", "연습"],
                    ],
                    "forbidden_groups": [],
                    "is_conclusion": False,
                    "model_answers": [
                        "비교적 쉬운 과제를 할 때는 커피숍이나 도서관에서 함께 공부하는 것이, "
                        "지나치게 어렵거나 도전이 필요한 과제를 할 때는 혼자 충분히 연습하는 것이 "
                        "효율적이다.(비교와 대조)",
                    ],
                },
                "(2) 문장": {
                    "allowed_methods": ["인과"],
                    "method_feature_groups": {
                        "인과": [
                            ["사회적촉진"],
                            ["사회적억제"],
                            ["때문", "-여서", "로인해", "-므로"],
                        ]
                    },
                    "required_groups": [
                        ["사회적촉진"],
                        ["사회적억제"],
                    ],
                    "forbidden_groups": [],
                    "is_conclusion": False,
                    "model_answers": [
                        "이는 쉬운 과제에서는 사회적 촉진이, 어려운 과제에서는 사회적 억제가 "
                        "나타나기 때문이다.(인과)",
                    ],
                },
            },
        },
        "q3_av": {
            "label": "[서논술형 3] 영상 기획 시청각 요소",
            "scene1_forbidden": ["함께", "모임", "경쾌", "밝은"],
            "items": {
                "A (시각 요소)": {
                    "required_groups": [
                        ["혼자"],
                        ["조용", "개인", "독서실", "학습실"],
                    ],
                    "forbidden_groups": [
                        ["함께", "여러명", "모임"],
                    ],
                    "effect_required_groups": [
                        ["혼자", "개인", "집중"],
                    ],
                    "model_answers": [
                        "조용한 개인 학습실에서 한 학생이 혼자 문제집에 몰두하는 모습을 클로즈업으로 보여줌",
                    ],
                },
                "B (청각 요소)": {
                    "required_groups": [
                        ["조용", "정적", "무음", "소음없"],
                    ],
                    "forbidden_groups": [
                        ["경쾌", "리듬감", "밝은음악"],
                    ],
                    "effect_required_groups": [
                        ["혼자", "집중", "조용"],
                    ],
                    "model_answers": [
                        "배경음악 없이 시계 초침 소리 정도만 은은하게 삽입함",
                    ],
                },
            },
        },
    },

    # =====================================================
    # 세트 2 : 정전기
    # =====================================================
    "세트2": {
        "title": "정전기의 특징",
        "q1_blank": {
            "label": "[서논술형 1] 표 빈칸 채우기",
            "items": {
                "⊙ (물의 상태에 비유)": {
                    "required_groups": [
                        ["고여있는물", "고인물"],
                    ],
                    "forbidden_groups": [
                        ["흐르는물"],
                    ],
                    "is_conclusion": False,
                    "model_answers": [
                        "높은 곳에 고여 있는 물",
                    ],
                },
                "ⓒ (전하의 상태)": {
                    "required_groups": [
                        ["이동하지않", "머물러있", "정지상태"],
                    ],
                    "forbidden_groups": [
                        ["전하가이동"],
                    ],
                    "is_conclusion": False,
                    "model_answers": [
                        "전하가 이동하지 않고 머물러 있음(정지 상태)",
                    ],
                },
                "ⓔ (위험성)": {
                    "required_groups": [
                        ["전압은높", "전압이높"],
                        ["위험하지않", "안전", "피해가없"],
                    ],
                    "forbidden_groups": [
                        ["위험하다", "감전등의위험이있"],
                    ],
                    "is_conclusion": True,
                    "model_answers": [
                        "전압은 매우 높지만 위험하지 않음(피해가 없음)",
                    ],
                },
            },
        },
        "q2_sentence": {
            "label": "[서논술형 2] 조건에 맞는 문장 작성",
            "items": {
                "(1) 문장": {
                    # '비유'는 1쪽 표에 없는 명칭이므로 '정의' 또는 '비교와 대조'만 인정
                    "allowed_methods": ["정의", "비교와 대조"],
                    "disallowed_method_labels": ["비유"],
                    "method_feature_groups": {
                        "정의": [
                            ["전하가정지상태", "정지상태로있"],
                            ["분포", "변화하지않"],
                        ],
                        "비교와 대조": [
                            ["흐르는물"],
                            ["고여있는물", "고인물"],
                        ],
                    },
                    "required_groups": [
                        ["정지상태", "이동하지않", "머물러있"],
                        ["고여있는물", "고인물"],
                    ],
                    "forbidden_groups": [],
                    "is_conclusion": False,
                    "model_answers": [
                        "정전기란 전하가 정지 상태로 있어 그 분포가 시간적으로 변화하지 않는 전기로, "
                        "흐르는 물과 같은 실생활 전기와 달리 고여 있는 물에 비유할 수 있다.(정의)",
                    ],
                },
                "(2) 문장": {
                    "allowed_methods": ["인과"],
                    "method_feature_groups": {
                        "인과": [
                            ["머물러있", "이동하지않", "정지"],
                            ["위험하지않", "안전", "피해가없"],
                        ]
                    },
                    "required_groups": [
                        ["머물러있", "이동하지않", "정지"],
                        ["위험하지않", "안전", "피해가없"],
                    ],
                    "forbidden_groups": [
                        ["위험하다"],
                    ],
                    "is_conclusion": True,
                    "model_answers": [
                        "전하가 이동하지 않고 머물러 있기 때문에, 정전기는 전압이 매우 높음에도 "
                        "불구하고 감전 등의 위험 없이 안전하다.(인과)",
                    ],
                },
            },
        },
        "q3_av": {
            "label": "[서논술형 3] 영상 기획 시청각 요소",
            "scene1_forbidden": ["폭포", "쏟아", "역동적", "웅장", "큰소리"],
            "items": {
                "A (시각 요소)": {
                    "required_groups": [
                        ["고여있", "정지된물", "저수지", "댐"],
                    ],
                    "forbidden_groups": [
                        ["폭포", "쏟아져내려", "역동적"],
                    ],
                    "effect_required_groups": [
                        ["이동하지않", "머물러있", "정지"],
                    ],
                    "model_answers": [
                        "폭포와 달리, 저수지나 댐에 잔잔하게 고여 있는 넓은 물의 정적인 화면",
                    ],
                },
                "B (청각 요소)": {
                    "required_groups": [
                        ["정적", "고요", "지지직", "작은소리"],
                    ],
                    "forbidden_groups": [
                        ["웅장", "큰소리", "부딪히는"],
                    ],
                    "effect_required_groups": [
                        ["머물러있", "정지", "위험하지않", "안전"],
                    ],
                    "model_answers": [
                        "물소리 없이 고요한 정적, 또는 아주 작은 '지지직' 소리만 삽입",
                    ],
                },
            },
        },
    },

    # =====================================================
    # 세트 3 : 인공지능 예술
    # =====================================================
    "세트3": {
        "title": "인공지능이 그린 그림을 바라보는 시각",
        "q1_blank": {
            "label": "[서논술형 1] 표 빈칸 채우기",
            "items": {
                "⊙ (올림픽 경기에 비유)": {
                    "required_groups": [
                        ["로봇"],
                        ["완벽", "실수없이"],
                        ["감동을주지못", "마음을울리지못"],
                    ],
                    "forbidden_groups": [],
                    "is_conclusion": False,
                    "model_answers": [
                        "로봇이 한 번의 실수 없이 완벽하게 해내지만 마음을 울리지 못하는 피겨 스케이팅",
                    ],
                },
                "ⓒ (예술로 볼 수 있는가+근거)": {
                    "required_groups": [
                        ["감정을느끼지못", "감정이없"],
                        ["철학이나이야기가없", "독자적인철학", "이야기가없"],
                    ],
                    "conclusion_groups": [
                        ["예술로보기어렵", "예술로볼수없", "예술이아니"],
                    ],
                    "forbidden_groups": [
                        ["예술로볼수있다", "예술이다"],
                    ],
                    "is_conclusion": True,
                    "model_answers": [
                        "감정을 느끼지 못하고 독자적인 철학이나 이야기가 없으므로 예술로 보기 어렵다.",
                    ],
                },
                "ⓔ (예술로서의 가치)": {
                    "required_groups": [
                        ["미술계에변화", "변화를가져왔"],
                        ["범주를확장", "예술의범주"],
                    ],
                    "forbidden_groups": [
                        ["가치가없", "의미가없"],
                    ],
                    "is_conclusion": True,
                    "model_answers": [
                        "기존 미술계에 변화를 가져왔고 예술의 범주를 확장할 수 있다는 점에서 상징적 가치를 지님",
                    ],
                },
            },
        },
        "q2_sentence": {
            "label": "[서논술형 2] 조건에 맞는 문장 작성",
            "items": {
                "(1) 문장": {
                    "allowed_methods": ["비교와 대조"],
                    "method_feature_groups": {
                        "비교와 대조": [
                            ["감정", "철학", "경험"],           # 인간 특성
                            ["감정을느끼지못", "철학이나이야기가없"],  # AI 특성
                        ]
                    },
                    "required_groups": [
                        ["감정", "철학", "경험"],
                        ["감정을느끼지못", "철학이나이야기가없"],
                    ],
                    # 오개념: AI에게 감정/철학이 있다고 서술하면 안 됨
                    "forbidden_groups": [
                        ["인공지능은감정을느낀다", "인공지능도감정이있"],
                    ],
                    "is_conclusion": False,
                    "model_answers": [
                        "인간의 예술에는 작가의 감정이나 철학, 경험이 담겨 있는 반면, 인공 지능은 감정을 "
                        "느끼지 못하고 독자적인 철학이나 이야기가 없다는 차이가 있다.(비교와 대조)",
                    ],
                },
                "(2) 문장": {
                    "allowed_methods": ["인과", "예시"],  # 근거-결론 구조를 인과에 준해 인정
                    "method_feature_groups": {
                        "인과": [
                            ["미술계에변화", "범주를확장"],
                            ["상징적가치", "의미"],
                        ]
                    },
                    "required_groups": [
                        ["미술계에변화", "범주를확장"],
                        ["상징적가치", "의미"],
                    ],
                    "forbidden_groups": [
                        ["가치가없", "의미가없"],
                    ],
                    "is_conclusion": True,
                    "model_answers": [
                        "그러나 인공 지능이 그린 그림은 미술계에 변화를 가져오고 예술의 범주를 확장할 "
                        "수 있다는 점에서 상징적인 가치를 지닌다.(인과)",
                    ],
                },
            },
        },
        "q3_av": {
            "label": "[서논술형 3] 영상 기획 시청각 요소",
            "scene1_forbidden": ["로봇", "완벽한", "기계적", "메트로놈", "기계음"],
            "items": {
                "A (시각 요소)": {
                    "required_groups": [
                        ["감정", "경험", "삶"],
                        ["감동", "몰입", "눈물"],
                    ],
                    "forbidden_groups": [
                        ["로봇", "완벽한", "기계적"],
                    ],
                    "effect_required_groups": [
                        ["감정", "경험", "감동"],
                    ],
                    "model_answers": [
                        "화가가 자신의 삶과 감정을 담아 그림을 완성해가는 모습과, 이를 본 관람객이 "
                        "감동받는 표정을 함께 보여줌",
                    ],
                },
                "B (청각 요소)": {
                    "required_groups": [
                        ["감정이실린", "따뜻한", "잔잔한"],
                    ],
                    "forbidden_groups": [
                        ["기계음", "메트로놈"],
                    ],
                    "effect_required_groups": [
                        ["감정", "철학", "경험"],
                    ],
                    "model_answers": [
                        "기계음 대신 잔잔하고 감정이 실린 현악기 독주 음악을 사용",
                    ],
                },
            },
        },
    },
}


# =========================================================
# 2. 채점 엔진
# =========================================================

def grade_blank_item(text: str, rubric_item: dict):
    req = rubric_item.get("required_groups", [])
    forb = rubric_item.get("forbidden_groups", [])
    conc = rubric_item.get("conclusion_groups", None)

    hit, total, misconception, req_status, forb_status = score_from_groups(text, req, forb)

    conclusion_ok = None
    if conc is not None:
        conclusion_ok = group_hit(text, conc[0]) if conc else True
        total += 1
        hit += 1 if conclusion_ok else 0

    verdict = verdict_label(hit, total, misconception)
    return {
        "hit": hit, "total": total, "misconception": misconception,
        "req_status": req_status, "verdict": verdict,
        "conclusion_ok": conclusion_ok,
    }


def extract_method_label(text: str):
    """문장 끝 괄호 안 방법 명칭 추출: '...다.(비교와 대조)' 형태"""
    import re
    m = re.findall(r"\(([^()]+)\)\s*$", text.strip())
    return m[-1].strip() if m else None


def grade_method_sentence(text: str, rubric_item: dict):
    declared = extract_method_label(text)
    allowed = rubric_item.get("allowed_methods", [])
    disallowed = rubric_item.get("disallowed_method_labels", [])

    method_ok = declared in allowed if declared else False
    method_disallowed_used = declared in disallowed if declared else False

    # 방법 특성 검증: 선언한 방법의 특성 키워드 그룹이 실제로 드러나야 함
    feature_ok = None
    feature_groups = rubric_item.get("method_feature_groups", {})
    if declared in feature_groups:
        f_hit, f_total, f_mis, _, _ = score_from_groups(text, feature_groups[declared], [])
        feature_ok = (f_hit == f_total)
    elif declared and declared not in feature_groups:
        feature_ok = None  # 특성 정의 안 된 방법(자유 서술)

    req = rubric_item.get("required_groups", [])
    forb = rubric_item.get("forbidden_groups", [])
    hit, total, misconception, req_status, forb_status = score_from_groups(text, req, forb)

    verdict = "FAIL"
    notes = []
    if method_disallowed_used:
        notes.append(f"'{declared}'은(는) 1쪽 표에 없는 설명 방법 명칭입니다. "
                      f"(허용: {', '.join(allowed)})")
    if declared is None:
        notes.append("문장 끝에 사용한 설명 방법 명칭 '(방법명)' 표기가 없습니다.")
    elif not method_ok and not method_disallowed_used:
        notes.append(f"선언한 방법 '{declared}'이(가) 허용된 방법({', '.join(allowed)})과 다릅니다.")
    if feature_ok is False:
        notes.append(f"선언한 방법 '{declared}'의 특성이 답안 내용에 충분히 드러나지 않습니다.")

    if total > 0:
        if hit == total and not misconception and (method_ok or declared is None) and feature_ok is not False:
            verdict = "PASS"
        elif hit == 0:
            verdict = "FAIL"
        else:
            verdict = "PARTIAL"
    else:
        verdict = "PASS" if (method_ok and feature_ok is not False) else "PARTIAL"

    if misconception:
        verdict += " (오개념 의심 ⚠)"

    return {
        "declared_method": declared, "method_ok": method_ok,
        "feature_ok": feature_ok, "hit": hit, "total": total,
        "misconception": misconception, "verdict": verdict, "notes": notes,
    }


def grade_av_item(element_text: str, effect_text: str, rubric_item: dict, scene1_forbidden: list):
    req = rubric_item.get("required_groups", [])
    forb = rubric_item.get("forbidden_groups", []) + [scene1_forbidden]
    hit, total, misconception, req_status, forb_status = score_from_groups(element_text, req, forb)

    eff_req = rubric_item.get("effect_required_groups", [])
    eff_hit, eff_total, eff_mis, eff_status, _ = score_from_groups(effect_text, eff_req, [])

    contrast_ok = not group_hit(element_text, scene1_forbidden)

    overall_ok = (hit == total) and contrast_ok and (eff_hit == eff_total) and not misconception
    verdict = "PASS" if overall_ok else ("FAIL" if (hit == 0 and eff_hit == 0) else "PARTIAL")
    if misconception:
        verdict += " (오개념 의심 ⚠)"
    if not contrast_ok:
        verdict += " / 장면1과 대비 실패"

    return {
        "hit": hit, "total": total, "eff_hit": eff_hit, "eff_total": eff_total,
        "contrast_ok": contrast_ok, "misconception": misconception, "verdict": verdict,
    }


# =========================================================
# 3. Streamlit UI
# =========================================================

st.set_page_config(page_title="서논술형 자동 채점", layout="wide")
st.title("📝 서·논술형 문항 자동 채점 (2회시험 대비)")
st.caption("세트1(사회적 촉진·억제) / 세트2(정전기) / 세트3(인공지능 예술)")

set_key = st.sidebar.radio("세트 선택", list(RUBRIC.keys()),
                            format_func=lambda k: f"{k} · {RUBRIC[k]['title']}")
set_rubric = RUBRIC[set_key]

tab1, tab2, tab3 = st.tabs(["서논술형 1 (빈칸)", "서논술형 2 (문장)", "서논술형 3 (영상 기획)"])

# ---------- 서논술형 1 ----------
with tab1:
    st.subheader(set_rubric["q1_blank"]["label"])
    answers = {}
    for key, item in set_rubric["q1_blank"]["items"].items():
        with st.expander(f"모범 답안 / 인정 표현 보기 — {key}"):
            for ma in item["model_answers"]:
                st.write("• " + ma)
        answers[key] = st.text_input(f"{key} 학생 답안 입력", key=f"{set_key}_q1_{key}")

    if st.button("채점하기", key=f"{set_key}_grade_q1"):
        for key, item in set_rubric["q1_blank"]["items"].items():
            text = answers[key]
            if not text.strip():
                st.warning(f"{key}: 답안이 입력되지 않았습니다.")
                continue
            result = grade_blank_item(text, item)
            st.markdown(f"**{key}** → **{result['verdict']}**  "
                        f"(필수요소 {result['hit']}/{result['total']} 충족)")
            if result["conclusion_ok"] is not None and not result["conclusion_ok"]:
                st.error("⛔ 결론 방향 확인 필요: 요구된 결론 방향이 답안에 드러나지 않습니다.")
            if result["misconception"]:
                st.error("⚠ 반대 개념(오개념)으로 의심되는 표현이 포함되어 있습니다.")

# ---------- 서논술형 2 ----------
with tab2:
    st.subheader(set_rubric["q2_sentence"]["label"])
    st.info("문장 끝에 사용한 설명 방법을 '(방법명)' 형태로 표기해서 입력하세요. 예: '...이다.(비교와 대조)'")
    answers2 = {}
    for key, item in set_rubric["q2_sentence"]["items"].items():
        allowed = ", ".join(item.get("allowed_methods", []))
        with st.expander(f"모범 답안 보기 — {key} (허용 설명 방법: {allowed})"):
            for ma in item["model_answers"]:
                st.write("• " + ma)
        answers2[key] = st.text_area(f"{key} 학생 답안 입력", key=f"{set_key}_q2_{key}", height=80)

    if st.button("채점하기", key=f"{set_key}_grade_q2"):
        for key, item in set_rubric["q2_sentence"]["items"].items():
            text = answers2[key]
            if not text.strip():
                st.warning(f"{key}: 답안이 입력되지 않았습니다.")
                continue
            result = grade_method_sentence(text, item)
            st.markdown(f"**{key}** → **{result['verdict']}**  "
                        f"(선언 방법: {result['declared_method'] or '표기 없음'}, "
                        f"내용요소 {result['hit']}/{result['total']} 충족)")
            for n in result["notes"]:
                st.warning(n)
            if result["misconception"]:
                st.error("⚠ 반대 개념(오개념)으로 의심되는 표현이 포함되어 있습니다.")

# ---------- 서논술형 3 ----------
with tab3:
    st.subheader(set_rubric["q3_av"]["label"])
    scene1_forbidden = set_rubric["q3_av"]["scene1_forbidden"]
    st.caption(f"※ 장면1의 특성 키워드(대비 필요): {', '.join(scene1_forbidden)}")
    answers3 = {}
    for key, item in set_rubric["q3_av"]["items"].items():
        with st.expander(f"모범 답안 보기 — {key}"):
            for ma in item["model_answers"]:
                st.write("• " + ma)
        col1, col2 = st.columns(2)
        with col1:
            elem = st.text_area(f"{key} — 요소 내용", key=f"{set_key}_q3_{key}_elem", height=80)
        with col2:
            eff = st.text_area(f"{key} — 효과 서술", key=f"{set_key}_q3_{key}_eff", height=80)
        answers3[key] = (elem, eff)

    if st.button("채점하기", key=f"{set_key}_grade_q3"):
        for key, item in set_rubric["q3_av"]["items"].items():
            elem, eff = answers3[key]
            if not elem.strip() or not eff.strip():
                st.warning(f"{key}: 요소 또는 효과 서술이 입력되지 않았습니다.")
                continue
            result = grade_av_item(elem, eff, item, scene1_forbidden)
            st.markdown(f"**{key}** → **{result['verdict']}**  "
                        f"(요소 요건 {result['hit']}/{result['total']}, "
                        f"효과 요건 {result['eff_hit']}/{result['eff_total']}, "
                        f"장면1 대비 {'성공' if result['contrast_ok'] else '실패'})")
            if result["misconception"]:
                st.error("⚠ 반대 개념(오개념)으로 의심되는 표현이 포함되어 있습니다.")

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**채점 로직 요약**\n"
    "- 필수 키워드 그룹 중 하나만 매칭돼도 인정(동의어 허용)\n"
    "- 선언한 설명 방법의 특성 키워드가 없으면 PARTIAL/경고\n"
    "- 반대 개념 키워드 등장 시 오개념 의심 표시\n"
    "- 결론 방향 키워드 누락 시 결론 방향 오류로 별도 표시\n"
    "- 영상 기획 문항은 장면1 키워드가 재등장하면 '대비 실패'로 표시"
)
