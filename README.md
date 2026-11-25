# habit-heatmap

매일 목표 달성량을 기록하면 달성률에 따라 색이 진해지는 **잔디(히트맵)형 습관/공부 기록기**입니다.


## 사용법
```bash
python habit_tracker.py goal 120               # 하루 목표 설정 (예: 120분)
python habit_tracker.py log 90                 # 오늘 90 기록 (같은 날은 누적)
python habit_tracker.py log 60 -d 2026-11-20   # 특정 날짜 기록
python habit_tracker.py log 30 --overwrite     # 덮어쓰기
python habit_tracker.py show                   # 터미널에 잔디 출력
python habit_tracker.py html                   # heatmap.html 생성 후 브라우저로 열기
```

## 색상 단계
| 단계 | 달성률 |
|---|---|
| 0 | 기록 없음 |
| 1 | 1% ~ 32% |
| 2 | 33% ~ 65% |
| 3 | 66% ~ 99% |
| 4 | 목표 달성 (100% 이상) |

## exe 파일로 만들기 (Windows)
```bash
pip install pyinstaller
pyinstaller --onefile habit_tracker.py
```
`dist/habit_tracker.exe`가 생성됩니다. 기록은 실행한 폴더의 `habit_data.json`에 저장됩니다.
