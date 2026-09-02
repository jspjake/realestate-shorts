"""로컬 PC에서 딱 한 번만 실행하는 스크립트입니다.

사전 준비:
1. Google Cloud Console에서 OAuth 2.0 클라이언트 ID(데스크톱 앱 유형)를 만듭니다.
2. 다운로드한 JSON을 이 스크립트와 같은 폴더에 client_secret.json 이름으로 저장합니다.

실행하면 브라우저가 열립니다. 업로드에 쓸 유튜브 채널 계정으로 로그인하고
동의하면 터미널에 세 가지 값이 출력됩니다. 이 값들을 GitHub Secrets에
YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN 으로 각각 등록하세요.
"""
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main() -> None:
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n=== 아래 값을 GitHub Secrets에 등록하세요 ===")
    print(f"YT_CLIENT_ID={creds.client_id}")
    print(f"YT_CLIENT_SECRET={creds.client_secret}")
    print(f"YT_REFRESH_TOKEN={creds.refresh_token}")


if __name__ == "__main__":
    main()
