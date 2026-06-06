import streamlit as st
from utils.style import apply_custom_style
from utils.auth import login_check, logout_button
import sqlite3
import pandas as pd
from datetime import date

st.set_page_config(
    page_title="출석관리",
    page_icon="✅",
    layout="wide"
)

apply_custom_style()
login_check()
logout_button()

conn = sqlite3.connect("members.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attendance_date TEXT,
    member_id INTEGER,
    class_id INTEGER,
    status TEXT,
    memo TEXT
)
""")
conn.commit()

st.title("✅ 출석관리")

menu = st.radio(
    "메뉴 선택",
    ["Class별 출석 체크", "출석 기록 조회"],
    horizontal=True
)

# ----------------------
# Class별 출석 체크
# ----------------------
if menu == "Class별 출석 체크":
    st.subheader("Class별 출석 체크")

    attendance_date = st.date_input("출석일", value=date.today())

    class_query = """
    SELECT
        c.id,
        c.class_no,
        c.category,
        c.class_name,
        c.target,
        i.instructor_name,
        c.weekdays,
        c.start_time,
        c.end_time,
        c.duration
    FROM class_master c
    LEFT JOIN instructors i ON c.instructor_id = i.id
    WHERE c.active = 'Y'
    ORDER BY c.class_name
    """

    classes = pd.read_sql_query(class_query, conn)

    if classes.empty:
        st.info("사용 가능한 Class가 없습니다.")
        st.stop()

    class_label = st.selectbox(
        "Class 선택",
        classes.apply(
            lambda x: f"{x['id']} - {x['class_no']} / {x['class_name']} / {x['weekdays']} / {x['start_time']}~{x['end_time']}",
            axis=1
        )
    )

    class_id = int(class_label.split(" - ")[0])
    selected_class = classes[classes["id"] == class_id].iloc[0]

    st.info(
        f"선택 Class: {selected_class['class_no']} / {selected_class['class_name']} / "
        f"{selected_class['weekdays']} / {selected_class['start_time']}~{selected_class['end_time']} / "
        f"강사: {selected_class['instructor_name']}"
    )

    students_query = """
    SELECT
        m.id AS member_id,
        m.name AS 회원명,
        m.member_type AS 회원구분,
        m.school AS 학교,
        m.grade AS 학년,
        e.id AS enrollment_id
    FROM enrollments e
    JOIN members m ON e.member_id = m.id
    WHERE e.class_id = ?
      AND e.status = '수강중'
      AND m.status = '재원'
    ORDER BY m.name
    """

    students = pd.read_sql_query(students_query, conn, params=(class_id,))

    if students.empty:
        st.info("이 Class에 등록된 수강중 회원이 없습니다.")
        st.stop()

    existing_query = """
    SELECT member_id, status, memo
    FROM attendance
    WHERE attendance_date = ?
      AND class_id = ?
    """

    existing_attendance = pd.read_sql_query(
        existing_query,
        conn,
        params=(str(attendance_date), class_id)
    )

    existing_map = {}

    if not existing_attendance.empty:
        for _, row in existing_attendance.iterrows():
            existing_map[int(row["member_id"])] = {
                "status": row["status"],
                "memo": row["memo"]
            }

    st.divider()
    st.subheader("출석부")

    attendance_rows = []

    for _, row in students.iterrows():
        member_id = int(row["member_id"])

        saved_status = existing_map.get(member_id, {}).get("status", "결석")
        saved_memo = existing_map.get(member_id, {}).get("memo", "")

        default_checked = True if saved_status == "출석" else False

        col1, col2, col3, col4, col5 = st.columns([1.5, 1, 1.5, 1, 2])

        with col1:
            st.write(f"👤 **{row['회원명']}**")

        with col2:
            st.write(row["회원구분"])

        with col3:
            school_text = "" if pd.isna(row["학교"]) else row["학교"]
            grade_text = "" if pd.isna(row["학년"]) else row["학년"]
            st.write(f"{school_text} {grade_text}")

        with col4:
            checked = st.checkbox(
                "출석",
                value=default_checked,
                key=f"attendance_check_{class_id}_{member_id}"
            )

        with col5:
            memo = st.text_input(
                "메모",
                value="" if pd.isna(saved_memo) else saved_memo,
                key=f"attendance_memo_{class_id}_{member_id}"
            )

        status = "출석" if checked else "결석"

        attendance_rows.append({
            "member_id": member_id,
            "status": status,
            "memo": memo
        })

    st.divider()

    col_save, col_reset = st.columns(2)

    with col_save:
        if st.button("💾 출석 저장", use_container_width=True):
            for item in attendance_rows:
                cursor.execute("""
                DELETE FROM attendance
                WHERE attendance_date = ?
                  AND member_id = ?
                  AND class_id = ?
                """, (
                    str(attendance_date),
                    item["member_id"],
                    class_id
                ))

                cursor.execute("""
                INSERT INTO attendance
                (
                    attendance_date,
                    member_id,
                    class_id,
                    status,
                    memo
                )
                VALUES (?, ?, ?, ?, ?)
                """, (
                    str(attendance_date),
                    item["member_id"],
                    class_id,
                    item["status"],
                    item["memo"]
                ))

            conn.commit()
            st.success("출석 저장 완료")
            st.rerun()

    with col_reset:
        if st.button("🧹 오늘 이 Class 출석 초기화", use_container_width=True):
            cursor.execute("""
            DELETE FROM attendance
            WHERE attendance_date = ?
              AND class_id = ?
            """, (
                str(attendance_date),
                class_id
            ))

            conn.commit()
            st.success("출석 기록 초기화 완료")
            st.rerun()

# ----------------------
# 출석 기록 조회
# ----------------------
elif menu == "출석 기록 조회":
    st.subheader("출석 기록 조회")

    query = """
    SELECT
        a.id AS 출석번호,
        a.attendance_date AS 날짜,
        c.class_no AS "Class No.",
        c.category AS 구분,
        c.class_name AS "Class 명",
        i.instructor_name AS 강사,
        c.weekdays AS 요일,
        c.start_time AS "시간(시작)",
        c.end_time AS "시간(종료)",
        m.name AS 회원명,
        m.member_type AS 회원구분,
        m.school AS 학교,
        m.grade AS 학년,
        a.status AS 출석상태,
        a.memo AS 메모
    FROM attendance a
    LEFT JOIN members m ON a.member_id = m.id
    LEFT JOIN class_master c ON a.class_id = c.id
    LEFT JOIN instructors i ON c.instructor_id = i.id
    ORDER BY a.attendance_date DESC, c.class_name, m.name
    """

    attendance_df = pd.read_sql_query(query, conn)

    if attendance_df.empty:
        st.info("출석 기록이 없습니다.")
    else:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            search_member = st.text_input("회원명 검색")

        with col2:
            class_filter = st.selectbox(
                "Class 필터",
                ["전체"] + attendance_df["Class 명"].dropna().unique().tolist()
            )

        with col3:
            status_filter = st.selectbox(
                "출석상태 필터",
                ["전체", "출석", "결석"]
            )

        with col4:
            date_filter = st.date_input("날짜 선택", value=date.today())

        view_df = attendance_df.copy()

        if search_member:
            view_df = view_df[
                view_df["회원명"].str.contains(search_member, case=False, na=False)
            ]

        if class_filter != "전체":
            view_df = view_df[view_df["Class 명"] == class_filter]

        if status_filter != "전체":
            view_df = view_df[view_df["출석상태"] == status_filter]

        if date_filter:
            view_df = view_df[view_df["날짜"] == str(date_filter)]

        st.data_editor(
            view_df,
            use_container_width=True,
            hide_index=True,
            disabled=True,
            height=500
        )

        st.divider()

        st.subheader("출석 통계")

        total_count = len(view_df)
        present_count = len(view_df[view_df["출석상태"] == "출석"])
        absent_count = len(view_df[view_df["출석상태"] == "결석"])

        attendance_rate = round((present_count / total_count) * 100, 1) if total_count > 0 else 0

        col1, col2, col3 = st.columns(3)

        col1.metric("전체", total_count)
        col2.metric("출석", present_count)
        col3.metric("결석", absent_count)

        st.metric("출석률", f"{attendance_rate}%")