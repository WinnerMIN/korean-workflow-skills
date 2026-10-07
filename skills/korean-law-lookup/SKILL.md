---
name: korean-law-lookup
description: "대한민국 법령·시행령·시행규칙·조례·판례·행정규칙·유권해석이 조금이라도 걸리는 질문이나 작업에서 답하기 전에 먼저 호출한다. 조문 내용, 판례 번호 확인, 법적 근거, 시행일·현행 여부, 과거 시점에 적용되는 법령, 조문 인용 검증, 조례의 상위법 점검 요청에 쓴다. korean-law MCP 도구 매핑과 인용 검증 절차를 담고 있다."
---

# 한국 법령·판례 조회 규칙

법령은 자주 개정되고, 모델의 학습 데이터에는 옛 조문과 폐지된 조항이 섞여 있다. 이 스킬은 법률 질문에 기억으로 답하지 않고 법제처 1차 출처를 조회한 뒤 답하게 한다.

## 준비

- [korean-law-mcp](https://github.com/chrisryugj/korean-law-mcp)(MIT)를 설치하고 법제처 Open API 인증키(OC)를 등록한다. 설치 방법은 원본 저장소의 README를 따른다.
- 등록이 끝나면 도구 이름이 `mcp__korean-law__search_law` 형태로 보인다.

## 규칙

- 대한민국 법령·시행령·시행규칙·조례·판례·행정규칙·유권해석이 조금이라도 걸리는 질문이나 작업에서는 학습 데이터나 기억으로 답하지 않는다. **반드시 `korean-law` MCP를 호출**해 법제처 국가법령정보로 확인한다.
- 도구 매핑
  - 법령 검색: `search_law` → 조문 본문: `get_law_text`
  - 판례·해석례: `search_decisions` + `get_decision_text`
  - 여러 단계에 걸친 조사: `legal_research`
  - 인용 검증·영향 분석·행위시법: `legal_analysis`
  - 조례의 상위법 정비 점검: `ordinance_radar`
  - 별표·서식: `get_annexes`
- 답변에 조문이나 판례를 인용하려면, 제시하기 전에 `legal_analysis(mode="verify_citations")`로 실제로 존재하는지와 내용이 맞는지 검증한다. 검증하지 않은 인용은 쓰지 않는다.
- 조문을 인용할 때는 시행일과 `[현행]` 여부를 함께 적는다. 과거 시점의 사건이면 `legal_analysis(mode="applicable_law")`로 그 당시 적용되던 법령(행위시법)을 확인한다.
- 도구 호출이 실패하면 추측으로 메우지 않고, 실패한 사실과 원인을 그대로 알린다.
- 도구 목록에 `search_law`가 없으면 `claude mcp list`로 등록 상태를 확인한다. MCP를 쓸 수 없으면 korean-law-mcp에 포함된 CLI로 대신 조회할 수 있다. 어느 경로로 조회하든 학습 데이터로 추측하지 않고 도구 출력만을 근거로 답한다.
