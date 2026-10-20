import html
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title='교육생 차량 주행 및 조 편성 자동 계산기',
    page_icon='🚗',
    layout='wide',
)

# ---------- 스타일 ----------
st.markdown(
    """
<style>
/* 본문: 너무 넓게 늘리지 않고 읽기 좋은 폭 유지 */
.block-container {
    padding-top: 2.5rem;
    max-width: 1400px;
}

/* 제목 */
.main-title {
    font-size: 2.8rem;
    font-weight: 900;
    line-height: 1.3;
    margin-bottom: 0.4rem;
}
.main-desc {
    font-size: 1.3rem;
    opacity: 0.8;
    line-height: 1.6;
    margin-bottom: 1.5rem;
}

/* 요약 카드 */
.summary-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 1rem;
}
.summary-item {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 18px 22px;
}
.summary-label {
    font-size: 1.3rem;
    color: #64748b;
    font-weight: 700;
}
.summary-value {
    font-size: 2.6rem;
    font-weight: 900;
    color: #0f172a;
    line-height: 1.3;
}

/* 조 제목 */
.group-title {
    font-size: 2.2rem;
    font-weight: 900;
    margin: 2rem 0 0.8rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 3px solid #e2e8f0;
}
.group-range {
    font-size: 1.4rem;
    font-weight: 600;
    color: #64748b;
    margin-left: 0.8rem;
}

/* 차량 카드 */
.car-card {
    background: #ffffff;
    color: #0f172a;
    border: 2px solid #e2e8f0;
    border-radius: 18px;
    padding: 20px 22px;
    box-shadow: 0 3px 10px rgba(15, 23, 42, 0.06);
    display: flex;
    flex-direction: column;
    min-height: 260px;
    margin-bottom: 1rem;
}
.car-name {
    font-size: 2.4rem;
    font-weight: 900;
    color: #1e3a8a;
    margin-bottom: 8px;
}
.car-stat {
    font-size: 1.4rem;
    color: #334155;
    margin-bottom: 12px;
    line-height: 1.6;
}
.car-stat b {
    color: #0f172a;
    font-weight: 900;
}
.badges {
    margin-bottom: 14px;
    line-height: 2.2;
}
.badge {
    display: inline-block;
    padding: 4px 14px;
    margin: 4px 8px 4px 0;
    border-radius: 999px;
    background: #e0e7ff;
    color: #312e81;
    font-size: 1.5rem;
    font-weight: 800;
}
.exit-box {
    margin-top: auto;
    background: #ecfdf5;
    color: #065f46;
    border-left: 6px solid #10b981;
    padding: 12px 16px;
    border-radius: 12px;
    font-size: 1.35rem;
    font-weight: 800;
    line-height: 1.5;
}
.empty-box {
    color: #94a3b8;
    font-size: 1.5rem;
    padding: 40px 0;
    text-align: center;
    font-weight: 700;
}

/* 사이드바 글자 키우기 */
[data-testid="stSidebar"] label p,
[data-testid="stSidebar"] .stMarkdown p {
    font-size: 1.2rem !important;
    font-weight: 700 !important;
}
[data-testid="stSidebar"] input {
    font-size: 1.3rem !important;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-size: 1.6rem !important;
}

/* 본문 경고 글자 */
.stAlert p {
    font-size: 1.2rem !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------- 핵심 로테이션 계산 함수 (차량별 고정 규칙 사후 필터링 방식) ----------
def generate_training_schedule(start_no, end_no, car_names, absent_str):
  absents = []
  if absent_str:
    for x in absent_str.replace(',', ' ').split():
      if x.isdigit():
        absents.append(int(x))

  num_cars = len(car_names)
  if num_cars == 0:
    return []

  group_capacity = num_cars * 4
  all_groups_data = []

  current_start = start_no
  group_num = 1
  global_cum_lap = 0

  while current_start <= end_no:
    current_end = min(current_start + group_capacity - 1, end_no)
    grp_all_nums = list(range(current_start, current_end + 1))

    if not grp_all_nums:
      break

    grp_range_str = f'{grp_all_nums[0]}~{grp_all_nums[-1]}번'

    car_assignments = {}
    car_targets = {}

    # 원래 조 대역을 먼저 차량별 고정 규칙으로 배정한 뒤, 결석자만 제외 (해당 차량 슬롯에서만 빠짐)
    for c_idx, car in enumerate(car_names):
      original_car_studs = grp_all_nums[c_idx::num_cars]
      car_studs = [s for s in original_car_studs if s not in absents]

      car_assignments[car] = car_studs
      car_targets[car] = len(car_studs) * 2  # 인원당 2바퀴

    # 퇴장 누적 회차 시뮬레이션
    car_laps_done = {car: 0 for car in car_names}
    exit_laps = {}
    group_local_lap = 0
    total_needed = sum(car_targets.values())

    if total_needed > 0:
      while sum(car_laps_done.values()) < total_needed:
        for car in car_names:
          if car_laps_done[car] < car_targets[car]:
            global_cum_lap += 1
            group_local_lap += 1
            car_laps_done[car] += 1
            if car_laps_done[car] == car_targets[car] and car not in exit_laps:
              exit_laps[car] = global_cum_lap

    all_groups_data.append({
        'group_num': group_num,
        'range_str': grp_range_str,
        'car_assignments': car_assignments,
        'car_targets': car_targets,
        'exit_laps': exit_laps,
        'total_laps': group_local_lap,
    })

    current_start += group_capacity
    group_num += 1

  return all_groups_data


# ---------- 카드 HTML ----------
def render_car_card(car, studs, target_laps, exit_lap):
  if studs:
    badges = ''.join(f'<span class="badge">{s}</span>' for s in studs)
    body = (
        f'<div class="car-stat">👥 배정 <b>{len(studs)}명</b> · '
        f'목표 <b>{target_laps}바퀴</b></div>'
        f'<div class="badges">{badges}</div>'
        f'<div class="exit-box">🏁 전체 누적 {exit_lap}번째 바퀴 완료 후 정차</div>'
    )
  else:
    body = '<div class="empty-box">주행 대상 없음</div>'

  return (
      '<div class="car-card">'
      f'<div class="car-name">🚘 {html.escape(car)}</div>'
      f'{body}'
      '</div>'
  )


# ---------- 사이드바 입력 ----------
st.sidebar.header('⚙️ 주행 조건 설정')
start_no = st.sidebar.number_input('시작 번호', value=1, step=1)
end_no = st.sidebar.number_input('끝 번호', value=32, step=1)

num_cars = st.sidebar.radio('운행 차량 대수', options=[3, 4], index=0)

st.sidebar.subheader('🚘 운행 차량 번호')
default_cars_str = '51호, 52호, 55호' if num_cars == 3 else '51호, 52호, 53호, 55호'
custom_cars_input = st.sidebar.text_input(
    '차량 번호 목록 (쉼표 구분)', value=default_cars_str
)
car_names = [car.strip() for car in custom_cars_input.split(',') if car.strip()]

absent_str = st.sidebar.text_input(
    '결석자 번호 (쉼표 구분)',
    value='7',
    help='예: 7, 10 (없으면 공백)',
)

if len(car_names) != num_cars:
  st.sidebar.warning(
      f'선택한 차량 대수({num_cars}대)와 입력한 차량 번호 개수({len(car_names)}개)가'
      ' 일치하지 않습니다.'
  )

# ---------- 본문 ----------
st.markdown(
    '<div class="main-title">🚗 교육생 차량 주행 및 조 편성 자동 계산기</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="main-desc">'
    '차량별 고정 배정 규칙을 유지한 상태에서 결석자를 제외하고, '
    '이전 조의 주행 누적 바퀴수를 이어서 계산합니다.'
    '</div>',
    unsafe_allow_html=True,
)

# ---------- 계산 및 출력 ----------
results = generate_training_schedule(start_no, end_no, car_names, absent_str)

if not results:
  st.warning('조건에 맞는 교육생이 없거나 차량 번호 설정이 올바르지 않습니다.')
else:
  absent_count = len([x for x in absent_str.replace(',', ' ').split() if x.isdigit()])
  total_students = sum(
      len(studs) for g in results for studs in g['car_assignments'].values()
  )

  st.markdown(
      '<div class="summary-row">'
      f'<div class="summary-item"><div class="summary-label">총 교육생</div>'
      f'<div class="summary-value">{total_students}명</div></div>'
      f'<div class="summary-item"><div class="summary-label">총 조 수</div>'
      f'<div class="summary-value">{len(results)}조</div></div>'
      f'<div class="summary-item"><div class="summary-label">결석자</div>'
      f'<div class="summary-value">{absent_count}명</div></div>'
      f'<div class="summary-item"><div class="summary-label">운행 차량</div>'
      f'<div class="summary-value">{len(car_names)}대</div></div>'
      '</div>',
      unsafe_allow_html=True,
  )

  for g in results:
    st.markdown(
        f'<div class="group-title">📌 {g["group_num"]}조'
        f'<span class="group-range">대상 번호 {g["range_str"]}</span></div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(len(car_names))
    for col, car in zip(cols, car_names):
      with col:
        st.markdown(
            render_car_card(
                car,
                g['car_assignments'].get(car, []),
                g['car_targets'].get(car, 0),
                g['exit_laps'].get(car, 0),
            ),
            unsafe_allow_html=True,
        )