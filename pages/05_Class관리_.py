import streamlit as st
from utils.style import apply_custom_style
from utils.auth import login_check, logout_button
import sqlite3
import pandas as pd
from datetime import date

st.set_page_config(
    page_title="Class관리",
    page_icon="🏫",
    layout="wide"
)

apply_custom_style()
login_check()
logout_button()

conn = sqlite3.connect("members.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    class_id INTEGER,
    enroll_date TEXT,
    status TEXT,
    memo TEXT
)
""")
conn.commit()

st.title("🏫 Class관리")

menu = st.radio(
    "메뉴 선택",
    ["Class 목록", "Class별 회원 맵핑", "Class 등록현황"],
    horizontal=True
)

# ----------------------
# Class 목록
# ----------------------
if menu == "Class 목록":
    st.subheader("Class 전체 목록")

    query = """
    SELECT
        c.id AS 번호,
        c.class_no AS "Class No.",
        c.category AS 구분,
        c.class_name AS "Class 명",
        c.target AS 대상,
        i.instructor_name AS 강사,
        c.weekdays AS 요일,
        c.weekly_count AS 수업일수,
        c.start_date AS "수업기간(시작)",
        c.end_date AS "수업기간(종료)",
        c.start_time AS "시간(시작)",
        c.end_time AS "시간(종료)",
        c.duration AS 수업시간,
        c.tuition AS 수업료,
        c.active AS 사용여부
    FROM class_master c
    LEFT JOIN instructors i ON c.instructor_id = i.id
    ORDER BY c.id
    """

    classes = pd.read_sql_query(query, conn)

    if classes.empty:
        st.info("등록된 Class가 없습니다. 먼저 수업마스터에서 Class를 등록하세요.")
    else:
        st.data_editor(
            classes,
            use_container_width=True,
            hide_index=True,
            disabled=True,
            height=450
        )

# ----------------------
# Class별 회원 맵핑
# ----------------------
elif menu == "Class별 회원 맵핑":
    st.subheader("Class별 회원 맵핑")

    class_query = """
    SELECT
        c.id,
        c.class_no,
        c.class_name,
        c.category,
        c.target,
        i.instructor_name,
        c.weekdays,
        c.start_time,
        c.end_time,
        c.tuition
    FROM class_master c
    LEFT JOIN instructors i ON c.instructor_id = i.id
    WHERE c.active = 'Y'
    ORDER BY c.id
    """

    classes = pd.read_sql_query(class_query, conn)

    if classes.empty:
        st.info("사용 가능한 Class가 없습니다. 먼저 수업마스터에서 Class를 등록하세요.")
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
        f"{selected_class['weekdays']} / {selected_class['start_time']}~{selected_class['end_time']}"
    )

    st.divider()

    # 현재 Class에 등록된 회원
    enrolled_query = """
    SELECT
        e.id AS 등록번호,
        m.id AS 회원번호,
        m.name AS 회원명,
        m.member_type AS 회원구분,
        m.school AS 학교,
        m.grade AS 학년,
        m.phone AS 연락처,
        e.enroll_date AS 등록일,
        e.status AS 수강상태,
        e.memo AS 메모
    FROM enrollments e
    JOIN members m ON e.member_id = m.id
    WHERE e.class_id = ?
    ORDER BY m.name
    """

    enrolled_df = pd.read_sql_query(enrolled_query, conn, params=(class_id,))

    st.subheader("현재 Class 등록 회원")

    if enrolled_df.empty:
        st.info("현재 이 Class에 등록된 회원이 없습니다.")
    else:
        st.data_editor(
            enrolled_df,
            use_container_width=True,
            hide_index=True,
            disabled=True,
            height=300
        )

    st.divider()

    # 추가 가능한 회원
    available_query = """
    SELECT
        m.id AS 회원번호,
        m.name AS 회원명,
        m.member_type AS 회원구분,
        m.school AS 학교,
        m.grade AS 학년,
        m.phone AS 연락처,
        m.status AS 회원상태
    FROM members m
    WHERE m.status = '재원'
      AND m.id NOT IN (
          SELECT member_id
          FROM enrollments
          WHERE class_id = ?
            AND status = '수강중'
      )
    ORDER BY m.name
    """

    available_df = pd.read_sql_query(available_query, conn, params=(class_id,))

    st.subheader("회원 추가 맵핑")

    if available_df.empty:
        st.info("추가 가능한 재원 회원이 없습니다.")
    else:
        mapping_df = available_df.copy()
        mapping_df["선택"] = False

        mapping_df = mapping_df[[
            "선택", "회원번호", "회원명", "회원구분", "학교", "학년", "연락처", "회원상태"
        ]]

        edited_df = st.data_editor(
            mapping_df,
            use_container_width=True,
            hide_index=True,
            height=350,
            column_config={
                "선택": st.column_config.CheckboxColumn("선택"),
                "회원번호": st.column_config.NumberColumn(width="small", disabled=True),
                "회원명": st.column_config.TextColumn(width="medium", disabled=True),
                "회원구분": st.column_config.TextColumn(width="small", disabled=True),
                "학교": st.column_config.TextColumn(width="medium", disabled=True),
                "학년": st.column_config.TextColumn(width="small", disabled=True),
                "연락처": st.column_config.TextColumn(width="medium", disabled=True),
                "회원상태": st.column_config.TextColumn(width="small", disabled=True),
            }
        )

        selected_members = edited_df[edited_df["선택"] == True]

        st.write(f"선택된 회원 수: {len(selected_members)}명")

        enroll_date = st.date_input("수강 시작일", value=date.today())
        memo = st.text_area("공통 메모")

        if st.button("선택 회원 Class 등록", use_container_width=True):
            if selected_members.empty:
                st.warning("선택된 회원이 없습니다.")
            else:
                save_count = 0
                skip_count = 0

                for _, row in selected_members.iterrows():
                    member_id = int(row["회원번호"])

                    exists = cursor.execute("""
                    SELECT COUNT(*)
                    FROM enrollments
                    WHERE member_id = ?
                      AND class_id = ?
                      AND status = '수강중'
                    """, (member_id, class_id)).fetchone()[0]

                    if exists > 0:
                        skip_count += 1
                        continue

                    cursor.execute("""
                    INSERT INTO enrollments
                    (
                        member_id,
                        class_id,
                        enroll_date,
                        status,
                        memo
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        member_id,
                        class_id,
                        str(enroll_date),
                        "수강중",
                        memo
                    ))

                    save_count += 1

                conn.commit()
                st.success(f"Class 맵핑 완료: {save_count}명 등록 / {skip_count}명 중복 제외")
                st.rerun()

    st.divider()

    # 등록된 회원 상태 변경/삭제
    st.subheader("등록 회원 상태 변경 / 삭제")

    if enrolled_df.empty:
        st.info("상태 변경 또는 삭제할 회원이 없습니다.")
    else:
        selected_enroll_label = st.selectbox(
            "변경할 등록 회원 선택",
            enrolled_df.apply(
                lambda x: f"{x['등록번호']} - {x['회원명']} - {x['수강상태']}",
                axis=1
            )
        )

        selected_enroll_id = int(selected_enroll_label.split(" - ")[0])

        new_status = st.selectbox("수강상태 변경", ["수강중", "휴강", "종료"])
        new_memo = st.text_area("메모 변경")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 상태 저장", use_container_width=True):
                cursor.execute("""
                UPDATE enrollments
                SET status = ?, memo = ?
                WHERE id = ?
                """, (
                    new_status,
                    new_memo,
                    selected_enroll_id
                ))

                conn.commit()
                st.success("수강상태 변경 완료")
                st.rerun()

        with col2:
            if st.button("🗑 Class 맵핑 삭제", use_container_width=True):
                cursor.execute(
                    "DELETE FROM enrollments WHERE id = ?",
                    (selected_enroll_id,)
                )

                conn.commit()
                st.success("Class 맵핑 삭제 완료")
                st.rerun()

# ----------------------
# Class 등록현황
# ----------------------
elif menu == "Class 등록현황":
    st.subheader("Class 등록현황")

    query = """
    SELECT
        e.id AS 등록번호,
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
        m.phone AS 연락처,
        e.enroll_date AS 수강시작일,
        e.status AS 수강상태,
        e.memo AS 메모
    FROM enrollments e
    JOIN members m ON e.member_id = m.id
    JOIN class_master c ON e.class_id = c.id
    LEFT JOIN instructors i ON c.instructor_id = i.id
    ORDER BY c.class_name, m.name
    """

    enroll_df = pd.read_sql_query(query, conn)

    if enroll_df.empty:
        st.info("등록된 Class 수강현황이 없습니다.")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            search_member = st.text_input("회원명 검색")

        with col2:
            class_filter = st.selectbox(
                "Class 필터",
                ["전체"] + enroll_df["Class 명"].dropna().unique().tolist()
            )

        with col3:
            status_filter = st.selectbox(
                "수강상태 필터",
                ["전체", "수강중", "휴강", "종료"]
            )

        view_df = enroll_df.copy()

        if search_member:
            view_df = view_df[
                view_df["회원명"].str.contains(search_member, case=False, na=False)
            ]

        if class_filter != "전체":
            view_df = view_df[view_df["Class 명"] == class_filter]

        if status_filter != "전체":
            view_df = view_df[view_df["수강상태"] == status_filter]

        st.data_editor(
            view_df,
            use_container_width=True,
            hide_index=True,
            disabled=True,
            height=500
        )