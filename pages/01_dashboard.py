import streamlit as st
from utils.style import apply_custom_style
from utils.auth import login_check, logout_button
import sqlite3
import pandas as pd
from datetime import date

st.set_page_config(
    page_title="대시보드",
    page_icon="🏠",
    layout="wide"
)

apply_custom_style()
login_check()
logout_button()

conn = sqlite3.connect("members.db", check_same_thread=False)

st.title("🏠 GROW DANCE 대시보드")

today = date.today()
today_str = str(today)
current_month = today.strftime("%Y-%m")

def table_exists(table_name):
    result = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    ).fetchone()
    return result is not None

def load_table(table_name):
    if table_exists(table_name):
        return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    return pd.DataFrame()

members = load_table("members")
instructors = load_table("instructors")
class_master = load_table("class_master")
enrollments = load_table("enrollments")
attendance = load_table("attendance")

if "dashboard_detail_title" not in st.session_state:
    st.session_state.dashboard_detail_title = ""
if "dashboard_detail_df" not in st.session_state:
    st.session_state.dashboard_detail_df = pd.DataFrame()

def show_detail(title, df):
    st.session_state.dashboard_detail_title = title
    st.session_state.dashboard_detail_df = df

# ----------------------
# 주요 지표
# ----------------------
active_members = (
    len(members[members["status"] == "재원"])
    if not members.empty and "status" in members.columns
    else 0
)

if not members.empty and "join_date" in members.columns:
    members_for_month = members.copy()
    members_for_month["join_date"] = members_for_month["join_date"].astype(str)
    monthly_new_members = len(
        members_for_month[members_for_month["join_date"].str.startswith(current_month)]
    )
else:
    monthly_new_members = 0

# 수강인원 = enrollments 기준 수강중 건수
# 예: A 1개, B 2개, C 3개 수강이면 6명으로 계산
enrollment_count = (
    len(enrollments[enrollments["status"] == "수강중"])
    if not enrollments.empty and "status" in enrollments.columns
    else 0
)

today_attendance = (
    attendance[attendance["attendance_date"] == today_str]
    if not attendance.empty and "attendance_date" in attendance.columns
    else pd.DataFrame()
)

today_present = (
    len(today_attendance[today_attendance["status"] == "출석"])
    if not today_attendance.empty
    else 0
)

today_total = len(today_attendance) if not today_attendance.empty else 0

today_rate = round((today_present / today_total) * 100, 1) if today_total > 0 else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("재원회원", active_members)
current_month_num = today.month

col2.metric(
    f"{current_month_num}월 신규회원",
    monthly_new_members
)
col3.metric("수강인원", enrollment_count)
col4.metric("오늘 출석률", f"{today_rate}%")

st.divider()

# ----------------------
# 회원상태 / 회원구분
# ----------------------
left, right = st.columns(2)

with left:
    st.subheader("회원상태 현황")

    if members.empty:
        st.info("등록된 회원이 없습니다.")
    else:
        status_count = members["status"].fillna("미입력").value_counts().reset_index()
        status_count.columns = ["회원상태", "회원수"]

        for _, row in status_count.iterrows():
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.write(row["회원상태"])
            with col_b:
                if st.button(
                    f"{row['회원수']}명",
                    key=f"status_{row['회원상태']}",
                    use_container_width=True
                ):
                    detail = members[members["status"].fillna("미입력") == row["회원상태"]].copy()
                    detail = detail.rename(columns={
                        "id": "번호",
                        "name": "회원명",
                        "gender": "성별",
                        "member_type": "회원구분",
                        "phone": "연락처",
                        "school": "학교",
                        "grade": "학년",
                        "status": "회원상태"
                    })
                    show_cols = ["번호", "회원명", "성별", "회원구분", "연락처", "학교", "학년", "회원상태"]
                    show_detail(
                        f"회원상태 [{row['회원상태']}] 회원 리스트",
                        detail[[col for col in show_cols if col in detail.columns]]
                    )

with right:
    st.subheader("회원구분 현황")

    if members.empty or "member_type" not in members.columns:
        st.info("회원구분 데이터가 없습니다.")
    else:
        type_count = members["member_type"].fillna("미입력").value_counts().reset_index()
        type_count.columns = ["회원구분", "회원수"]

        for _, row in type_count.iterrows():
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.write(row["회원구분"])
            with col_b:
                if st.button(
                    f"{row['회원수']}명",
                    key=f"type_{row['회원구분']}",
                    use_container_width=True
                ):
                    detail = members[members["member_type"].fillna("미입력") == row["회원구분"]].copy()
                    detail = detail.rename(columns={
                        "id": "번호",
                        "name": "회원명",
                        "gender": "성별",
                        "member_type": "회원구분",
                        "phone": "연락처",
                        "school": "학교",
                        "grade": "학년",
                        "status": "회원상태"
                    })
                    show_cols = ["번호", "회원명", "성별", "회원구분", "연락처", "학교", "학년", "회원상태"]
                    show_detail(
                        f"회원구분 [{row['회원구분']}] 회원 리스트",
                        detail[[col for col in show_cols if col in detail.columns]]
                    )

st.divider()

# ----------------------
# Class별 수강 인원
# ----------------------
st.subheader("Class별 수강 인원")

if enrollments.empty or class_master.empty:
    st.info("Class 등록 데이터가 없습니다.")
else:
    class_query = """
    SELECT
        c.id AS class_id,
        c.class_no AS "Class No.",
        c.class_name AS "Class 명",
        c.category AS 구분,
        i.instructor_name AS 강사,
        c.weekdays AS 요일,
        c.start_time AS "시간(시작)",
        c.end_time AS "시간(종료)",
        COUNT(e.member_id) AS 수강인원
    FROM enrollments e
    JOIN class_master c ON e.class_id = c.id
    LEFT JOIN instructors i ON c.instructor_id = i.id
    WHERE e.status = '수강중'
    GROUP BY c.id, c.class_no, c.class_name, c.category, i.instructor_name, c.weekdays, c.start_time, c.end_time
    ORDER BY 수강인원 DESC
    """

    class_count = pd.read_sql_query(class_query, conn)

    if class_count.empty:
        st.info("수강중인 회원이 없습니다.")
    else:
        for _, row in class_count.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([1, 1.5, 1, 1, 1, 1])
            col1.write(row["Class No."])
            col2.write(row["Class 명"])
            col3.write(row["강사"])
            col4.write(row["요일"])
            col5.write(f"{row['시간(시작)']}~{row['시간(종료)']}")

            with col6:
                if st.button(
                    f"{row['수강인원']}명",
                    key=f"class_{row['class_id']}",
                    use_container_width=True
                ):
                    detail_query = """
                    SELECT
                        m.id AS 번호,
                        m.name AS 회원명,
                        m.member_type AS 회원구분,
                        m.school AS 학교,
                        m.grade AS 학년,
                        m.phone AS 연락처,
                        e.enroll_date AS 수강시작일,
                        e.status AS 수강상태
                    FROM enrollments e
                    JOIN members m ON e.member_id = m.id
                    WHERE e.class_id = ?
                      AND e.status = '수강중'
                    ORDER BY m.name
                    """
                    detail = pd.read_sql_query(detail_query, conn, params=(int(row["class_id"]),))
                    show_detail(
                        f"Class [{row['Class No.']} / {row['Class 명']}] 수강 명단",
                        detail
                    )

st.divider()

# ----------------------
# 오늘 출석 현황
# ----------------------
st.subheader("오늘 출석 현황")

if today_attendance.empty:
    st.info("오늘 저장된 출석 기록이 없습니다.")
else:
    attendance_count = today_attendance["status"].value_counts().reset_index()
    attendance_count.columns = ["출석상태", "인원수"]

    for _, row in attendance_count.iterrows():
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.write(row["출석상태"])
        with col_b:
            if st.button(
                f"{row['인원수']}명",
                key=f"attendance_{row['출석상태']}",
                use_container_width=True
            ):
                detail_query = """
                SELECT
                    a.attendance_date AS 날짜,
                    c.class_no AS "Class No.",
                    c.class_name AS "Class 명",
                    m.name AS 회원명,
                    m.member_type AS 회원구분,
                    m.school AS 학교,
                    m.grade AS 학년,
                    a.status AS 출석상태,
                    a.memo AS 메모
                FROM attendance a
                LEFT JOIN members m ON a.member_id = m.id
                LEFT JOIN class_master c ON a.class_id = c.id
                WHERE a.attendance_date = ?
                  AND a.status = ?
                ORDER BY c.class_name, m.name
                """
                detail = pd.read_sql_query(
                    detail_query,
                    conn,
                    params=(today_str, row["출석상태"])
                )
                show_detail(
                    f"오늘 [{row['출석상태']}] 회원 리스트",
                    detail
                )

st.divider()

# ----------------------
# 클릭 결과 상세 리스트
# ----------------------
st.subheader("선택 상세 리스트")

if st.session_state.dashboard_detail_title == "":
    st.info("위의 인원수 버튼을 클릭하면 상세 리스트가 표시됩니다.")
else:
    st.markdown(f"### {st.session_state.dashboard_detail_title}")

    detail_df = st.session_state.dashboard_detail_df

    if detail_df.empty:
        st.info("조회된 데이터가 없습니다.")
    else:
        st.data_editor(
            detail_df,
            use_container_width=True,
            hide_index=True,
            disabled=True,
            height=420
        )

    if st.button("상세 리스트 닫기", use_container_width=True):
        st.session_state.dashboard_detail_title = ""
        st.session_state.dashboard_detail_df = pd.DataFrame()
        st.rerun()

st.divider()

# ----------------------
# 최근 출석 기록
# ----------------------
st.subheader("최근 출석 기록")

if attendance.empty:
    st.info("출석 기록이 없습니다.")
else:
    recent_query = """
    SELECT
        a.attendance_date AS 날짜,
        c.class_no AS "Class No.",
        c.class_name AS "Class 명",
        m.name AS 회원명,
        a.status AS 출석상태,
        a.memo AS 메모
    FROM attendance a
    LEFT JOIN members m ON a.member_id = m.id
    LEFT JOIN class_master c ON a.class_id = c.id
    ORDER BY a.attendance_date DESC, a.id DESC
    LIMIT 20
    """

    recent_attendance = pd.read_sql_query(recent_query, conn)

    st.data_editor(
        recent_attendance,
        use_container_width=True,
        hide_index=True,
        disabled=True,
        height=350
    )