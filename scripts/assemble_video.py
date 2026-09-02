"""narration.wav + images/*.jpg + tts_timestamps.json(단어별 타이밍)을 이용해
자막이 실제 음성과 정확히 맞는 세로 쇼츠 영상(output.mp4, 9:16)을 만든다.
GitHub Actions 러너에는 ffmpeg와 한글 폰트(fonts-nanum)가 미리 설치되어 있어야 한다.
moviepy 2.x 문법 기준.
"""
import glob
import json

from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    concatenate_videoclips,
)

W, H = 1080, 1920


def find_font() -> str:
    """fonts-nanum 패키지가 설치한 굵은 나눔고딕 폰트 파일 경로를 찾는다."""
    candidates = glob.glob("/usr/share/fonts/truetype/nanum/*Bold*.ttf")
    if not candidates:
        candidates = glob.glob("/usr/share/fonts/truetype/nanum/*.ttf")
    if not candidates:
        raise SystemExit(
            "나눔고딕 폰트를 찾지 못했습니다. 워크플로에 'apt-get install fonts-nanum'이 있는지 확인하세요."
        )
    return candidates[0]


MAX_CHARS_PER_CAPTION = 9  # 한 줄에 큼직하게 들어갈 정도의 짧은 구절 길이


def group_words_into_captions(words: list) -> list:
    """단어별 타임스탬프를 짧은 구절 단위 자막 그룹으로 묶는다 (한 줄에 표시하기 위함).
    각 그룹은 (자막 텍스트, 시작초, 종료초) 튜플이며, 실제 발화 시각 그대로다."""
    groups = []
    current = []
    current_len = 0

    def flush():
        if current:
            caption_text = " ".join(x["text"] for x in current)
            groups.append((caption_text, current[0]["start"], current[-1]["end"]))

    for w in words:
        word_text = w["text"].strip()
        added_len = len(word_text) + (1 if current else 0)
        # 글자수 제한을 넘기기 직전이면 지금 단어를 넣기 전에 끊는다.
        if current and current_len + added_len > MAX_CHARS_PER_CAPTION:
            flush()
            current = []
            current_len = 0
        current.append(w)
        current_len += len(word_text) + (1 if len(current) > 1 else 0)
        # 문장이 끝나는 단어면 여기서도 끊는다.
        if word_text.endswith((".", "!", "?")):
            flush()
            current = []
            current_len = 0

    flush()
    return groups


def main() -> None:
    with open("tts_timestamps.json", "r", encoding="utf-8") as f:
        words = json.load(f)

    font_path = find_font()

    audio = AudioFileClip("narration.wav")
    duration = audio.duration

    images = sorted(glob.glob("images/*.jpg"))
    if not images:
        raise SystemExit("images/ 폴더에 이미지가 없습니다.")

    per_image = duration / len(images)
    image_clips = []
    for path in images:
        clip = ImageClip(path, duration=per_image).resized(height=H)
        clip = clip.cropped(x_center=clip.w / 2, width=min(clip.w, W))
        image_clips.append(clip)

    slideshow = concatenate_videoclips(image_clips, method="compose").with_audio(audio)

    caption_groups = group_words_into_captions(words)
    if not caption_groups:
        raise SystemExit("자막 타이밍 데이터(tts_timestamps.json)가 비어 있습니다.")

    subtitle_clips = []
    for text, start, end in caption_groups:
        clip_duration = max(end - start, 0.3)
        txt = (
            TextClip(
                font=font_path,
                text=text,
                font_size=80,
                color="white",
                stroke_color="black",
                stroke_width=3,
                method="caption",
                size=(W - 160, None),
            )
            .with_start(start)
            .with_duration(clip_duration)
            .with_position(("center", H // 2))
        )
        subtitle_clips.append(txt)

    final = CompositeVideoClip([slideshow, *subtitle_clips], size=(W, H))
    final.write_videofile("output.mp4", fps=30, codec="libx264", audio_codec="aac")

    print(f"영상 합성 완료: output.mp4 (자막 {len(caption_groups)}개, 실제 음성 타이밍 기준)")


if __name__ == "__main__":
    main()
