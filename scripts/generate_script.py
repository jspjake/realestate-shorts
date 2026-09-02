"""Anthropic API로 동네 소개 쇼츠 대본을 생성해 script.json에 저장한다.
필요 환경변수: ANTHROPIC_API_KEY
실행: python generate_script.py <동네명>
"""
import json
import os
import sys

import anthropic

# 비용/품질 균형이 좋은 모델. 볼륨이 작아 Haiku로 바꿔도 비용 차이는 미미하다.
MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """당신은 한국 부동산 동네 소개 유튜브 쇼츠 대본 작가입니다.
아래 조건을 반드시 지켜서 대본을 작성하세요.

- 분량: 내레이션 기준 400~450자 이보다 짧게 쓰지 마세요. (TTS 속도를 빠르게 설정해뒀으니 실제 재생시간은 60~70초 정도가 됩니다. 짧고 밋밋하게 쓰지 말고 정보 밀도를 높게 채울 것.)
- 톤: 친근한 구어체, 사람이 직접 말하듯이
- 타겟 시청자: 그 동네를 잘 모르는 지방 거주자도 포함. 단순 trivia보다 "이 동네가 실제로 어떤 곳인지 체감"할 수 있는 실용적인 내용 위주로 구성할 것.
- 내용: 아래 1번(위치·교통)을 우선적으로 검토하되, 그 동네의 진짜 특징이 아니면 억지로 넣지 않아도 됨. 최소 2~3가지를 조합해 구체적으로 구성할 것.
  1) 위치·교통 접근성 (최우선 고려): 강남/서울 내에서 정확히 어디쯤인지 — 예: 테헤란로 기준 남/북, 인접한 동네·구, 주요 업무지구(강남역·테헤란로, 잠실, 판교·경기남부 등)까지의 출퇴근 편의성. 서울 지리를 잘 모르는 사람도 감 잡을 수 있게 설명할 것.
  2) 재건축·재개발 이슈: 진행 중이거나 화제가 된 단지, 최근 동향 (단, 확실하지 않은 구체적 수치는 단정하지 말 것)
  3) 학군·교육 배경 (해당되면)
  4) 개발 연혁 (언제, 어떻게 지금 모습이 됐는지)
  5) 의외의 통계나 상식
- 지명의 어원·유래는 다루지 말 것 (밋밋하고 실용성이 낮음)
- 절대 하지 말 것: 확인 안 된 구체적 수치를 단정적으로 말하기, 특정 매물·특정 중개업소 홍보, 자극적이거나 선정적인 표현, "다음 편에서는~" 같은 예고성 멘트로 마무리하기
- 시작 3초 안에 흥미를 끄는 훅(hook) 문장으로 시작
- 마무리는 예고 멘트 없이, 마지막 사실이나 인사이트로 여운을 남기며 자연스럽게 끝낼 것

출력은 반드시 아래 JSON 형식으로만 답하세요. 다른 설명은 절대 추가하지 마세요.
{
  "title": "유튜브 제목 (동네명 포함, 30자 내외)",
  "description": "유튜브 설명란 (동네명으로 시작, 2~3문장)",
  "tags": ["태그1", "태그2"],
  "narration": "실제 TTS로 읽을 내레이션 전문"
}
"""


def main() -> None:
    if len(sys.argv) < 2:
        print("사용법: python generate_script.py <동네명>", file=sys.stderr)
        sys.exit(1)

    neighborhood = sys.argv[1]
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"'{neighborhood}'에 대한 쇼츠 대본을 만들어줘.",
            }
        ],
    )

    text_parts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
    raw_text = "\n".join(text_parts).strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.lower().startswith("json"):
            raw_text = raw_text.split("\n", 1)[-1]

    try:
        script = json.loads(raw_text)
    except json.JSONDecodeError:
        print("모델 응답을 JSON으로 파싱하지 못했습니다. 원문:", file=sys.stderr)
        print(raw_text, file=sys.stderr)
        print(f"(참고) stop_reason: {response.stop_reason}", file=sys.stderr)
        sys.exit(1)

    script["neighborhood"] = neighborhood

    with open("script.json", "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    print(f"대본 생성 완료: {neighborhood}")


if __name__ == "__main__":
    main()
