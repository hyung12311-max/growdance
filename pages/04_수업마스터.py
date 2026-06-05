import streamlit as st
from utils.style import apply_custom_style
from utils.auth import login_check, logout_button
import sqlite3
import pandas as pd
from datetime import date, time

st.set_page_config(
    page_title="수업마스터",
    page_icon="📚",
    layout="wide"
)

apply_custom_style()
login_check()
logout_button()

conn = sqlite3.connect("members.db", check_same_thread=False)
cursor = conn.cursor()

# 기존 테이블이 있어도 새 컬럼 구조를 사용할 수 있도록 생성
cursor.execute("""
CREATE TABLE IF NOT EXISTS class_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_no TEXT,
    category TEXT,
    class_name TEXT,
    target TEXT,
    instructor_id INTEGER,
    weekdays TEXT,
    weekly_count TEXT,
    start_date TEXT,
    end_date TEXT,
    start_time TEXT,
    end_time TEXT,
    duration TEXT,
    tuition INTEGER,
    three_month_tuition INTEGER,
    memo TEXT,
    active TEXT
)
""")
conn.commit()

st.title("📚 수업마스터")

if "show_class_form" not in st.session_state:
    st.session_state.show_class_form = False

if "show_class_edit_form" not in st.session_state:
    st.session_state.show_class_edit_form = False

# 강사 목록
try:
    instructors = pd.read_sql_query(
        "SELECT id, instructor_name FROM instructors WHERE status='재직' ORDER BY instructor_name",
        conn
    )
except:
    instructors = pd.DataFrame(columns=["id", "instructor_name"])

classes = pd.read_sql_query("SELECT * FROM class_master ORDER BY id", conn)

st.subheader("수업마스터 전체 목록")

if classes.empty:
    st.info("등록된 수업마스터가 없습니다.")
else:
    query = """
    SELECT
        c.id AS No,
        c.class_no AS "Class No.",
        c.category AS "구분",
        c.class_name AS "Class 명",
        c.target AS "대상",
        i.instructor_name AS "강사",
        c.weekdays AS "요일",
        c.weekly_count AS "수업일수",
        c.start_date AS "수업기간(시작)",
        c.end_date AS "수업기간(종료)",
        c.start_time AS "시간(시작)",
        c.end_time AS "시간(종료)",
        c.duration AS "수업시간",
        c.tuition AS "수업료",
        c.three_month_tuition AS "수업료(3개월)",
        c.active AS "사용여부",
        c.memo AS "메모"
    FROM class_master c
    LEFT JOIN instructors i ON c.instructor_id = i.id
    ORDER BY c.id
    """

    view_df = pd.read_sql_query(query, conn)

    st.data_editor(
        view_df,
        use_container_width=True,
        hide_index=True,
        disabled=True,
        height=420,
        column_config={
            "No": st.column_config.NumberColumn(width="small"),
            "Class No.": st.column_config.TextColumn(width="small"),
            "구분": st.column_config.TextColumn(width="medium"),
            "Class 명": st.column_config.TextColumn(width="medium"),
            "대상": st.column_config.TextColumn(width="small"),
            "강사": st.column_config.TextColumn(width="medium"),
            "요일": st.column_config.TextColumn(width="medium"),
            "수업일수": st.column_config.TextColumn(width="small"),
            "수업기간(시작)": st.column_config.TextColumn(width="medium"),
            "수업기간(종료)": st.column_config.TextColumn(width="medium"),
            "시간(시작)": st.column_config.TextColumn(width="small"),
            "시간(종료)": st.column_config.TextColumn(width="small"),
            "수업시간": st.column_config.TextColumn(width="small"),
            "수업료": st.column_config.NumberColumn(width="medium", format="%d원"),
            "수업료(3개월)": st.column_config.NumberColumn(width="medium", format="%d원"),
            "사용여부": st.column_config.TextColumn(width="small"),
            "메모": st.column_config.TextColumn(width="large"),
        }
    )

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("➕ 수업 등록", use_container_width=True):
        st.session_state.show_class_form = True
        st.session_state.show_class_edit_form = False

with col2:
    if st.button("✏️ 수업 수정/삭제", use_container_width=True):
        st.session_state.show_class_edit_form = True
        st.session_state.show_class_form = False

with col3:
    if st.button("닫기", use_container_width=True):
        st.session_state.show_class_form = False
        st.session_state.show_class_edit_form = False


def calc_duration(start_t, end_t):
    start_minutes = start_t.hour * 60 + start_t.minute
    end_minutes = end_t.hour * 60 + end_t.minute
    diff = end_minutes - start_minutes

    if diff <= 0:
        return "0:00"

    h = diff // 60
    m = diff % 60
    return f"{h}:{m:02d}"


def make_class_no():
    next_id = cursor.execute(
        "SELECT COUNT(*) FROM class_master"
    ).fetchone()[0] + 1

    return f"CLASS{next_id:03d}"


category_options = ["Street Dance", "K-pop", "Fitness"]

class_name_options = [
    "키즈댄스",
    "방송댄스",
    "힙합",
    "하우스",
    "셔플",
    "퍼포먼스",
    "Waacking"
]

target_options = [
    "유아",
    "저학년",
    "고학년",
    "초등",
    "중고등",
    "성인",
    "14세 이상",
    "전체"
]

weekday_options = ["월", "화", "수", "목", "금", "토", "일"]

active_options = ["Y", "N"]

# ----------------------
# 수업 등록
# ----------------------
if st.session_state.show_class_form:
    st.subheader("수업 등록")

    col1, col2 = st.columns(2)

    with col1:
        category = st.selectbox("구분", category_options)

        class_name = st.selectbox("Class 명", class_name_options)

        target = st.selectbox("대상", target_options)

        if instructors.empty:
            st.warning("등록된 재직 강사가 없습니다. 먼저 강사관리에 강사를 등록하세요.")
            instructor_id = None
        else:
            instructor_label = st.selectbox(
                "강사",
                instructors.apply(lambda x: f"{x['id']} - {x['instructor_name']}", axis=1)
            )
            instructor_id = int(instructor_label.split(" - ")[0])

        weekdays = st.multiselect(
            "요일 선택",
            weekday_options,
            max_selections=5
        )

        weekly_count = f"{len(weekdays)}회/주" if len(weekdays) > 0 else ""

    with col2:
        start_date = st.date_input("수업기간(시작)", value=date.today())
        end_date = st.date_input("수업기간(종료)", value=date.today())

        start_time = st.time_input("시간(시작)", value=time(19, 0))
        end_time = st.time_input("시간(종료)", value=time(20, 0))

        duration = calc_duration(start_time, end_time)

        tuition = st.number_input(
            "수업료",
            min_value=0,
            step=10000,
            value=0
        )

        three_month_tuition = st.number_input(
            "수업료(3개월)",
            min_value=0,
            step=10000,
            value=0
        )

        active = st.selectbox("사용여부", active_options)
        memo = st.text_area("메모")

    st.info(f"선택 요일: {', '.join(weekdays) if weekdays else '미선택'} / 수업일수: {weekly_count} / 수업시간: {duration}")

    if st.button("수업 저장", use_container_width=True):
        if not weekdays:
            st.warning("요일은 최소 1개 이상 선택하세요.")
        elif len(weekdays) > 5:
            st.warning("요일은 최대 5개까지 선택 가능합니다.")
        elif instructor_id is None:
            st.warning("강사를 선택하세요.")
        else:
            class_no = make_class_no()

            cursor.execute("""
            INSERT INTO class_master
            (
                class_no,
                category,
                class_name,
                target,
                instructor_id,
                weekdays,
                weekly_count,
                start_date,
                end_date,
                start_time,
                end_time,
                duration,
                tuition,
                three_month_tuition,
                memo,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                class_no,
                category,
                class_name,
                target,
                instructor_id,
                ",".join(weekdays),
                weekly_count,
                str(start_date),
                str(end_date),
                str(start_time)[:5],
                str(end_time)[:5],
                duration,
                tuition,
                three_month_tuition,
                memo,
                active
            ))

            conn.commit()
            st.session_state.show_class_form = False
            st.success("수업 등록 완료")
            st.rerun()

# ----------------------
# 수업 수정 / 삭제
# ----------------------
if st.session_state.show_class_edit_form:
    st.subheader("수업 수정 / 삭제")

    all_classes = pd.read_sql_query("SELECT * FROM class_master ORDER BY id", conn)

    if all_classes.empty:
        st.info("수정할 수업이 없습니다.")
    else:
        class_label = st.selectbox(
            "수정 또는 삭제할 수업 선택",
            all_classes.apply(lambda x: f"{x['id']} - {x['class_no']} - {x['class_name']}", axis=1)
        )

        selected_id = int(class_label.split(" - ")[0])

        selected = pd.read_sql_query(
            "SELECT * FROM class_master WHERE id=?",
            conn,
            params=(selected_id,)
        ).iloc[0]

        col1, col2 = st.columns(2)

        with col1:
            category = st.selectbox(
                "구분",
                category_options,
                index=category_options.index(selected["category"])
                if selected["category"] in category_options else 0
            )

            class_name = st.selectbox(
                "Class 명",
                class_name_options,
                index=class_name_options.index(selected["class_name"])
                if selected["class_name"] in class_name_options else 0
            )

            target = st.selectbox(
                "대상",
                target_options,
                index=target_options.index(selected["target"])
                if selected["target"] in target_options else 0
            )

            if instructors.empty:
                st.warning("등록된 재직 강사가 없습니다.")
                instructor_id = None
            else:
                instructor_options = instructors.apply(
                    lambda x: f"{x['id']} - {x['instructor_name']}",
                    axis=1
                ).tolist()

                selected_index = 0
                for idx, label in enumerate(instructor_options):
                    if label.startswith(f"{selected['instructor_id']} - "):
                        selected_index = idx
                        break

                instructor_label = st.selectbox(
                    "강사",
                    instructor_options,
                    index=selected_index
                )

                instructor_id = int(instructor_label.split(" - ")[0])

            current_weekdays = []
            if pd.notna(selected["weekdays"]) and selected["weekdays"] != "":
                current_weekdays = selected["weekdays"].split(",")

            weekdays = st.multiselect(
                "요일 선택",
                weekday_options,
                default=current_weekdays,
                max_selections=5
            )

            weekly_count = f"{len(weekdays)}회/주" if len(weekdays) > 0 else ""

        with col2:
            start_date = st.date_input(
                "수업기간(시작)",
                value=pd.to_datetime(selected["start_date"]).date()
                if pd.notna(selected["start_date"]) and selected["start_date"] != ""
                else date.today()
            )

            end_date = st.date_input(
                "수업기간(종료)",
                value=pd.to_datetime(selected["end_date"]).date()
                if pd.notna(selected["end_date"]) and selected["end_date"] != ""
                else date.today()
            )

            try:
                start_hour, start_minute = str(selected["start_time"]).split(":")
                start_default = time(int(start_hour), int(start_minute))
            except:
                start_default = time(19, 0)

            try:
                end_hour, end_minute = str(selected["end_time"]).split(":")
                end_default = time(int(end_hour), int(end_minute))
            except:
                end_default = time(20, 0)

            start_time = st.time_input("시간(시작)", value=start_default)
            end_time = st.time_input("시간(종료)", value=end_default)

            duration = calc_duration(start_time, end_time)

            tuition = st.number_input(
                "수업료",
                min_value=0,
                step=10000,
                value=int(selected["tuition"]) if pd.notna(selected["tuition"]) else 0
            )

            three_month_tuition = st.number_input(
                "수업료(3개월)",
                min_value=0,
                step=10000,
                value=int(selected["three_month_tuition"]) if pd.notna(selected["three_month_tuition"]) else 0
            )

            active = st.selectbox(
                "사용여부",
                active_options,
                index=active_options.index(selected["active"])
                if selected["active"] in active_options else 0
            )

            memo = st.text_area(
                "메모",
                selected["memo"] if pd.notna(selected["memo"]) else ""
            )

        st.info(f"선택 요일: {', '.join(weekdays) if weekdays else '미선택'} / 수업일수: {weekly_count} / 수업시간: {duration}")

        col_save, col_delete = st.columns(2)

        with col_save:
            if st.button("💾 수정 저장", use_container_width=True):
                if not weekdays:
                    st.warning("요일은 최소 1개 이상 선택하세요.")
                elif len(weekdays) > 5:
                    st.warning("요일은 최대 5개까지 선택 가능합니다.")
                elif instructor_id is None:
                    st.warning("강사를 선택하세요.")
                else:
                    cursor.execute("""
                    UPDATE class_master
                    SET
                        category=?,
                        class_name=?,
                        target=?,
                        instructor_id=?,
                        weekdays=?,
                        weekly_count=?,
                        start_date=?,
                        end_date=?,
                        start_time=?,
                        end_time=?,
                        duration=?,
                        tuition=?,
                        three_month_tuition=?,
                        memo=?,
                        active=?
                    WHERE id=?
                    """, (
                        category,
                        class_name,
                        target,
                        instructor_id,
                        ",".join(weekdays),
                        weekly_count,
                        str(start_date),
                        str(end_date),
                        str(start_time)[:5],
                        str(end_time)[:5],
                        duration,
                        tuition,
                        three_month_tuition,
                        memo,
                        active,
                        selected_id
                    ))

                    conn.commit()
                    st.success("수업 수정 완료")
                    st.rerun()

        with col_delete:
            if st.button("🗑 삭제", use_container_width=True):
                cursor.execute(
                    "DELETE FROM class_master WHERE id=?",
                    (selected_id,)
                )
                conn.commit()
                st.success("수업 삭제 완료")
                st.rerun()