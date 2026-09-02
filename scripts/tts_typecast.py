"""Typecast TTS-with-timestamps API로 narration.wav와 자막 타이밍(tts_timestamps.json)을 생성한다.
필요 환경변수: TYPECAST_API_KEY (선택: TYPECAST_VOICE_ID)
voice_id 목록: https://studio.typecast.ai/developers/api/voices

일반 TTS API 대신 '단어별 타임스탬프' 엔드포인트를 사용해서, 나중에 자막을
실제 발화 시각에 정확히 맞출 수 있게 한다.
"""
import base64
import json
import os

import requests

API_URL = "https://api.typecast.ai/v1/text-to-speech/with-timestamps"
# 예시 voice_id. 원하는 목소리는 https://studio.typecast.ai/developers/api/voices 에서 골라 voice_id를 바꾸세요.
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
            "audio_tempo": 1.4,
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
    data = resp.json()

    with open("narration.wav", "wb") as f:
        f.write(base64.b64decode(data["audio"]))

    words = data.get("words") or []
    with open("tts_timestamps.json", "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

    print(
        f"TTS 생성 완료: narration.wav "
        f"(길이 {data.get('audio_duration')}초, 단어 타임스탬프 {len(words)}개)"
    )


if __name__ == "__main__":
    main()
