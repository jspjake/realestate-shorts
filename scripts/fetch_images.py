"""Unsplash API로 동네 관련 이미지를 다운로드한다.
필요 환경변수: UNSPLASH_ACCESS_KEY

주의: 특정 동네 이름으로 검색해도 실제로 그 동네 사진이 잘 안 잡히는 경우가 많다.
그런 경우를 대비해 일반적인 서울/아파트 이미지로 보강한다.
실사 사진을 그대로 쓰는 대신 일러스트 톤으로 가고 싶다면 이 스크립트를
이미지 생성 API 호출로 교체하면 된다.
"""
import json
import os

import requests

SEARCH_URL = "https://api.unsplash.com/search/photos"


def search_and_download(query: str, access_key: str, start_index: int, max_results: int = 2) -> int:
    resp = requests.get(
        SEARCH_URL,
        params={"query": query, "per_page": max_results, "orientation": "portrait"},
        headers={"Authorization": f"Client-ID {access_key}"},
        timeout=30,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])

    count = 0
    for r in results:
        img_url = r["urls"]["regular"]
        img_data = requests.get(img_url, timeout=30).content
        with open(f"images/{start_index + count:02d}.jpg", "wb") as f:
            f.write(img_data)
        count += 1
    return count


def main() -> None:
    with open("script.json", "r", encoding="utf-8") as f:
        script = json.load(f)

    neighborhood = script["neighborhood"]
    access_key = os.environ["UNSPLASH_ACCESS_KEY"]

    os.makedirs("images", exist_ok=True)

        queries = [
        f"{neighborhood} Seoul",
        "Seoul subway station",
        "Seoul apartment complex",
        "Seoul skyline aerial",
        "Korean neighborhood street",
        "Gangnam Seoul cityscape",
    ]

    total = 0
    for q in queries:
        total += search_and_download(q, access_key, total, max_results=3)
    if total == 0:
        raise SystemExit(f"'{neighborhood}' 관련 이미지를 하나도 찾지 못했습니다. 검색어를 조정하세요.")

    print(f"이미지 {total}장 다운로드 완료")


if __name__ == "__main__":
    main()
