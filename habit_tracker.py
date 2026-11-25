"""잔디(히트맵)형 습관/공부 기록기 - 월별 달력 + 할 일 달성률

[할 일] 완료한 일은 목록에서 사라지고, 달성률(완료/전체)이 자동 계산돼요.
    python habit_tracker.py add 리포트 쓰기          # 오늘 할 일 추가
    python habit_tracker.py add 자바 복습 -d 2026-11-27   # 다른 날짜에 추가
    python habit_tracker.py list                    # 남은 할 일 + 달성률
    python habit_tracker.py list --all              # 완료한 일도 함께 보기
    python habit_tracker.py done 1                  # 1번 완료
    python habit_tracker.py undo 1                  # 1번 완료 취소
    python habit_tracker.py remove 1                # 1번 삭제 (전체 개수에서도 빠짐)

[직접 기록] 공부 시간 같은 숫자를 기록하고 싶을 때
    python habit_tracker.py goal 120                # 하루 목표 설정 (예: 120분)
    python habit_tracker.py log 90                  # 오늘 90 기록 (같은 날은 누적)
    python habit_tracker.py log 60 -d 2026-11-20    # 특정 날짜에 기록
    python habit_tracker.py log 30 --overwrite      # 누적하지 않고 덮어쓰기

[보기]
    python habit_tracker.py show                    # 이번 달 달력을 터미널에 출력
    python habit_tracker.py show 2026-10            # 특정 달 보기
    python habit_tracker.py html                    # 최근 6개월 heatmap.html 생성
    python habit_tracker.py html --months 12        # 최근 12개월
"""
import argparse
import calendar
import json
import os
import webbrowser
from datetime import date, datetime, timedelta
from pathlib import Path

DATA_FILE = Path("habit_data.json")
HTML_FILE = Path("heatmap.html")
NAMES = ["월", "화", "수", "목", "금", "토", "일"]

# 단계별 색상 (0: 기록 없음 ~ 4: 목표 달성)
TERM_BG = [236, 22, 28, 34, 46]
TERM_FG = [250, 255, 255, 16, 16]
HTML_COLORS = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]


# ---------- 데이터 ----------
def load():
    data = {}
    if DATA_FILE.exists():
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    data.setdefault("goal", 60)
    data.setdefault("records", {})  # {"2026-11-25": 90}  직접 기록한 숫자
    data.setdefault("todos", {})    # {"2026-11-25": [{"title": "...", "done": false}]}
    return data


def save(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_day(text):
    """'YYYY-MM-DD' 문자열을 날짜로 변환. 없으면 오늘"""
    if not text:
        return date.today()
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise SystemExit("날짜 형식은 YYYY-MM-DD 이에요. 예: 2026-11-26")


def parse_month(text):
    """'YYYY-MM' 문자열을 (연, 월)로 변환. 없으면 이번 달"""
    if not text:
        today = date.today()
        return today.year, today.month
    try:
        d = datetime.strptime(text, "%Y-%m")
    except ValueError:
        raise SystemExit("월 형식은 YYYY-MM 이에요. 예: 2026-11")
    return d.year, d.month


def months_back(n):
    """이번 달부터 거꾸로 n개월의 (연, 월) 목록"""
    today = date.today()
    y, m = today.year, today.month
    result = []
    for _ in range(n):
        result.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return result


# ---------- 달성률 계산 ----------
def todo_counts(data, day):
    """(완료 수, 전체 수)"""
    items = data["todos"].get(day.isoformat(), [])
    return sum(1 for t in items if t["done"]), len(items)


def day_ratio(data, day):
    """그날의 달성률(0~). 할 일 달성률과 직접 기록 달성률 중 높은 쪽을 사용"""
    ratios = [0.0]
    done, total = todo_counts(data, day)
    if total:
        ratios.append(done / total)
    value = data["records"].get(day.isoformat(), 0)
    if value > 0:
        ratios.append(value / data["goal"])
    return max(ratios)


def level(ratio):
    """달성률에 따라 0~4단계로 변환"""
    if ratio <= 0:
        return 0
    if ratio >= 1:
        return 4
    if ratio >= 0.66:
        return 3
    if ratio >= 0.33:
        return 2
    return 1


def describe(data, day):
    """칸에 마우스를 올렸을 때 보여줄 설명"""
    parts = []
    done, total = todo_counts(data, day)
    if total:
        parts.append(f"할 일 {done}/{total} ({round(done / total * 100)}%)")
    value = data["records"].get(day.isoformat(), 0)
    if value > 0:
        parts.append(f"기록 {value}/{data['goal']}")
    return " · ".join(parts) if parts else "기록 없음"


def month_stats(data, year, month):
    """해당 월의 (목표 달성일 수, 평균 달성률 %) - 기록이 있는 날만 계산"""
    today = date.today()
    achieved = 0
    ratios = []
    for d in range(1, calendar.monthrange(year, month)[1] + 1):
        day = date(year, month, d)
        if day > today:
            break
        key = day.isoformat()
        if data["todos"].get(key) or data["records"].get(key, 0) > 0:
            r = day_ratio(data, day)
            ratios.append(min(r, 1.0))
            if r >= 1:
                achieved += 1
    avg = round(sum(ratios) / len(ratios) * 100) if ratios else 0
    return achieved, avg


def streak(data):
    """현재 연속 달성일 (오늘 미달성이면 어제부터 계산)"""
    day = date.today()
    if day_ratio(data, day) < 1:
        day -= timedelta(days=1)
    count = 0
    while day_ratio(data, day) >= 1:
        count += 1
        day -= timedelta(days=1)
    return count


# ---------- 할 일 ----------
def print_todos(data, day, show_all=False):
    items = data["todos"].get(day.isoformat(), [])
    label = "오늘" if day == date.today() else day.isoformat()
    print(f"\n  {label}의 할 일")
    shown = 0
    for i, t in enumerate(items, 1):
        if t["done"] and not show_all:
            continue  # 완료한 일은 목록에서 숨김
        print(f"  {i}. {'[x]' if t['done'] else '[ ]'} {t['title']}")
        shown += 1
    if not items:
        print("  (비어 있어요. add 명령어로 추가해 보세요)")
        return
    if shown == 0:
        print("  남은 할 일이 없어요. 모두 완료했어요!")
    done, total = len([t for t in items if t["done"]]), len(items)
    rate = round(done / total * 100)
    bar = "█" * (rate // 10) + "░" * (10 - rate // 10)
    print(f"\n  달성률 {bar} {done}/{total} ({rate}%)\n")


def get_item(data, day, number):
    items = data["todos"].get(day.isoformat(), [])
    if not 1 <= number <= len(items):
        raise SystemExit("번호가 올바르지 않아요. list --all 로 번호를 확인해 보세요.")
    return items, items[number - 1]


def cmd_add(args):
    data = load()
    day = get_day(args.date)
    data["todos"].setdefault(day.isoformat(), []).append(
        {"title": " ".join(args.title), "done": False}
    )
    save(data)
    print_todos(data, day)


def cmd_list(args):
    data = load()
    print_todos(data, get_day(args.date), args.all)


def cmd_done(args):
    data = load()
    day = get_day(args.date)
    if day > date.today():
        raise SystemExit("아직 오지 않은 날의 할 일은 완료할 수 없어요.")
    _, item = get_item(data, day, args.number)
    item["done"] = True
    save(data)
    print(f"\n  완료: {item['title']}")
    print_todos(data, day)


def cmd_undo(args):
    data = load()
    day = get_day(args.date)
    _, item = get_item(data, day, args.number)
    item["done"] = False
    save(data)
    print(f"\n  완료 취소: {item['title']}")
    print_todos(data, day)


def cmd_remove(args):
    data = load()
    day = get_day(args.date)
    items, item = get_item(data, day, args.number)
    items.pop(args.number - 1)
    if not items:
        del data["todos"][day.isoformat()]
    save(data)
    print(f"\n  삭제: {item['title']}")
    print_todos(data, day)


# ---------- 직접 기록 ----------
def cmd_goal(args):
    data = load()
    data["goal"] = args.value
    save(data)
    print(f"하루 목표를 {args.value}으로 설정했어요.")


def cmd_log(args):
    data = load()
    day = get_day(args.date)
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


# ---------- 보기 ----------
def cmd_show(args):
    os.system("")  # Windows 터미널에서 ANSI 색상 활성화
    data = load()
    year, month = parse_month(args.month)
    today = date.today()

    print(f"\n  {year}년 {month}월\n")
    print("  " + "".join(f" {n}  " for n in NAMES))
    for week in calendar.monthcalendar(year, month):
        line = "  "
        for d in week:
            if d == 0:
                line += "     "
                continue
            day = date(year, month, d)
            if day > today:  # 아직 오지 않은 날은 흐리게
                line += f"\033[2m {d:2d} \033[0m "
                continue
            lv = level(day_ratio(data, day))
            style = f"\033[48;5;{TERM_BG[lv]}m\033[38;5;{TERM_FG[lv]}m"
            if day == today:  # 오늘은 굵게 + 밑줄
                style += "\033[1;4m"
            line += f"{style} {d:2d} \033[0m "
        print(line)

    achieved, avg = month_stats(data, year, month)
    print(f"\n  이달 달성 {achieved}일 | 평균 달성률 {avg}% | 현재 연속 {streak(data)}일")
    done, total = todo_counts(data, today)
    if total:
        print(f"  오늘 할 일 {done}/{total} ({round(done / total * 100)}%)")
    print("  다른 달 보기: python habit_tracker.py show 2026-10\n")


def month_card(data, year, month):
    today = date.today()
    cells = []
    for week in calendar.monthcalendar(year, month):
        for d in week:
            if d == 0:
                cells.append('<div class="c empty"></div>')
                continue
            day = date(year, month, d)
            if day > today:
                cells.append(f'<div class="c l0 future">{d}</div>')
                continue
            cls = f"c l{level(day_ratio(data, day))}" + (" today" if day == today else "")
            tip = f"{day.isoformat()} : {describe(data, day)}"
            cells.append(f'<div class="{cls}" title="{tip}">{d}</div>')
    heads = "".join(f'<div class="h">{n}</div>' for n in NAMES)
    body = "".join(cells)
    achieved, avg = month_stats(data, year, month)
    return (
        f'<section class="card"><h3>{year}년 {month}월</h3>'
        f'<p class="sub">달성 {achieved}일 · 평균 달성률 {avg}%</p>'
        f'<div class="cal">{heads}{body}</div></section>'
    )


def cmd_html(args):
    data = load()
    cards = "".join(month_card(data, y, m) for y, m in months_back(args.months))
    css_levels = "\n".join(f".l{i}{{background:{c}}}" for i, c in enumerate(HTML_COLORS))
    legend = "".join(f'<div class="c l{i} lg"></div>' for i in range(5))
    html = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>습관 히트맵</title>
<style>
body{{font-family:sans-serif;margin:24px;color:#24292f}}
.wrap{{display:flex;flex-wrap:wrap;gap:20px}}
.card{{padding:14px 16px;border:1px solid #d0d7de;border-radius:10px}}
.card h3{{margin:0 0 4px}}
.sub{{margin:0 0 10px;font-size:13px;color:#57606a}}
.cal{{display:grid;grid-template-columns:repeat(7,38px);gap:4px}}
.h{{text-align:center;font-size:12px;color:#57606a}}
.c{{width:38px;height:38px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:13px}}
.empty{{background:none}}
{css_levels}
.l3,.l4{{color:#fff}}
.future{{opacity:.4}}
.today{{outline:2px solid #24292f;font-weight:bold}}
.legend{{display:flex;gap:4px;align-items:center;margin-top:16px;font-size:12px}}
.lg{{width:16px;height:16px}}
</style></head><body>
<h2>습관/공부 히트맵</h2>
<p>현재 연속 <b>{streak(data)}일</b></p>
<div class="wrap">{cards}</div>
<div class="legend">적음 {legend} 많음</div>
</body></html>"""
    HTML_FILE.write_text(html, encoding="utf-8")
    print(f"{HTML_FILE} 파일을 만들었어요.")
    webbrowser.open(HTML_FILE.resolve().as_uri())


def main():
    parser = argparse.ArgumentParser(description="잔디(히트맵)형 습관/공부 기록기")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_date(p):
        p.add_argument("-d", "--date", help="YYYY-MM-DD (생략하면 오늘)")

    p = sub.add_parser("add", help="할 일 추가")
    p.add_argument("title", nargs="+")
    add_date(p)
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("list", help="할 일 목록과 달성률 보기")
    p.add_argument("--all", action="store_true", help="완료한 일도 함께 보기")
    add_date(p)
    p.set_defaults(func=cmd_list)

    for name, func, text in [
        ("done", cmd_done, "할 일 완료"),
        ("undo", cmd_undo, "완료 취소"),
        ("remove", cmd_remove, "할 일 삭제"),
    ]:
        p = sub.add_parser(name, help=text)
        p.add_argument("number", type=int, help="list 에 나온 번호")
        add_date(p)
        p.set_defaults(func=func)

    p = sub.add_parser("goal", help="직접 기록용 하루 목표 설정")
    p.add_argument("value", type=int)
    p.set_defaults(func=cmd_goal)

    p = sub.add_parser("log", help="숫자(공부 시간 등) 직접 기록")
    p.add_argument("value", type=int)
    add_date(p)
    p.add_argument("--overwrite", action="store_true", help="누적 대신 덮어쓰기")
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("show", help="월별 달력을 터미널에 출력")
    p.add_argument("month", nargs="?", help="YYYY-MM (생략하면 이번 달)")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("html", help="월별 HTML 히트맵 생성")
    p.add_argument("--months", type=int, default=6, help="보여줄 개월 수 (기본 6)")
    p.set_defaults(func=cmd_html)

    args = parser.parse_args()
    if getattr(args, "value", 1) <= 0:
        parser.error("값은 1 이상이어야 해요.")
    if getattr(args, "months", 1) <= 0:
        parser.error("개월 수는 1 이상이어야 해요.")
    args.func(args)


if __name__ == "__main__":
    main()
