"""narration.wav + images/*.jpg + script.json의 자막을 합쳐 output.mp4(9:16)를 만든다.
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


def main() -> None:
    with open("script.json", "r", encoding="utf-8") as f:
        script = json.load(f)

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

    raw = script["narration"].replace("!", ".").replace("?", ".")
    sentences = [s.strip() for s in raw.split(".") if s.strip()]
    per_sentence = duration / max(len(sentences), 1)

    subtitle_clips = []
    for i, sentence in enumerate(sentences):
        txt = (
            TextClip(
                font=font_path,
                text=sentence,
                font_size=64,
                color="white",
                stroke_color="black",
                stroke_width=3,
                method="caption",
                size=(W - 100, None),
            )
            .with_start(i * per_sentence)
            .with_duration(per_sentence)
            .with_position(("center", H // 2))
        )
        subtitle_clips.append(txt)

    final = CompositeVideoClip([slideshow, *subtitle_clips], size=(W, H))
    final.write_videofile("output.mp4", fps=30, codec="libx264", audio_codec="aac")

    print("영상 합성 완료: output.mp4")


if __name__ == "__main__":
    main()
