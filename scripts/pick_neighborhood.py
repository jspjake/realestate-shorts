"""neighborhoods.json에서 아직 사용하지 않은 다음 동네를 골라 출력한다.
GitHub Actions에서는 GITHUB_OUTPUT에도 기록해서 다음 스텝/잡에서 참조할 수 있게 한다.
실제로 '사용 완료' 표시는 업로드가 끝난 뒤 mark_used.py에서 한다 (실패 시 재시도 가능하도록).
"""
import json
import os
import sys

QUEUE_FILE = "neighborhoods.json"


def main() -> None:
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)

    next_item = next((x for x in items if not x["used"]), None)
    if next_item is None:
        print(
            "사용 가능한 동네가 큐에 남아있지 않습니다. neighborhoods.json에 항목을 추가하세요.",
            file=sys.stderr,
        )
        sys.exit(1)

    name = next_item["name"]
    print(f"선택된 동네: {name}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"neighborhood={name}\n")


if __name__ == "__main__":
    main()
