"""narration.wav + images/*.jpg + script.json의 자막을 합쳐 output.mp4(9:16)를 만든다.
GitHub Actions 러너에는 ffmpeg와 한글 폰트(fonts-nanum)가 미리 설치되어 있어야 한다.
"""
import glob
import json

from moviepy.editor import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    concatenate_videoclips,
)

W, H = 1080, 1920
FONT = "NanumGothic-Bold"  # apt install fonts-nanum 로 설치되는 폰트명


def main() -> None:
    with open("script.json", "r", encoding="utf-8") as f:
        script = json.load(f)

    audio = AudioFileClip("narration.wav")
    duration = audio.duration

    images = sorted(glob.glob("images/*.jpg"))
    if not images:
        raise SystemExit("images/ 폴더에 이미지가 없습니다.")

    per_image = duration / len(images)
    image_clips = []
    for path in images:
        clip = ImageClip(path).resize(height=H).set_duration(per_image)
        clip = clip.crop(x_center=clip.w / 2, width=min(clip.w, W))
        image_clips.append(clip)

    slideshow = concatenate_videoclips(image_clips, method="compose").set_audio(audio)

    # 문장 단위 자막을 오디오 길이에 균등 배분 (정밀 동기화는 TODO 참고)
    raw = script["narration"].replace("!", ".").replace("?", ".")
    sentences = [s.strip() for s in raw.split(".") if s.strip()]
    per_sentence = duration / max(len(sentences), 1)

    subtitle_clips = []
    for i, sentence in enumerate(sentences):
        txt = (
            TextClip(
                sentence,
                fontsize=64,
                color="white",
                font=FONT,
                stroke_color="black",
                stroke_width=3,
                method="caption",
                size=(W - 100, None),
            )
            .set_start(i * per_sentence)
            .set_duration(per_sentence)
            .set_position(("center", H - 400))
        )
        subtitle_clips.append(txt)

    final = CompositeVideoClip([slideshow, *subtitle_clips], size=(W, H))
    final.write_videofile("output.mp4", fps=30, codec="libx264", audio_codec="aac")

    print("영상 합성 완료: output.mp4")


if __name__ == "__main__":
    main()
