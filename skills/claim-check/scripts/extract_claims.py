#!/usr/bin/env python3
"""원고에서 사실 주장 후보 문장을 뽑아 주장 원장(claims.json)과 검토표(claims-review.txt)를 만든다.
claim-check 스킬의 일부.

사용:
  python3 extract_claims.py <원고 파일(.md/.txt/.html)> [-o 출력 폴더]
    출력 폴더 기본값: 원고와 같은 폴더의 <원고 이름>.claims/
  python3 extract_claims.py --check <claims.json> <원고 파일>
    원고를 다시 읽어 대조한다. 다음 가운데 하나라도 있으면 종료 코드 1:
      - 원고에 있는 주장 후보가 원장에 없거나(원고가 바뀐 뒤의 옛 원장 포함) 판정이 '근거 있음'이 아님
      - '근거 없음' 판정, 근거나 인용이 비었거나 공백뿐인 '근거 있음'
      - '삭제함'으로 표시했는데 그 문장이 원고에 아직 있음
      - 규정 주장인데 시행일·적용 조건 확인(rule_conditions_checked)이 true가 아님
    원고 sha256이 원장 작성 때와 다르면 알려 준다(위 대조가 통과하면 그것만으로 실패는 아님).

주장 종류(한 문장에 여러 개가 붙을 수 있다):
  수치  숫자+단위(원·%·명·개·일·분·W·cm 등), 큰 숫자(연도만 있는 숫자는 제외)
  날짜  연도·월일·요일·시각·기간(2026.10.29, 2026-10-29, 18·19시 등)
  규정  법·시행령·고시·세율·세목·신고·요건·자격·과태료 등 제도 표현(조사가 붙어도 잡는다)
  효과  "줄어듭니다", "절약", "개선" 같은 효과 주장
  비교  "보다", "가장", "최대·최소", "유일", "처음"
  단정  "무조건", "반드시", "누구나", "100%", "보장", "1분이면" 같은 단정·과장
  기관·이력  기관명(○○부·○○청·공단·협회 등), 수상·선정·지정·주최·후원, 개최 이력
질문형 문장과 ※·참고 문장도 위 표현이 있으면 뽑는다. 판정은 사람이나 별도 검토자가 한다.
"""
import hashlib
import html
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

KUNIT = r"(?:만\s?원|개월|시간|퍼센트|원|억|만|천|%|명|개|곳|건|회|번|일|주|년|분|초|㎡|평|배|위|등|세|쪽|장|칸|℃|°C|도)"
LUNIT = r"(?:km|cm|mm|kg|kW|mAh|GB|MB|ppm|dB|ml|m|g|L|W|V|A)"
NUM_UNIT = re.compile(r"\d[\d,.]*\s*" + KUNIT + r"|\d[\d,.]*\s*" + LUNIT + r"(?![A-Za-z])")
BIG_NUM = re.compile(r"\d{1,3}(?:,\d{3})+|(?<![\d.])(?!(?:19|20)\d\d(?!\d))\d{4,}")  # 연도만 있는 숫자는 수치로 보지 않는다
DATE = re.compile(
    r"(?:19|20)\d\d\s?년|(?:19|20)\d\d[.\-/]\d{1,2}[.\-/]\d{1,2}|\d{1,2}\s?월\s?\d{1,2}\s?일|\d{1,2}\s?월|\d{1,2}일\s?\([월화수목금토일]\)"
    r"|[월화수목금토일]요일|[월화수목금토일]\s?~\s?[월화수목금토일]|\d{1,2}:\d{2}|\d{1,2}(?:·\d{1,2})*\s?시(?![간장청도작])|오전|오후|마감"
    r"|\d\s?(?:일|월|시|년)?\s?(?:까지|부터)|\d{1,2}\.\d{1,2}\s?\(")
RULE = re.compile(
    r"(?<![방불편요마문어용수기필화공해])법(?:률|령)?(?=대로|[이은을에의상과와도만으로]|\s|[,.)」』]|$)|시행령|시행규칙|고시|조례|훈령|지침|제\d+조"
    r"|요건|자격|대상자|신청 기한|과태료|벌금|의무|면제|공제|감면|비과세|과세|세율|부가세|부가가치세|종합소득세|소득세|법인세|원천징수|간이과세|일반과세"
    r"|보험료|국민연금|건강보험|고용보험|산재보험|최저임금|신고|등록 기준|인증|허가|승인|규정|약관")
EFFECT = re.compile(r"줄어|줄일|절약|아낄|늘어|늘릴|높아|높일|낮아|낮출|개선|향상|해결|효과|도움이 됩|빨라|빨리|좋아집|예방|막을 수")
COMPARE = re.compile(r"보다\s|가장|최대|최소|최고|최저|유일|처음|최초|1위|으뜸|제일|훨씬")
ABSOLUTE = re.compile(r"무조건|반드시|누구나|항상|절대|100\s?%|보장|확실|틀림없|완벽|전혀|모두\s|모든\s|\d+\s?분(?:이)?면|바로\s|즉시|공짜|무료")
ORG = re.compile(
    r"공단|공사(?=[가-힣]{0,2}\s)|재단|협회|위원회|시청|군청|구청|도청|교육청|학회|조합|센터(?=[가-힣]{0,2}\s)"
    r"|[가-힣]{2,}부(?=\s|에서|가\s|는\s|의\s|와\s)|[가-힣]{2,}청(?=\s|에서|이\s|은\s|의\s|와\s)"
    r"|수상|선정|지정|주최|주관|후원|협찬|개최|창립|설립|역대|지난해|작년|전년|코로나19|산업혁명")
URL = re.compile(r"https?://\S+|www\.\S+")


def sentences(text):
    """(줄 번호, 문장) 목록. 줄 안에서 마침표·물음표·느낌표로 나눈다."""
    for no, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith(("```", "|---", "<!--")):
            continue
        line = re.sub(r"^(?:[#>*\-■◆━·※]+\s*|\d{1,2}[.)]\s+|참고\s*[:：]?\s*)+", "", line).strip()  # 목록 기호·※만 지운다(내용 앞 숫자는 남김)
        for s in re.split(r"(?<=[.!?。？])\s+|(?<=다\.)|(?<=요\.)", line):
            s = s.strip()
            if len(s) >= 6:
                yield no, s


def classify(s):
    t = URL.sub(" ", s)  # URL 안의 숫자를 주장으로 보지 않는다
    kinds = []
    if NUM_UNIT.search(t) or BIG_NUM.search(t):
        kinds.append("수치")
    if DATE.search(t):
        kinds.append("날짜")
    if RULE.search(t):
        kinds.append("규정")
    if EFFECT.search(t):
        kinds.append("효과")
    if COMPARE.search(t):
        kinds.append("비교")
    if ABSOLUTE.search(t):
        kinds.append("단정")
    if ORG.search(t):
        kinds.append("기관·이력")
    return kinds


def load_text(path):
    path = Path(path)
    raw = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() in (".html", ".htm"):
        extra = []
        for m in re.finditer(r"<meta\b[^>]*(?:name|property)=[\"'](?:description|og:description|twitter:description|og:title)[\"'][^>]*>", raw, re.I):
            c = re.search(r"content=[\"']([^\"']*)", m.group(0), re.I)
            if c: extra.append(c.group(1))
        for m in re.finditer(r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>", raw, re.S | re.I):
            extra += re.findall(r"\"(?:text|name|description|headline|startDate|endDate|price)\"\s*:\s*\"([^\"]+)\"", m.group(1))
        extra += re.findall(r"\balt=[\"']([^\"']{6,})[\"']", raw, re.I)
        raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
        raw = re.sub(r"<(script|style)\b.*?</\1>", "", raw, flags=re.S | re.I)
        raw = re.sub(r"<br\s*/?>|</p>|</li>|</h\d>|</div>|</tr>|</dd>|</dt>|</td>|</th>", "\n", raw, flags=re.I)
        raw = html.unescape(re.sub(r"<[^>]+>", " ", raw))
        raw += "\n" + "\n".join(html.unescape(x) for x in extra)
    else:
        raw = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), raw, flags=re.S)
    return raw


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def extract(path):
    out, seen = [], {}
    for no, s in sentences(load_text(path)):
        key = norm(s)
        if key in seen:  # 같은 문장이 여러 곳에 나오면 한 번만 검토하고 줄 번호만 더한다
            seen[key]["also_lines"].append(no)
            continue
        kinds = classify(s)
        if kinds:
            out.append({
                "id": f"C{len(out) + 1:03d}", "line": no, "sentence": s, "kinds": kinds,
                "evidence": "", "quote": "", "verdict": "확인 필요",
                "rule_conditions_checked": False if "규정" in kinds else None, "also_lines": [],
            })
            seen[key] = out[-1]
    return out


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(claims, src, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "claims.json").write_text(json.dumps({"source": str(src), "source_sha256": sha(src), "claims": claims}, ensure_ascii=False, indent=1), encoding="utf-8")
    rows = ["| ID | 줄 | 종류 | 문장 | 근거(경로·URL) | 인용 | 판정 |", "|---|---|---|---|---|---|---|"]
    for c in claims:
        rows.append(f"| {c['id']} | {c['line']} | {'·'.join(c['kinds'])} | {c['sentence'].replace('|', '/')} |  |  | 확인 필요 |")
    # .txt: 노트·문서 색인 도구(**/*.md)에 섞이지 않게 한다(내용은 마크다운 표)
    (outdir / "claims-review.txt").write_text(f"# 주장 검토표: {src}\n\n" + "\n".join(rows) + "\n", encoding="utf-8")


def check(ledger_path, src):
    data = json.loads(Path(ledger_path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        print("문제: 원장 형식이 아니다(claims 목록 없음)"); return 1
    bad, notes = [], []
    keys = [norm(c.get("sentence", "")) for c in data["claims"]]
    dup = sorted({k for k in keys if keys.count(k) > 1})
    if dup:
        bad.append(f"원장에 같은 문장이 {len(dup)}개 중복된다(판정이 엇갈릴 수 있음): {dup[0][:50]}")
    if data.get("source_sha256") and data["source_sha256"] != sha(src):
        notes.append("원고가 원장 작성 뒤에 바뀌었다(sha256 다름). 아래 대조로 판정한다")
    led = {norm(c["sentence"]): c for c in data["claims"]}
    current = extract(src)
    cur_keys = {norm(c["sentence"]) for c in current}
    for c in current:
        k = norm(c["sentence"])
        e = led.get(k)
        if e is None:
            bad.append(f"원장에 없는 주장(원고 {c['line']}행): {c['sentence'][:60]}")
            continue
        v = e.get("verdict")
        if v == "삭제함":
            bad.append(f"{e['id']} '삭제함'인데 원고 {c['line']}행에 그대로 있음")
        elif v != "근거 있음":
            bad.append(f"{e['id']} 판정이 '{v}': {c['sentence'][:60]}")
        elif not (str(e.get("evidence") or "").strip() and str(e.get("quote") or "").strip()):
            bad.append(f"{e['id']} '근거 있음'인데 근거 경로나 인용이 비었거나 공백뿐")
        if v == "근거 있음" and "규정" in set(e.get("kinds", [])) | set(c["kinds"]) and e.get("rule_conditions_checked") is not True:
            bad.append(f"{e['id']} 규정 주장인데 시행일·적용 조건 확인이 안 됨")
    for k, e in led.items():
        if k not in cur_keys and e.get("verdict") not in ("삭제함", "근거 있음"):
            notes.append(f"{e['id']} 원고에 없는 원장 항목(판정 {e.get('verdict')})")
    for n in notes:
        print("알림:", n)
    for b in bad:
        print("문제:", b)
    print(f"원고 주장 후보 {len(current)}개, 원장 {len(data['claims'])}개, 문제 {len(bad)}건")
    return 1 if bad else 0


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    if a[0] == "--check":
        if len(a) < 3:
            sys.exit("사용: --check <claims.json> <원고 파일>  (원고와 대조해야 한다)")
        sys.exit(check(a[1], a[2]))
    src = Path(a[0])
    if not src.is_file():
        sys.exit(f"원고 파일이 없습니다: {src}")
    outdir = Path(a[a.index("-o") + 1]) if "-o" in a else src.parent / f"{src.stem}.claims"
    claims = extract(src)
    write(claims, src, outdir)
    kinds = {}
    for c in claims:
        for k in c["kinds"]:
            kinds[k] = kinds.get(k, 0) + 1
    print(f"주장 후보 {len(claims)}개 ({', '.join(f'{k} {v}' for k, v in kinds.items()) or '없음'}) → {outdir}/claims.json, claims-review.txt")


if __name__ == "__main__":
    main()
