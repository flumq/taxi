import html
import streamlit as st

st.set_page_config(
    page_title='교육생 차량 주행 계산기',
    page_icon='🚗',
    layout='wide',
)

# ---------- 스타일 ----------
st.markdown(
    """
<style>
.block-container {
    padding-top: 3.5rem;  /* 🌟 상단 잘림 현상 해결을 위해 여백을 넉넉하게 수정 */
    padding-bottom: 1.5rem;
    max-width: 100%;
}
.title {
    font-size: 1.8rem;
    font-weight: 800;
    color: #374151;
    margin-bottom: 0.6rem;
}
.summary {
    font-size: 1.1rem;
    color: #4b5563;
    background: #f3f1ec;
    border-radius: 10px;
    padding: 8px 14px;
    margin-bottom: 0.6rem;
}
.summary b {
    color: #1f2937;
    font-weight: 800;
}
.caption {
    font-size: 0.95rem;
    color: #7b8190;
    margin-bottom: 0.4rem;
}

/* 전체 보드: 조(행) x 차량(열) */
.board {
    display: grid;
    gap: 10px;
    background: #f7f6f2;
    border-radius: 14px;
    padding: 12px;
}
.glabel {
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding-left: 6px;
}
.glabel b {
    font-size: clamp(22px, 2.2vw, 32px);
    font-weight: 800;
    color: #374151;
}
.glabel span {
    font-size: clamp(12px, 1vw, 15px);
    color: #7b8190;
}

.card {
    background: #ffffff;
    border: 1px solid #e3e1da;
    border-radius: 12px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-width: 0;
}
.car {
    font-size: clamp(18px, 1.8vw, 26px);
    font-weight: 800;
    color: #3d5a80;
}
.stat {
    font-size: clamp(13px, 1.2vw, 16px);
    color: #6b7280;
}
.badges {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}
.badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 2.1em;
    height: 2.1em;
    padding: 0 6px;
    border-radius: 999px;
    background: #e9ecf3;
    color: #3d4a63;
    font-size: clamp(15px, 1.5vw, 20px);
    font-weight: 700;
}
.exit {
    margin-top: auto;
    background: #eef5f0;
    color: #3f6b55;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: clamp(13px, 1.25vw, 17px);
    font-weight: 600;
}
.exit .num {
    display: inline-block;
    background: #fbe7b5;
    color: #7a4b00;
    font-size: 1.35em;
    font-weight: 900;
    padding: 0 8px;
    border-radius: 6px;
    margin: 0 2px;
}
.empty {
    color: #9ca3af;
    font-size: 1rem;
    text-align: center;
    margin: auto;
}

/* 📱 모바일 화면 최적화 (반응형 미디어 쿼리) */
@media (max-width: 768px) {
    .board {
        grid-template-columns: 1fr !important;
    }
    .glabel {
        margin-top: 12px;
        padding-left: 0;
        border-bottom: 2px solid #dcd9d0;
        padding-bottom: 6px;
    }
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

        # 원래 조 대역을 먼저 차량별 고정 규칙으로 배정한 뒤, 결석자만 제외
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
def render_card(car, studs, target_laps, exit_lap):
    if not studs:
        return (
            '<div class="card">'
            f'<div class="car">🚘 {html.escape(car)}</div>'
            '<div class="empty">주행 없음</div>'
            '</div>'
        )
    badges = ''.join(f'<span class="badge">{s}</span>' for s in studs)
    return (
        '<div class="card">'
        f'<div class="car">🚘 {html.escape(car)}</div>'
        f'<div class="stat">{len(studs)}명 · {target_laps}바퀴</div>'
        f'<div class="badges">{badges}</div>'
        f'<div class="exit">🏁 <span class="num">{exit_lap}</span>번째 바퀴 후 정차</div>'
        '</div>'
    )


# ---------- 사이드바 입력 ----------
st.sidebar.header('⚙️ 주행 조건')
start_no = st.sidebar.number_input('시작 번호', value=1, step=1)
end_no = st.sidebar.number_input('끝 번호', value=32, step=1)

num_cars = st.sidebar.radio('운행 차량 대수', options=[3, 4], index=0)

default_cars_str = '51호, 52호, 55호' if num_cars == 3 else '51호, 52호, 53호, 55호'
custom_cars_input = st.sidebar.text_input('차량 번호 (쉼표 구분)', value=default_cars_str)
car_names = [car.strip() for car in custom_cars_input.split(',') if car.strip()]

absent_str = st.sidebar.text_input(
    '결석자 번호 (쉼표 구분)',
    value='7',
    help='예: 7, 10 (없으면 공백)',
)

if len(car_names) != num_cars:
    st.sidebar.warning(
        f'차량 대수({num_cars}대)와 차량 번호 개수({len(car_names)}개)가 다릅니다.'
    )

# ---------- 본문 ----------
st.markdown('<div class="title">🚗 교육생 차량 주행 및 조 편성</div>', unsafe_allow_html=True)

results = generate_training_schedule(start_no, end_no, car_names, absent_str)

if not results:
    st.warning('조건에 맞는 교육생이 없거나 차량 번호 설정이 올바르지 않습니다.')
else:
    absent_count = len([x for x in absent_str.replace(',', ' ').split() if x.isdigit()])
    total_students = sum(
        len(studs) for g in results for studs in g['car_assignments'].values()
    )

    st.markdown(
        f'<div class="summary">총 <b>{total_students}명</b> · '
        f'<b>{len(results)}조</b> · 결석 <b>{absent_count}명</b> · '
        f'운행 <b>{len(car_names)}대</b></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="caption">※ 번호는 전체 누적 바퀴 기준입니다.</div>',
        unsafe_allow_html=True,
    )

    cells = []
    for g in results:
        cells.append(
            f'<div class="glabel"><b>{g["group_num"]}조</b>'
            f'<span>{g["range_str"]}</span></div>'
        )
        for car in car_names:
            cells.append(
                render_card(
                    car,
                    g['car_assignments'].get(car, []),
                    g['car_targets'].get(car, 0),
                    g['exit_laps'].get(car, 0),
                )
            )

    st.markdown(
        f'<div class="board" style="grid-template-columns: '
        f'clamp(80px, 7vw, 120px) repeat({len(car_names)}, 1fr);">'
        + ''.join(cells)
        + '</div>',
        unsafe_allow_html=True,
    )