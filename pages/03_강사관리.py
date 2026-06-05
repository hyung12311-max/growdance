import streamlit as st
from utils.style import apply_custom_style
from utils.auth import login_check, logout_button
import sqlite3
import pandas as pd
from datetime import date

st.set_page_config(
    page_title="강사관리",
    page_icon="👨‍🏫",
    layout="wide"
)

apply_custom_style()
login_check()
logout_button()

conn = sqlite3.connect("members.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS instructors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instructor_code TEXT,
    instructor_name TEXT,
    instructor_type TEXT,
    phone TEXT,
    genre TEXT,
    hire_date TEXT,
    status TEXT,
    memo TEXT
)
""")
conn.commit()

st.title("👨‍🏫 강사관리")

if "show_instructor_form" not in st.session_state:
    st.session_state.show_instructor_form = False

if "show_instructor_edit_form" not in st.session_state:
    st.session_state.show_instructor_edit_form = False

df = pd.read_sql_query("SELECT * FROM instructors ORDER BY id", conn)

st.subheader("강사 전체 목록")

if df.empty:
    st.info("등록된 강사가 없습니다.")
else:
    search = st.text_input("강사 검색")

    if search:
        df = df[df["instructor_name"].str.contains(search, case=False, na=False)]

    view_df = df.copy()

    view_df = view_df.rename(columns={
        "id": "번호",
        "instructor_code": "강사코드",
        "instructor_name": "강사명",
        "instructor_type": "구분",
        "phone": "연락처",
        "genre": "담당장르",
        "hire_date": "입사일",
        "status": "상태",
        "memo": "메모"
    })

    show_df = view_df[[
        "번호", "강사코드", "구분", "강사명",
        "연락처", "담당장르", "입사일", "상태", "메모"
    ]]

    st.data_editor(
        show_df,
        use_container_width=True,
        hide_index=True,
        disabled=True,
        height=420,
        column_config={
            "번호": st.column_config.NumberColumn(width="small"),
            "강사코드": st.column_config.TextColumn(width="small"),
            "구분": st.column_config.TextColumn(width="small"),
            "강사명": st.column_config.TextColumn(width="medium"),
            "연락처": st.column_config.TextColumn(width="medium"),
            "담당장르": st.column_config.TextColumn(width="medium"),
            "입사일": st.column_config.TextColumn(width="medium"),
            "상태": st.column_config.TextColumn(width="small"),
            "메모": st.column_config.TextColumn(width="large"),
        }
    )

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("➕ 강사 등록", use_container_width=True):
        st.session_state.show_instructor_form = True
        st.session_state.show_instructor_edit_form = False

with col2:
    if st.button("✏️ 강사 수정/삭제", use_container_width=True):
        st.session_state.show_instructor_edit_form = True
        st.session_state.show_instructor_form = False

with col3:
    if st.button("닫기", use_container_width=True):
        st.session_state.show_instructor_form = False
        st.session_state.show_instructor_edit_form = False

# ----------------------
# 강사 등록
# ----------------------
if st.session_state.show_instructor_form:
    st.subheader("강사 등록")

    col1, col2 = st.columns(2)

    with col1:
        instructor_name = st.text_input("강사명")
        instructor_type = st.selectbox("구분", ["원장", "강사"])
        phone = st.text_input("연락처")
        genre = st.selectbox(
            "담당장르",
            ["House", "Shuffle", "K-POP", "HipHop", "Kids", "Performance", "기타"]
        )

    with col2:
        hire_date = st.date_input("입사일", value=date.today())
        status = st.selectbox("상태", ["재직", "휴직", "퇴사"])
        memo = st.text_area("메모")

    if st.button("강사 저장", use_container_width=True):
        if instructor_name.strip() == "":
            st.warning("강사명을 입력하세요.")
        else:
            next_id = cursor.execute(
                "SELECT COUNT(*) FROM instructors"
            ).fetchone()[0] + 1

            instructor_code = f"T{next_id:03d}"

            cursor.execute("""
            INSERT INTO instructors
            (
                instructor_code,
                instructor_name,
                instructor_type,
                phone,
                genre,
                hire_date,
                status,
                memo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                instructor_code,
                instructor_name,
                instructor_type,
                phone,
                genre,
                str(hire_date),
                status,
                memo
            ))

            conn.commit()
            st.session_state.show_instructor_form = False
            st.success("강사 등록 완료")
            st.rerun()

# ----------------------
# 강사 수정 / 삭제
# ----------------------
if st.session_state.show_instructor_edit_form:
    st.subheader("강사 수정 / 삭제")

    all_instructors = pd.read_sql_query(
        "SELECT * FROM instructors ORDER BY id",
        conn
    )

    if all_instructors.empty:
        st.info("수정할 강사가 없습니다.")
    else:
        instructor_label = st.selectbox(
            "수정 또는 삭제할 강사 선택",
            all_instructors.apply(
                lambda x: f"{x['id']} - {x['instructor_type']} - {x['instructor_name']}",
                axis=1
            )
        )

        selected_id = int(instructor_label.split(" - ")[0])

        selected = pd.read_sql_query(
            "SELECT * FROM instructors WHERE id=?",
            conn,
            params=(selected_id,)
        ).iloc[0]

        col1, col2 = st.columns(2)

        with col1:
            instructor_name = st.text_input(
                "강사명",
                selected["instructor_name"] if pd.notna(selected["instructor_name"]) else ""
            )

            type_options = ["원장", "강사"]
            instructor_type = st.selectbox(
                "구분",
                type_options,
                index=type_options.index(selected["instructor_type"])
                if selected["instructor_type"] in type_options else 1
            )

            phone = st.text_input(
                "연락처",
                selected["phone"] if pd.notna(selected["phone"]) else ""
            )

            genre_options = [
                "House", "Shuffle", "K-POP", "HipHop",
                "Kids", "Performance", "기타"
            ]

            genre = st.selectbox(
                "담당장르",
                genre_options,
                index=genre_options.index(selected["genre"])
                if selected["genre"] in genre_options else 0
            )

        with col2:
            hire_date = st.date_input(
                "입사일",
                value=pd.to_datetime(selected["hire_date"]).date()
                if pd.notna(selected["hire_date"]) and selected["hire_date"] != ""
                else date.today()
            )

            status_options = ["재직", "휴직", "퇴사"]

            status = st.selectbox(
                "상태",
                status_options,
                index=status_options.index(selected["status"])
                if selected["status"] in status_options else 0
            )

            memo = st.text_area(
                "메모",
                selected["memo"] if pd.notna(selected["memo"]) else ""
            )

        col_save, col_delete = st.columns(2)

        with col_save:
            if st.button("💾 수정 저장", use_container_width=True):
                if instructor_name.strip() == "":
                    st.warning("강사명을 입력하세요.")
                else:
                    cursor.execute("""
                    UPDATE instructors
                    SET
                        instructor_name=?,
                        instructor_type=?,
                        phone=?,
                        genre=?,
                        hire_date=?,
                        status=?,
                        memo=?
                    WHERE id=?
                    """, (
                        instructor_name,
                        instructor_type,
                        phone,
                        genre,
                        str(hire_date),
                        status,
                        memo,
                        selected_id
                    ))

                    conn.commit()
                    st.success("강사 정보 수정 완료")
                    st.rerun()

        with col_delete:
            if st.button("🗑 삭제", use_container_width=True):
                cursor.execute(
                    "DELETE FROM instructors WHERE id=?",
                    (selected_id,)
                )
                conn.commit()
                st.success("강사 삭제 완료")
                st.rerun()