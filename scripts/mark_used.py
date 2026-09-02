"""업로드가 성공적으로 끝난 뒤에만 호출한다. 실행: python mark_used.py <동네명>"""
import json
import sys

QUEUE_FILE = "neighborhoods.json"


def main() -> None:
    if len(sys.argv) < 2:
        print("사용법: python mark_used.py <동네명>", file=sys.stderr)
        sys.exit(1)

    name = sys.argv[1]
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)

    found = False
    for x in items:
        if x["name"] == name:
            x["used"] = True
            found = True
            break

    if not found:
        print(f"'{name}'을(를) 큐에서 찾지 못했습니다.", file=sys.stderr)
        sys.exit(1)

    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"'{name}' 사용 완료로 표시했습니다.")


if __name__ == "__main__":
    main()
