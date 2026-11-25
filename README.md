# habit-heatmap

매일 목표 달성률에 따라 색이 진해지는 **월별 달력형 잔디(히트맵) 습관/공부 기록기**입니다.
외부 라이브러리 없이 Python 3.8+ 만 있으면 실행됩니다.

## 할 일 목록 (달성률 자동 계산)
```bash
python habit_tracker.py add 리포트 쓰기              # 오늘 할 일 추가
python habit_tracker.py add 자바 복습 -d 2026-11-27  # 다른 날짜에 추가
python habit_tracker.py list                        # 남은 할 일 + 달성률
python habit_tracker.py list --all                  # 완료한 일도 함께 보기
python habit_tracker.py done 1                      # 1번 완료 (목록에서 사라짐)
python habit_tracker.py undo 1                      # 1번 완료 취소
python habit_tracker.py remove 1                    # 1번 삭제 (전체 개수에서도 빠짐)
```
- 하루 달성률 = **완료한 할 일 ÷ 전체 할 일**
- 완료한 일은 `list`에서 사라지지만 기록은 남아 있어서 달성률 계산에 반영됩니다.
- 번호는 하루 안에서 고정이라, 중간 번호가 사라져도 나머지 번호는 그대로예요. (`remove`를 하면 번호가 당겨져요)

## 직접 기록 (공부 시간 등 숫자)
```bash
python habit_tracker.py goal 120               # 하루 목표 설정 (예: 120분)
python habit_tracker.py log 90                 # 오늘 90 기록 (같은 날은 누적)
python habit_tracker.py log 60 -d 2026-11-20   # 특정 날짜 기록
python habit_tracker.py log 30 --overwrite     # 덮어쓰기
```
같은 날 할 일과 직접 기록을 둘 다 쓰면 **달성률이 더 높은 쪽**이 잔디에 반영됩니다.

## 달력 보기
```bash
python habit_tracker.py show                   # 이번 달 달력을 터미널에 출력
python habit_tracker.py show 2026-10           # 특정 달 보기
python habit_tracker.py html                   # 최근 6개월 heatmap.html 생성 후 브라우저로 열기
python habit_tracker.py html --months 12       # 최근 12개월
```

## 색상 단계
| 단계 | 달성률 |
|---|---|
| 0 | 기록 없음 |
| 1 | 1% ~ 32% |
| 2 | 33% ~ 65% |
| 3 | 66% ~ 99% |
| 4 | 100% 이상 (목표 달성) |

## exe 파일로 만들기 (Windows)
```bash
pip install pyinstaller
pyinstaller --onefile habit_tracker.py
```
`dist/habit_tracker.exe`가 생성됩니다. 기록은 실행한 폴더의 `habit_data.json`에 저장됩니다.
