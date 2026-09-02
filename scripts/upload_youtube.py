"""완성된 output.mp4를 YouTube Data API로 업로드한다.
필요 환경변수: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
refresh token은 get_youtube_refresh_token.py를 로컬에서 1회 실행해 발급받는다.
"""
import json
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def main() -> None:
    with open("script.json", "r", encoding="utf-8") as f:
        script = json.load(f)

    creds = Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )

    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": script["title"],
            "description": script["description"],
            "tags": script.get("tags", []),
            "categoryId": "22",  # People & Blogs. 필요하면 변경.
        },
        "status": {
            # 처음 몇 회는 private로 테스트해보고, 안정화되면 public으로 바꾸는 걸 권장합니다.
            "privacyStatus": "private",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload("output.mp4", chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"업로드 진행률: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"업로드 완료: https://youtu.be/{video_id}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"video_id={video_id}\n")


if __name__ == "__main__":
    main()
