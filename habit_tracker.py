"""잔디(히트맵)형 습관/공부 기록기

사용법:
    python habit_tracker.py goal 120            # 하루 목표 설정 (예: 120분)
    python habit_tracker.py log 90              # 오늘 90 기록 (누적)
    python habit_tracker.py log 60 -d 2026-11-20  # 특정 날짜에 기록
    python habit_tracker.py log 30 --overwrite  # 누적하지 않고 덮어쓰기
    python habit_tracker.py show                # 터미널에 잔디 출력
    python habit_tracker.py html                # heatmap.html 생성 후 열기
"""
import argparse
import json
import os
import webbrowser
from datetime import date, datetime, timedelta
from pathlib import Path

DATA_FILE = Path("habit_data.json")
HTML_FILE = Path("heatmap.html")
TERM_WEEKS = 26
HTML_WEEKS = 52

# 단계별 색상 (0: 기록 없음 ~ 4: 목표 달성)
TERM_COLORS = [236, 22, 28, 34, 46]
HTML_COLORS = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]


def load():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {"goal": 60, "records": {}}


def save(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def level(value, goal):
    """달성률에 따라 0~4단계로 변환"""
    if value <= 0:
        return 0
    ratio = value / goal
    if ratio >= 1:
        return 4
    if ratio >= 0.66:
        return 3
    if ratio >= 0.33:
        return 2
    return 1


def grid_days(weeks):
    """월요일 시작 기준, 오늘까지의 날짜를 열(주) 단위로 반환"""
    today = date.today()
    start = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks - 1)
    days = []
    for w in range(weeks):
        for d in range(7):
            day = start + timedelta(weeks=w, days=d)
            if day <= today:
                days.append(day)
    return days


def stats(data):
    goal = data["goal"]
    rec = data["records"]
    achieved = sum(1 for v in rec.values() if v >= goal)
    # 현재 연속 달성일 (오늘 미달성이면 어제부터 계산)
    day = date.today()
    if rec.get(day.isoformat(), 0) < goal:
        day -= timedelta(days=1)
    streak = 0
    while rec.get(day.isoformat(), 0) >= goal:
        streak += 1
        day -= timedelta(days=1)
    return achieved, streak


def cmd_goal(args):
    data = load()
    data["goal"] = args.value
    save(data)
    print(f"하루 목표를 {args.value}으로 설정했어요.")


def cmd_log(args):
    data = load()
    day = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else date.today()
    if day > date.today():
        print("미래 날짜는 기록할 수 없어요.")
        return
    key = day.isoformat()
    if args.overwrite:
        data["records"][key] = args.value
    else:
        data["records"][key] = data["records"].get(key, 0) + args.value
    save(data)
    total = data["records"][key]
    print(f"{key}: {total} / 목표 {data['goal']} ({round(total / data['goal'] * 100)}%)")


def cmd_show(args):
    os.system("")  # Windows 터미널에서 ANSI 색상 활성화
    data = load()
    days = grid_days(TERM_WEEKS)
    by_week = [days[i:i + 7] for i in range(0, len(days), 7)]
    names = ["월", "화", "수", "목", "금", "토", "일"]
    print()
    for row in range(7):
        line = f"{names[row]} "
        for week in by_week:
            if row < len(week):
                v = data["records"].get(week[row].isoformat(), 0)
                c = TERM_COLORS[level(v, data["goal"])]
                line += f"\033[38;5;{c}m██\033[0m"
            else:
                line += "  "
        print(line)
    achieved, streak = stats(data)
    print(f"\n목표 달성 {achieved}일 | 현재 연속 {streak}일 | 하루 목표 {data['goal']}")


def cmd_html(args):
    data = load()
    goal = data["goal"]
    cells = []
    for day in grid_days(HTML_WEEKS):
        v = data["records"].get(day.isoformat(), 0)
        cells.append(
            f'<div class="c l{level(v, goal)}" title="{day.isoformat()} : {v} / {goal}"></div>'
        )
    achieved, streak = stats(data)
    legend = "".join(f'<div class="c l{i}"></div>' for i in range(5))
    css_levels = "\n".join(f".l{i}{{background:{c}}}" for i, c in enumerate(HTML_COLORS))
    html = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>습관 히트맵</title>
<style>
body{{font-family:sans-serif;margin:24px;color:#24292f}}
.wrap{{overflow-x:auto}}
.grid{{display:grid;grid-template-rows:repeat(7,14px);grid-auto-flow:column;grid-auto-columns:14px;gap:3px}}
.c{{width:14px;height:14px;border-radius:3px}}
{css_levels}
.legend{{display:flex;gap:3px;align-items:center;margin-top:12px;font-size:12px}}
</style></head><body>
<h2>습관/공부 히트맵</h2>
<p>목표 달성 <b>{achieved}일</b> · 현재 연속 <b>{streak}일</b> · 하루 목표 <b>{goal}</b></p>
<div class="wrap"><div class="grid">{"".join(cells)}</div></div>
<div class="legend">적음 {legend} 많음</div>
</body></html>"""
    HTML_FILE.write_text(html, encoding="utf-8")
    print(f"{HTML_FILE} 파일을 만들었어요.")
    webbrowser.open(HTML_FILE.resolve().as_uri())


def main():
    parser = argparse.ArgumentParser(description="잔디(히트맵)형 습관/공부 기록기")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("goal", help="하루 목표 설정")
    p.add_argument("value", type=int)
    p.set_defaults(func=cmd_goal)

    p = sub.add_parser("log", help="오늘(또는 지정 날짜) 기록")
    p.add_argument("value", type=int)
    p.add_argument("-d", "--date", help="YYYY-MM-DD")
    p.add_argument("--overwrite", action="store_true", help="누적 대신 덮어쓰기")
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("show", help="터미널에 잔디 출력")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("html", help="HTML 히트맵 생성")
    p.set_defaults(func=cmd_html)

    args = parser.parse_args()
    if getattr(args, "value", 1) is not None and getattr(args, "value", 1) <= 0:
        parser.error("값은 1 이상이어야 해요.")
    args.func(args)


if __name__ == "__main__":
    main()
