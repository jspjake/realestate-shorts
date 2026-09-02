"""Anthropic API(웹 검색 포함)로 동네 소개 쇼츠 대본을 생성해 script.json에 저장한다.
필요 환경변수: ANTHROPIC_API_KEY
실행: python generate_script.py <동네명>

안전장치:
1) 검색 도중 응답이 일시정지(pause_turn)되면 자동으로 이어서 계속 요청한다.
2) 검색을 여러 번 하면서 남는 중간 텍스트를 걸러내고, 마지막 답변에서
   첫 '{'부터 마지막 '}'까지만 JSON으로 추출한다.
3) 검색 인용 과정에서  태그가 섞여 나오면 태그만 제거하고 텍스트는 남긴다.
4) 내레이션이 너무 짧게 나오면 한 번 더 강하게 재요청한다.
"""
import json
import os
import re
import sys

import anthropic

MODEL = "claude-sonnet-5"
MIN_NARRATION_CHARS = 420
MAX_CONTINUATIONS = 5  # pause_turn 이어가기 최대 횟수 (무한루프 방지)

CITE_TAG_RE = re.compile(r"<cite[^>]*>(.*?)", re.DOTALL | re.IGNORECASE)

SYSTEM_PROMPT = """당신은 한국 부동산 동네 소개 유튜브 쇼츠 대본 작가입니다.
아래 조건을 반드시 지켜서 대본을 작성하세요.

- 분량: 내레이션 기준 420~500자. 이보다 짧게 쓰지 마세요. 분량을 채우기 위해
  뻔하거나 늘어지는 문장을 쓰지 말고, 아래 카테고리에서 여러 개를 조합해
  실제 정보 밀도를 높여서 채우세요.
- 톤: 친근한 구어체, 사람이 직접 말하듯이
- 출력 형식 주의: 이 결과물은 사람이 읽는 게 아니라 프로그램이 그대로 음성
  합성(TTS)에 넘깁니다.  태그, 각주, 마크다운 같은 어떤 마크업도 절대
  포함하지 말 것. 검색 결과를 참고했더라도 태그 없이 자연스러운 문장으로만
  풀어서 쓸 것.
- 타겟 시청자: 그 동네를 잘 모르는 지방 거주자도 포함. 단순 trivia보다
  "이 동네가 실제로 어떤 곳인지 체감"할 수 있는 실용적인 내용 위주로 구성할 것.
- 구체성: 가능하면 실제 아파트 단지명, 도로명, 지하철역명 등 구체적인 고유명사를
  언급할 것. "학군이 좋다", "교통이 편리하다" 같은 뭉뚱그린 표현만 쓰지 말 것.
- 웹 검색 활용: 재건축·재개발 진행 상황, 최근 이슈처럼 시간이 지나면 바뀌는
  정보는 웹 검색으로 확인한 뒤 반영할 것. 특정 기업의 본사·사옥 위치처럼 자주
  바뀌는 정보를 언급하려면 반드시 검색으로 현재 상태를 확인하고, 확인이
  어려우면 언급을 피할 것. 단, 검색은 최대 2~3회까지만 하고, 그 이상 고민하지
  말고 확보한 정보만으로 반드시 최종 JSON 답변을 작성할 것. 검색을 계속
  반복하느라 답변을 못 쓰는 일이 없도록 할 것.
- 균형: 장점만 나열하지 말 것. 그 동네의 단점이나 아쉬운 점(예: 높은 집값,
  교통 혼잡, 노후 시설, 편의시설 부족, 주차난 등)을 최소 1가지는 자연스럽게
  포함시킬 것. 장점만 늘어놓으면 광고처럼 느껴져서 신뢰도가 떨어짐.
- 내용: 아래 1번(위치·교통)을 우선적으로 검토하되, 그 동네의 진짜 특징이 아니면
  억지로 넣지 않아도 됨. 최소 3~4가지를 조합해 구체적으로 구성할 것.
  1) 위치·교통 접근성 (최우선 고려): 강남/서울 내에서 정확히 어디쯤인지 — 예:
     테헤란로 기준 남/북, 인접한 동네·구, 주요 업무지구(강남역·테헤란로, 잠실,
     판교·경기남부 등)까지의 출퇴근 편의성. 서울 지리를 잘 모르는 사람도 감
     잡을 수 있게 설명할 것.
  2) 재건축·재개발 이슈: 진행 중이거나 화제가 된 단지, 최근 동향
  3) 학군·교육 배경 (해당되면)
  4) 개발 연혁 (언제, 어떻게 지금 모습이 됐는지)
  5) 의외의 통계나 상식
- 지명의 어원·유래는 다루지 말 것 (밋밋하고 실용성이 낮음)
- 절대 하지 말 것: 확인 안 된 구체적 수치를 단정적으로 말하기, 특정 매물·특정
  중개업소 홍보, 자극적이거나 선정적인 표현, "다음 편에서는~" 같은 예고성
  멘트로 마무리하기
- 시작 3초 안에 흥미를 끄는 훅(hook) 문장으로 시작
- 마무리는 예고 멘트 없이, 마지막 사실이나 인사이트로 여운을 남기며 자연스럽게
  끝낼 것

출력은 반드시 아래 JSON 형식으로만 답하세요. JSON 앞뒤에 다른 설명이나
코드펜스, 인용 태그를 절대 추가하지 마세요.
{
  "title": "유튜브 제목 (동네명 포함, 30자 내외)",
  "description": "유튜브 설명란 (동네명으로 시작, 2~3문장)",
  "tags": ["태그1", "태그2"],
  "narration": "실제 TTS로 읽을 내레이션 전문"
}
"""


def call_model(client: anthropic.Anthropic, user_message: str):
    """웹 검색을 켠 상태로 모델을 호출하고, pause_turn이면 자동으로 이어간다."""
    messages = [{"role": "user", "content": user_message}]
    response = None

    for _ in range(MAX_CONTINUATIONS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=messages,
        )
        if response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            continue
        break

    text_blocks = [b.text for b in response.content if getattr(b, "type", None) == "text"]
    # 검색을 여러 번 하면서 중간 혼잣말 텍스트 블록이 여러 개 생길 수 있다.
    # 실제 최종 답변은 마지막 텍스트 블록이므로 그것만 사용한다.
    raw_text = text_blocks[-1].strip() if text_blocks else ""

    # 코드펜스나 앞뒤 설명 문구가 섞여 있어도, 첫 '{'부터 마지막 '}'까지만 추출한다.
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw_text = raw_text[start : end + 1]

    return raw_text, response


def clean_script(script: dict) -> dict:
    """혹시 남아있는 <cite> 태그를 제거하고 안의 텍스트만 남긴다."""
    for key in ("title", "description", "narration"):
        if key in script and isinstance(script[key], str):
            script[key] = CITE_TAG_RE.sub(r"\1", script[key]).strip()
    return script


def main() -> None:
    if len(sys.argv) < 2:
        print("사용법: python generate_script.py <동네명>", file=sys.stderr)
        sys.exit(1)

    neighborhood = sys.argv[1]
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    raw_text, response = call_model(
        client, f"'{neighborhood}'에 대한 쇼츠 대본을 만들어줘. 필요하면 웹 검색으로 사실관계를 확인해."
    )

    try:
        script = json.loads(raw_text)
    except json.JSONDecodeError:
        print("모델 응답을 JSON으로 파싱하지 못했습니다. 원문:", file=sys.stderr)
        print(raw_text, file=sys.stderr)
        print(f"(참고) stop_reason: {response.stop_reason}", file=sys.stderr)
        print(f"(참고) content block 타입들: {[getattr(b, 'type', None) for b in response.content]}", file=sys.stderr)
        sys.exit(1)

    script = clean_script(script)
    narration_len = len(script.get("narration", ""))

    if narration_len < MIN_NARRATION_CHARS:
        print(
            f"1차 시도가 {narration_len}자로 목표({MIN_NARRATION_CHARS}자)에 못 미쳐 재요청합니다.",
            file=sys.stderr,
        )
        retry_message = (
            f"'{neighborhood}'에 대한 쇼츠 대본을 만들어줘. "
            f"방금 만든 대본은 너무 짧아서 다시 써야 해. "
            f"반드시 내레이션을 {MIN_NARRATION_CHARS}자 이상으로, "
            f"카테고리를 최소 4개 조합하고 실제 지명(단지명·도로명·역명 등)을 "
            f"더 구체적으로 넣어서 다시 작성해줘. 필요하면 웹 검색으로 확인해."
        )
        raw_text_2, response_2 = call_model(client, retry_message)
        try:
            script_2 = clean_script(json.loads(raw_text_2))
            if len(script_2.get("narration", "")) > narration_len:
                script = script_2
                narration_len = len(script["narration"])
        except json.JSONDecodeError:
            print("재요청 응답도 JSON 파싱 실패, 1차 결과를 그대로 사용합니다.", file=sys.stderr)

    script["neighborhood"] = neighborhood

    with open("script.json", "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    print(f"대본 생성 완료: {neighborhood} (내레이션 {narration_len}자)")


if __name__ == "__main__":
    main()
