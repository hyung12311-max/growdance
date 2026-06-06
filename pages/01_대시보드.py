import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from utils.style import apply_custom_style
from utils.auth import login_check, logout_button

st.set_page_config(page_title="대시보드", page_icon="🏠", layout="wide")
apply_custom_style()
login_check()
logout_button()

conn = sqlite3.connect("members.db", check_same_thread=False)

st.title("🏠 대시보드")

today = date.today()
today_str = str(today)
current_month = today.strftime("%Y-%m")
current_month_num = today.month

def load_table(table_name):
    try:
        return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    except:
        return pd.DataFrame()

members = load_table("members")
enrollments = load_table("enrollments")
attendance = load_table("attendance")
class_master = load_table("class_master")

if "dashboard_detail_title" not in st.session_state:
    st.session_state.dashboard_detail_title = ""

if "dashboard_detail_df" not in st.session_state:
    st.session_state.dashboard_detail_df = pd.DataFrame()

def show_detail(title, df):
    st.session_state.dashboard_detail_title = title
    st.session_state.dashboard_detail_df = df

active_members = len(members[members["status"] == "재원"]) if not members.empty else 0

if not members.empty and "join_date" in members.columns:
    month_df = members.copy()
    month_df["join_date"] = month_df["join_date"].astype(str)
    monthly_new_members = len(month_df[month_df["join_date"].str.startswith(current_month)])
else:
    monthly_new_members = 0

enrollment_count = len(enrollments[enrollments["status"] == "수강중"]) if not enrollments.empty else 0

today_attendance = attendance[attendance["attendance_date"] == today_str] if not attendance.empty else pd.DataFrame()
today_total = len(today_attendance)
today_present = len(today_attendance[today_attendance["status"] == "출석"]) if today_total > 0 else 0
today_rate = round((today_present / today_total) * 100, 1) if today_total > 0 else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button(f"재원회원\n\n{active_members}명", use_container_width=True):
        detail = members[members["status"] == "재원"].copy()
        show_detail("재원회원 리스트", detail)

with col2:
    if st.button(f"{current_month_num}월 신규회원\n\n{monthly_new_members}명", use_container_width=True):
        detail = members[members["join_date"].astype(str).str.startswith(current_month)].copy()
        show_detail(f"{current_month_num}월 신규회원 리스트", detail)

with col3:
    if st.button(f"수강인원\n\n{enrollment_count}명", use_container_width=True):
        query = """
        SELECT
            e.id AS 등록번호,
            m.name AS 회원명,
            c.class_no AS "Class No.",
            c.class_name AS "Class 명",
            c.weekdays AS 요일,
            c.start_time AS "시작시간",
            c.end_time AS "종료시간",
            e.enroll_date AS 수강시작일,
            e.status AS 수강상태
        FROM enrollments e
        JOIN members m ON e.member_id = m.id
        JOIN class_master c ON e.class_id = c.id
        WHERE e.status = '수강중'
        ORDER BY c.class_name, m.name
        """
        detail = pd.read_sql_query(query, conn)
        show_detail("전체 수강인원 리스트", detail)

with col4:
    if st.button(f"오늘 출석률\n\n{today_rate}%", use_container_width=True):
        query = """
        SELECT
            a.attendance_date AS 날짜,
            c.class_name AS "Class 명",
            m.name AS 회원명,
            a.status AS 출석상태,
            a.memo AS 메모
        FROM attendance a
        LEFT JOIN members m ON a.member_id = m.id
        LEFT JOIN class_master c ON a.class_id = c.id
        WHERE a.attendance_date = ?
        ORDER BY c.class_name, m.name
        """
        detail = pd.read_sql_query(query, conn, params=(today_str,))
        show_detail("오늘 출석 전체 리스트", detail)

st.divider()

st.subheader("선택 상세 리스트")

if st.session_state.dashboard_detail_title == "":
    st.info("상단 카드 버튼을 클릭하면 상세 리스트가 표시됩니다.")
else:
    st.markdown(f"### {st.session_state.dashboard_detail_title}")

    detail_df = st.session_state.dashboard_detail_df

    if detail_df.empty:
        st.info("조회된 데이터가 없습니다.")
    else:
        st.dataframe(detail_df, use_container_width=True, hide_index=True)

    if st.button("상세 리스트 닫기", use_container_width=True):
        st.session_state.dashboard_detail_title = ""
        st.session_state.dashboard_detail_df = pd.DataFrame()
        st.rerun()

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("회원상태 현황")

    if members.empty:
        st.info("회원 데이터가 없습니다.")
    else:
        status_count = members["status"].fillna("미입력").value_counts().reset_index()
        status_count.columns = ["회원상태", "회원수"]
        st.dataframe(status_count, use_container_width=True, hide_index=True)

with right:
    st.subheader("회원구분 현황")

    if members.empty:
        st.info("회원 데이터가 없습니다.")
    else:
        type_count = members["member_type"].fillna("미입력").value_counts().reset_index()
        type_count.columns = ["회원구분", "회원수"]
        st.dataframe(type_count, use_container_width=True, hide_index=True)

st.divider()

st.subheader("Class별 수강 인원")

if enrollments.empty or class_master.empty:
    st.info("Class 등록 데이터가 없습니다.")
else:
    query = """
    SELECT
        c.class_no AS "Class No.",
        c.class_name AS "Class 명",
        c.weekdays AS 요일,
        c.start_time AS "시작시간",
        c.end_time AS "종료시간",
        COUNT(e.member_id) AS 수강인원
    FROM enrollments e
    JOIN class_master c ON e.class_id = c.id
    WHERE e.status = '수강중'
    GROUP BY c.id
    ORDER BY 수강인원 DESC
    """
    class_count = pd.read_sql_query(query, conn)
    st.dataframe(class_count, use_container_width=True, hide_index=True)

st.divider()

st.subheader("오늘 출석 현황")

if today_attendance.empty:
    st.info("오늘 저장된 출석 기록이 없습니다.")
else:
    attendance_count = today_attendance["status"].value_counts().reset_index()
    attendance_count.columns = ["출석상태", "인원수"]
    st.dataframe(attendance_count, use_container_width=True, hide_index=True)