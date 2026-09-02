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

- 분량: 내레이션 기준 180~220자 (TTS로 읽었을 때 약 55~65초)
- 톤: 친근한 구어체, 사람이 직접 말하듯이
- 내용: 특정 동네의 일반적이지만 의외로 흥미로운 사실 1~2가지 중심 (학군, 집값 변천사, 지명 유래, 의외의 통계 등)
- 절대 하지 말 것: 확인 안 된 최신 수치나 소문을 단정적으로 말하기, 특정 매물·특정 중개업소 홍보, 자극적이거나 선정적인 표현
- 시작 3초 안에 흥미를 끄는 훅(hook) 문장으로 시작
- 마지막은 짧은 여운 또는 다음 편 예고성 멘트로 마무리
- 최신 통계나 정확한 수치보다는, 시간이 지나도 잘 안 바뀌는 일반 상식/역사/지명유래 위주로 구성할 것

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
        max_tokens=1000,
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
