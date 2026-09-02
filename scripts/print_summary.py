"""script.json을 읽어 GitHub Actions Job Summary용 마크다운으로 출력한다.
워크플로에서 `python scripts/print_summary.py >> $GITHUB_STEP_SUMMARY` 형태로 사용.
"""
import json

with open("script.json", "r", encoding="utf-8") as f:
    s = json.load(f)

print(f"## 📝 대본 검수: {s['neighborhood']}\n")
print(f"**제목**: {s['title']}\n")
print(f"**설명**: {s['description']}\n")
print(f"**태그**: {', '.join(s.get('tags', []))}\n")
print("**내레이션**:\n")
print(f"> {s['narration']}\n")
print("---")
print("이 내용이 마음에 들면 아래 'Review deployments'에서 Approve 하세요.")
print("이상하면 그냥 두면 이번 회차는 건너뛰고 다음 실행 때 넘어갑니다.")
