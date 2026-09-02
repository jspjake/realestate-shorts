"""Typecast TTS API로 narration.wav를 생성한다.
필요 환경변수: TYPECAST_API_KEY (선택: TYPECAST_VOICE_ID)
voice_id 목록: https://studio.typecast.ai/developers/api/voices
"""
import json
import os

import requests

API_URL = "https://api.typecast.ai/v1/text-to-speech"
# 예시 voice_id. 원하는 목소리로 바꾸려면 위 링크에서 골라 TYPECAST_VOICE_ID로 지정하세요.
DEFAULT_VOICE_ID = "tc_60e5426de8b95f1d3000d7b5"


def main() -> None:
    with open("script.json", "r", encoding="utf-8") as f:
        script = json.load(f)

    api_key = os.environ["TYPECAST_API_KEY"]
    payload = {
        "voice_id": os.environ.get("TYPECAST_VOICE_ID", DEFAULT_VOICE_ID),
        "text": script["narration"],
        "model": "ssfm-v30",
        "prompt": {"emotion_type": "smart"},
        "output": {
            "volume": 100,
            "audio_pitch": 0,
            "audio_tempo": 1,
            "audio_format": "wav",
        },
    }

    resp = requests.post(
        API_URL,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()

    with open("narration.wav", "wb") as f:
        f.write(resp.content)

    print("TTS 생성 완료: narration.wav")
    print(
        "참고: 자막을 대사와 정밀하게 맞추고 싶으면 Typecast의 "
        "Timestamp TTS API 연동을 검토하세요 (https://typecast.ai/docs/ko). "
        "지금 스크립트는 문장 길이 기준 균등 배분으로 근사치만 맞춥니다."
    )


if __name__ == "__main__":
    main()
