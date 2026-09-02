# 부동산 동네 소개 쇼츠 자동화

이틀에 하나, 사람 등장 없이 TTS 나레이션으로 만드는 유튜브 쇼츠 자동화 파이프라인입니다.
대본 생성까지는 완전 자동, **업로드 직전에 한 번 승인**을 받도록 설계되어 있습니다.

## 흐름

1. `generate` 잡: 큐에서 다음 동네를 뽑고 → Claude API로 대본 생성 → Job Summary에 표시
2. **여기서 멈춰서 승인 대기** (GitHub Environment 보호 규칙)
3. `build-and-upload` 잡(승인 후에만 실행): TTS 생성 → 이미지 소싱 → 영상 합성 → 유튜브 업로드 → 큐 갱신

## 준비물 (계정 발급)

| 항목 | 발급처 | 비고 |
|---|---|---|
| Anthropic API 키 | https://platform.claude.com | 대본 생성용. 이 볼륨이면 월 몇백 원 수준 |
| Typecast API 키 | https://typecast.ai/kr/developers/api | 무료 티어 월 15,000 크레딧(글자당 1크레딧) — 이 볼륨이면 무료로 충분할 가능성이 높습니다 |
| Unsplash Access Key | https://unsplash.com/developers | 무료 |
| Google Cloud 프로젝트 + OAuth 클라이언트 ID | https://console.cloud.google.com | YouTube Data API v3 활성화 필요 |

## 설정 순서

1. 이 저장소를 GitHub에 올립니다 (private 추천).
2. 로컬에 클론하고 `pip install -r requirements.txt`.
3. Google Cloud Console에서:
   - 새 프로젝트 생성 → "YouTube Data API v3" 사용 설정
   - OAuth 동의 화면 구성 (테스트 사용자로 본인 계정 추가)
   - OAuth 클라이언트 ID 생성 (유형: 데스크톱 앱) → JSON 다운로드 → `client_secret.json`으로 저장
4. 로컬에서 **딱 한 번**:
   ```
   python scripts/get_youtube_refresh_token.py
   ```
   브라우저가 열리면 업로드할 채널 계정으로 로그인 → 동의. 터미널에 출력되는
   `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` 세 값을 복사해둡니다.
5. GitHub 저장소 **Settings → Secrets and variables → Actions**에서 다음을 등록:
   - `ANTHROPIC_API_KEY`
   - `TYPECAST_API_KEY`
   - `UNSPLASH_ACCESS_KEY`
   - `YT_CLIENT_ID`
   - `YT_CLIENT_SECRET`
   - `YT_REFRESH_TOKEN`
6. GitHub 저장소 **Settings → Environments → New environment**에서 이름을
   `upload-approval`로 만들고, **Required reviewers**에 본인 계정을 추가합니다.
   → 이게 "업로드 전 검수" 게이트입니다.
7. Actions 탭에서 워크플로를 `workflow_dispatch`(수동 실행)로 한 번 테스트해봅니다.

## 테스트 시 체크리스트

- `neighborhoods.json`에 다루고 싶은 동네를 원하는 만큼 추가/수정하세요.
- 처음 몇 번은 `scripts/upload_youtube.py`의 `privacyStatus`가 `private`로 되어
  있는지 확인하고, 결과물이 만족스러우면 `public`으로 바꾸세요.
- TTS 목소리는 `scripts/tts_typecast.py`의 `DEFAULT_VOICE_ID`를 바꾸거나,
  Secrets에 `TYPECAST_VOICE_ID`를 추가해서 지정할 수 있습니다.
  (보이스 목록: https://studio.typecast.ai/developers/api/voices)
- 자막은 지금은 문장 길이 기준으로 균등 배분한 근사치입니다. 더 정밀한 동기화가
  필요하면 Typecast의 Timestamp TTS API 연동을 검토하세요.
- cron은 매일 체크하도록 되어 있습니다. 정확히 "이틀 간격"이 중요하면
  `pick_neighborhood.py`에 마지막 실행일 체크 로직을 추가하는 걸 권장합니다.

## 참고: 저작권 · 정책

- Unsplash 이미지는 상업적 이용이 가능한 라이선스입니다.
- 특정 동네 사진이 스톡에 없을 수 있어 일반 서울/아파트 이미지로 보강하도록
  구성했습니다. 실제 동네 사진이 꼭 필요하면 별도 소싱 방법을 검토하세요.
- 유튜브의 AI 콘텐츠 공개 의무는 "실사와 혼동될 만큼 사실적인 콘텐츠"가
  기준입니다. 이 구성(정지 이미지 + TTS 나레이션)은 통상 라벨링 대상이
  아니지만, 정책은 계속 바뀌므로 주기적으로 확인하시길 권합니다.
