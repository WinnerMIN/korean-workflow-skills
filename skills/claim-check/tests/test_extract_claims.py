#!/usr/bin/env python3
"""extract_claims.py 단위 시험. 실행: python3 ~/.claude/skills/claim-check/tests/test_extract_claims.py
실제로 문제가 되었던 문장 유형과 독립 검토가 짚은 미탐 사례를 포함한다."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import extract_claims as ec  # noqa: E402

SCRIPT = HERE.parent / "scripts" / "extract_claims.py"
CASES = [
    # (문장, 반드시 포함할 종류, 뽑혀야 하는가)
    ("신청은 1분이면 됩니다.", {"단정"}, True),                                   # 실제 사례: 근거 없는 소요 시간 단정
    ("이번 달 매출 1,200만 원, 그런데 통장엔 왜 이것밖에 없을까요?", {"수치"}, True),  # 실제 사례: 출처 없는 매출 수치(물음표 그대로)
    ("1,200만 원 팔았는데, 그래서 진짜 내 돈은?", {"수치"}, True),                # 실제 사례: 영상 도입부 수치
    ("하루 10분이면 충분하지 않을까요?", {"단정"}, True),
    ("※ 2027년부터 세율 1%가 적용됩니다.", {"규정", "날짜", "수치"}, True),
    ("지금 법대로라면 2027년부터 1%·500만 원입니다.", {"규정"}, True),            # 실제 사례: 조건 없는 제도 설명
    ("국민연금법이 정한 기준을 따릅니다.", {"규정"}, True),
    ("생애최초 담보인정 80%까지 가능합니다.", {"수치"}, True),                     # 실제 사례: 원문에 없는 수치
    ("등급 기준 800W 유선 제품이 대상입니다.", {"수치"}, True),                    # 실제 사례: 원문에 없는 수치
    ("월~목 18·19·20·21시에 운영합니다.", {"날짜"}, True),
    ("행사 기간은 2026.10.29 ~ 2026.11.01입니다.", {"날짜"}, True),
    ("접수는 2026-10-29에 마감합니다.", {"날짜"}, True),
    ("4차 산업혁명 대상을 수상한 업체입니다.", {"기관·이력"}, True),
    ("코로나19 속에서도 매년 개최된 행사입니다.", {"기관·이력"}, True),
    ("축제는 10월 3일부터 5일까지 안동 탈춤공원에서 열립니다.", {"날짜"}, True),
    ("소상공인은 시행령 제12조에 따라 신고 의무가 면제됩니다.", {"규정"}, True),
    ("이 양식을 쓰면 정산 시간이 절반으로 줄어듭니다.", {"효과"}, True),
    ("국내에서 가장 큰 커피 박람회입니다.", {"비교"}, True),
    ("누구나 무조건 환급받을 수 있습니다.", {"단정"}, True),
    ("2026.10.29(목) ~ 11.1(일) 4일간", {"날짜", "수치"}, True),
    ("어떤 파일부터 열어야 할까요?", set(), False),
    ("천천히 둘러보세요.", set(), False),
    ("이 링크를 통해 신청하면 이 사이트는 광고주로부터 수수료를 받습니다.", set(), False),
    ("세금 떼고 남는 돈까지 보여 줍니다.", set(), False),
    ("박람회 › 지역 › 2026 ○○하우징페어", set(), False),
    ("방법이 간단합니다.", set(), False),
    ("자세한 내용은 https://example.com/2026/1234/page 를 보세요", set(), False),
]


def test_classify():
    fails = 0
    for s, must, should in CASES:
        kinds = set(ec.classify(s))
        if bool(kinds) != should or not must <= kinds:
            print(f"FAIL: {s!r} → {sorted(kinds)} (기대 {sorted(must)}, 뽑힘={should})")
            fails += 1
    return fails


def run(*a):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, a)], capture_output=True, text=True)


def fill(data, **over):
    for c in data["claims"]:
        c.update(verdict="근거 있음", evidence="https://example.org/공지", quote="인용문")
        if "규정" in c["kinds"]:
            c["rule_conditions_checked"] = True
        c.update(over)
    return data


def test_check_against_source():
    fails = 0
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "원고.html"
        src.write_text('<html><head><meta name="description" content="입장료 5,000원, 10월 3일 개막"></head><body>'
                       "<p>신청은 1분이면 됩니다.</p><!-- 주석 속 2026년 3월 1일 --><p>입장료는 5,000원입니다.</p>"
                       "<p>천천히 둘러보세요.</p></body></html>", encoding="utf-8")
        r = run(src)
        out = Path(d) / "원고.claims" / "claims.json"
        data = json.loads(out.read_text(encoding="utf-8"))
        sents = [c["sentence"] for c in data["claims"]]
        if len(sents) != 3 or any("주석" in s for s in sents) or not any("개막" in s for s in sents):
            print("FAIL: 주석 제외·meta 설명 포함·주장 3개 기대, 실제", sents, r.stderr); fails += 1
        if not (Path(d) / "원고.claims" / "claims-review.txt").exists():
            print("FAIL: 검토표 claims-review.txt 없음"); fails += 1

        def check(dat, label, want):
            out.write_text(json.dumps(dat, ensure_ascii=False), encoding="utf-8")
            rc = run("--check", out, src).returncode
            if rc != want:
                print(f"FAIL: {label}: 종료 코드 {rc}(기대 {want})"); return 1
            return 0
        base = json.loads(out.read_text(encoding="utf-8"))
        fails += check(base, "판정 전 원장", 1)
        fails += check(fill(json.loads(json.dumps(base))), "모두 근거 있음", 0)
        fails += check(dict(base, claims=[]), "빈 원장", 1)
        d2 = fill(json.loads(json.dumps(base))); d2["claims"][0]["quote"] = "   "
        fails += check(d2, "공백뿐인 인용", 1)
        d3 = fill(json.loads(json.dumps(base))); d3["claims"] = d3["claims"][1:]
        fails += check(d3, "주장 행을 지운 원장", 1)
        d4 = fill(json.loads(json.dumps(base))); d4["claims"][0]["verdict"] = "삭제함"
        fails += check(d4, "삭제함인데 원고에 남은 문장", 1)
        good = fill(json.loads(json.dumps(base)))
        src.write_text(src.read_text(encoding="utf-8").replace("<p>천천히", "<p>누구나 무조건 당첨됩니다.</p><p>천천히"), encoding="utf-8")
        fails += check(good, "원고에 새 주장을 더한 뒤의 옛 원장", 1)
        src.write_text(src.read_text(encoding="utf-8").replace("<p>누구나 무조건 당첨됩니다.</p>", "").replace("<p>신청은 1분이면 됩니다.</p>", ""), encoding="utf-8")
        g2 = json.loads(json.dumps(good)); g2["claims"][[i for i, c in enumerate(g2["claims"]) if "1분" in c["sentence"]][0]]["verdict"] = "삭제함"
        fails += check(g2, "문장을 실제로 지우고 삭제함 표시", 0)
        if run("--check", out).returncode == 0:
            print("FAIL: 원고 없이 --check가 통과함"); fails += 1
    return fails


def test_rule_conditions():
    fails = 0
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "s.txt"; src.write_text("소상공인은 시행령에 따라 면제됩니다.\n", encoding="utf-8")
        run(src); out = Path(d) / "s.claims" / "claims.json"
        dat = fill(json.loads(out.read_text(encoding="utf-8")), rule_conditions_checked=False)
        out.write_text(json.dumps(dat, ensure_ascii=False), encoding="utf-8")
        if run("--check", out, src).returncode != 1:
            print("FAIL: 규정 주장의 시행일·조건 미확인을 통과시킴"); fails += 1
    return fails


if __name__ == "__main__":
    n = test_classify() + test_check_against_source() + test_rule_conditions()
    print("통과" if n == 0 else f"실패 {n}건")
    sys.exit(1 if n else 0)
