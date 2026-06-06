import streamlit as st
from utils.style import apply_custom_style
from utils.auth import login_check, logout_button
import sqlite3
import pandas as pd
from datetime import date
from io import BytesIO

st.set_page_config(
    page_title="회원관리",
    page_icon="👥",
    layout="wide"
)

apply_custom_style()
login_check()
logout_button()

conn = sqlite3.connect("members.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    gender TEXT,
    birth_date TEXT,
    member_type TEXT,
    phone TEXT,
    parent_name TEXT,
    parent_phone TEXT,
    school TEXT,
    grade TEXT,
    dance_class TEXT,
    join_date TEXT,
    status TEXT,
    memo TEXT
)
""")
conn.commit()

st.title("👥 회원관리")

def calculate_grade(birth_date_value, member_type):
    if member_type == "성인":
        return "성인"

    try:
        birth_year = pd.to_datetime(birth_date_value).year
    except:
        return "미계산"

    current_year = date.today().year
    age_korean = current_year - birth_year + 1
    elementary_grade = current_year - (birth_year + 7) + 1

    if age_korean <= 7:
        return "유치부"
    elif 1 <= elementary_grade <= 6:
        return f"초{elementary_grade}"
    elif elementary_grade == 7:
        return "중1"
    elif elementary_grade == 8:
        return "중2"
    elif elementary_grade == 9:
        return "중3"
    elif elementary_grade == 10:
        return "고1"
    elif elementary_grade == 11:
        return "고2"
    elif elementary_grade == 12:
        return "고3"
    else:
        return "성인"

for key in [
    "show_member_form",
    "show_member_edit_form",
    "show_excel_upload",
    "confirm_bulk_delete"
]:
    if key not in st.session_state:
        st.session_state[key] = False

df = pd.read_sql_query("SELECT * FROM members ORDER BY id", conn)

st.subheader("회원 전체 목록")

selected_ids = []
selected_names = []

if df.empty:
    st.info("등록된 회원이 없습니다.")
else:
    search = st.text_input("회원 검색")

    if search:
        df = df[df["name"].str.contains(search, case=False, na=False)]

    df["자동학년"] = df.apply(
        lambda row: calculate_grade(row["birth_date"], row["member_type"]),
        axis=1
    )

    view_df = df.copy()
    view_df["선택"] = False

    view_df = view_df.rename(columns={
        "id": "번호",
        "name": "회원명",
        "gender": "성별",
        "birth_date": "생년월일",
        "member_type": "회원구분",
        "phone": "연락처",
        "parent_name": "보호자명",
        "parent_phone": "보호자 연락처",
        "school": "학교",
        "join_date": "가입일",
        "status": "회원상태",
        "memo": "메모"
    })

    show_df = view_df[[
        "선택", "번호", "회원명", "성별", "생년월일", "회원구분",
        "연락처", "보호자명", "보호자 연락처",
        "학교", "자동학년", "가입일", "회원상태", "메모"
    ]]

    edited_df = st.data_editor(
        show_df,
        use_container_width=True,
        hide_index=True,
        height=420,
        column_config={
            "선택": st.column_config.CheckboxColumn("선택"),
            "번호": st.column_config.NumberColumn(width="small", disabled=True),
            "회원명": st.column_config.TextColumn(width="medium", disabled=True),
            "성별": st.column_config.TextColumn(width="small", disabled=True),
            "생년월일": st.column_config.TextColumn(width="medium", disabled=True),
            "회원구분": st.column_config.TextColumn(width="small", disabled=True),
            "연락처": st.column_config.TextColumn(width="medium", disabled=True),
            "보호자명": st.column_config.TextColumn(width="medium", disabled=True),
            "보호자 연락처": st.column_config.TextColumn(width="medium", disabled=True),
            "학교": st.column_config.TextColumn(width="medium", disabled=True),
            "자동학년": st.column_config.TextColumn(width="small", disabled=True),
            "가입일": st.column_config.TextColumn(width="medium", disabled=True),
            "회원상태": st.column_config.TextColumn(width="small", disabled=True),
            "메모": st.column_config.TextColumn(width="large", disabled=True),
        }
    )

    selected_rows = edited_df[edited_df["선택"] == True]
    selected_ids = selected_rows["번호"].tolist()
    selected_names = selected_rows["회원명"].tolist()

    st.write(f"선택된 회원 수: {len(selected_ids)}명")

    st.divider()
    st.subheader("선택 회원 일괄 수정 / 삭제")

    col_u1, col_u2, col_u3, col_u4 = st.columns(4)

    with col_u1:
        update_target = st.selectbox(
            "변경할 항목",
            ["회원상태", "회원구분", "학교", "메모"]
        )

    with col_u2:
        if update_target == "회원상태":
            new_value = st.selectbox("변경값", ["재원", "휴원", "퇴원"])
        elif update_target == "회원구분":
            new_value = st.selectbox("변경값", ["학생", "성인"])
        else:
            new_value = st.text_input("변경값")

    with col_u3:
        st.write("")
        st.write("")
        if st.button("선택 회원 일괄 수정", use_container_width=True):
            if len(selected_ids) == 0:
                st.warning("선택된 회원이 없습니다.")
            elif update_target in ["학교", "메모"] and str(new_value).strip() == "":
                st.warning("변경값을 입력하세요.")
            else:
                column_map = {
                    "회원상태": "status",
                    "회원구분": "member_type",
                    "학교": "school",
                    "메모": "memo"
                }

                db_col = column_map[update_target]

                for member_id in selected_ids:
                    cursor.execute(
                        f"UPDATE members SET {db_col}=? WHERE id=?",
                        (new_value, int(member_id))
                    )

                    if update_target == "회원구분" and new_value == "성인":
                        cursor.execute(
                            """
                            UPDATE members
                            SET parent_name='', parent_phone='', school='', grade='성인'
                            WHERE id=?
                            """,
                            (int(member_id),)
                        )

                conn.commit()
                st.success(f"{len(selected_ids)}명 회원 일괄 수정 완료")
                st.rerun()

    with col_u4:
        st.write("")
        st.write("")
        if st.button("선택 회원 일괄 삭제", use_container_width=True):
            if len(selected_ids) == 0:
                st.warning("선택된 회원이 없습니다.")
            else:
                st.session_state.confirm_bulk_delete = True
                st.session_state.bulk_delete_ids = selected_ids
                st.session_state.bulk_delete_names = selected_names
                st.rerun()

    if st.session_state.confirm_bulk_delete:
        st.warning(f"선택한 회원 {len(st.session_state.bulk_delete_ids)}명을 삭제하시겠습니까?")

        delete_names = st.session_state.bulk_delete_names

        if delete_names:
            st.write("삭제 대상:")
            st.write(", ".join(delete_names))

        col_yes, col_no = st.columns(2)

        with col_yes:
            if st.button("예, 삭제합니다", use_container_width=True):
                for member_id in st.session_state.bulk_delete_ids:
                    cursor.execute(
                        "DELETE FROM members WHERE id=?",
                        (int(member_id),)
                    )

                conn.commit()
                st.session_state.confirm_bulk_delete = False
                st.session_state.bulk_delete_ids = []
                st.session_state.bulk_delete_names = []
                st.success("선택 회원 삭제 완료")
                st.rerun()

        with col_no:
            if st.button("취소", use_container_width=True):
                st.session_state.confirm_bulk_delete = False
                st.session_state.bulk_delete_ids = []
                st.session_state.bulk_delete_names = []
                st.rerun()

st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("➕ 회원 등록", use_container_width=True):
        st.session_state.show_member_form = True
        st.session_state.show_member_edit_form = False
        st.session_state.show_excel_upload = False

with col2:
    if st.button("📤 엑셀 업로드", use_container_width=True):
        st.session_state.show_excel_upload = True
        st.session_state.show_member_form = False
        st.session_state.show_member_edit_form = False

with col3:
    if st.button("✏️ 회원 개별 수정/삭제", use_container_width=True):
        st.session_state.show_member_edit_form = True
        st.session_state.show_member_form = False
        st.session_state.show_excel_upload = False

with col4:
    if st.button("닫기", use_container_width=True):
        st.session_state.show_member_form = False
        st.session_state.show_member_edit_form = False
        st.session_state.show_excel_upload = False
        st.session_state.confirm_bulk_delete = False

# ----------------------
# 엑셀 업로드
# ----------------------
if st.session_state.show_excel_upload:
    st.subheader("회원 엑셀 업로드")

    template_df = pd.DataFrame(columns=[
        "회원명", "성별", "생년월일", "회원구분", "연락처",
        "보호자명", "보호자 연락처", "학교",
        "가입일", "회원상태", "메모"
    ])

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        template_df.to_excel(writer, index=False, sheet_name="회원등록양식")

    st.download_button(
        label="📥 회원등록 엑셀 양식 다운로드",
        data=output.getvalue(),
        file_name="회원등록양식.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    uploaded_file = st.file_uploader(
        "회원 엑셀 파일 업로드",
        type=["xlsx"]
    )

    if uploaded_file is not None:
        upload_df = pd.read_excel(uploaded_file)

        required_cols = [
            "회원명", "성별", "생년월일", "회원구분", "연락처",
            "보호자명", "보호자 연락처", "학교",
            "가입일", "회원상태", "메모"
        ]

        missing_cols = [col for col in required_cols if col not in upload_df.columns]

        if missing_cols:
            st.error(f"누락된 컬럼이 있습니다: {missing_cols}")
        else:
            st.write("업로드 미리보기")
            st.dataframe(upload_df, use_container_width=True, hide_index=True)

            if st.button("엑셀 회원 저장", use_container_width=True):
                save_count = 0
                skip_count = 0

                for _, row in upload_df.iterrows():
                    name = str(row["회원명"]).strip()

                    if name == "" or name == "nan":
                        skip_count += 1
                        continue

                    phone = "" if pd.isna(row["연락처"]) else str(row["연락처"]).strip()
                    member_type = "" if pd.isna(row["회원구분"]) else str(row["회원구분"]).strip()
                    birth_date_value = "" if pd.isna(row["생년월일"]) else str(row["생년월일"])[:10]
                    grade = calculate_grade(birth_date_value, member_type)

                    duplicate = cursor.execute("""
                    SELECT COUNT(*)
                    FROM members
                    WHERE name = ? AND phone = ?
                    """, (name, phone)).fetchone()[0]

                    if duplicate > 0:
                        skip_count += 1
                        continue

                    cursor.execute("""
                    INSERT INTO members
                    (
                        name, gender, birth_date, member_type, phone,
                        parent_name, parent_phone, school, grade,
                        dance_class, join_date, status, memo
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        name,
                        "" if pd.isna(row["성별"]) else str(row["성별"]),
                        birth_date_value,
                        member_type,
                        phone,
                        "" if pd.isna(row["보호자명"]) else str(row["보호자명"]),
                        "" if pd.isna(row["보호자 연락처"]) else str(row["보호자 연락처"]),
                        "" if pd.isna(row["학교"]) else str(row["학교"]),
                        grade,
                        "",
                        "" if pd.isna(row["가입일"]) else str(row["가입일"])[:10],
                        "" if pd.isna(row["회원상태"]) else str(row["회원상태"]),
                        "" if pd.isna(row["메모"]) else str(row["메모"])
                    ))

                    save_count += 1

                conn.commit()
                st.success(f"엑셀 업로드 완료: 신규 {save_count}건 저장 / 중복 또는 오류 {skip_count}건 제외")
                st.rerun()

# ----------------------
# 회원 등록
# ----------------------
if st.session_state.show_member_form:
    st.subheader("회원 등록")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("회원명")
        gender = st.selectbox("성별", ["남", "여"])
        birth_date = st.date_input("생년월일")
        member_type = st.selectbox("회원구분", ["학생", "성인"])
        phone = st.text_input("회원 연락처")

    with col2:
        if member_type == "학생":
            parent_name = st.text_input("보호자명")
            parent_phone = st.text_input("보호자 연락처")
            school = st.text_input("학교")
            grade = calculate_grade(birth_date, member_type)
            st.info(f"자동 계산 학년: {grade}")
        else:
            parent_name = ""
            parent_phone = ""
            school = ""
            grade = "성인"

        join_date = st.date_input("가입일", value=date.today())
        status = st.selectbox("회원상태", ["재원", "휴원", "퇴원"])

    memo = st.text_area("메모")

    if st.button("회원 저장", use_container_width=True):
        if name.strip() == "":
            st.warning("회원명을 입력하세요.")
        else:
            cursor.execute("""
            INSERT INTO members
            (
                name, gender, birth_date, member_type, phone,
                parent_name, parent_phone, school, grade,
                dance_class, join_date, status, memo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, gender, str(birth_date), member_type, phone,
                parent_name, parent_phone, school, grade,
                "", str(join_date), status, memo
            ))

            conn.commit()
            st.session_state.show_member_form = False
            st.success("회원 등록 완료")
            st.rerun()

# ----------------------
# 회원 개별 수정 / 삭제
# ----------------------
if st.session_state.show_member_edit_form:
    st.subheader("회원 개별 수정 / 삭제")

    all_members = pd.read_sql_query("SELECT * FROM members ORDER BY id", conn)

    if all_members.empty:
        st.info("수정할 회원이 없습니다.")
    else:
        member_label = st.selectbox(
            "수정 또는 삭제할 회원 선택",
            all_members.apply(lambda x: f"{x['id']} - {x['name']} - {x['status']}", axis=1)
        )

        selected_id = int(member_label.split(" - ")[0])

        selected = pd.read_sql_query(
            "SELECT * FROM members WHERE id=?",
            conn,
            params=(selected_id,)
        ).iloc[0]

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("회원명", selected["name"] if pd.notna(selected["name"]) else "")

            gender_options = ["남", "여"]
            gender = st.selectbox(
                "성별",
                gender_options,
                index=gender_options.index(selected["gender"]) if selected["gender"] in gender_options else 0
            )

            birth_date = st.date_input(
                "생년월일",
                value=pd.to_datetime(selected["birth_date"]).date()
                if pd.notna(selected["birth_date"]) and selected["birth_date"] != ""
                else date.today()
            )

            member_type_options = ["학생", "성인"]
            member_type = st.selectbox(
                "회원구분",
                member_type_options,
                index=member_type_options.index(selected["member_type"])
                if selected["member_type"] in member_type_options else 0
            )

            phone = st.text_input(
                "회원 연락처",
                selected["phone"] if pd.notna(selected["phone"]) else ""
            )

        with col2:
            if member_type == "학생":
                parent_name = st.text_input(
                    "보호자명",
                    selected["parent_name"] if pd.notna(selected["parent_name"]) else ""
                )
                parent_phone = st.text_input(
                    "보호자 연락처",
                    selected["parent_phone"] if pd.notna(selected["parent_phone"]) else ""
                )
                school = st.text_input(
                    "학교",
                    selected["school"] if pd.notna(selected["school"]) else ""
                )

                grade = calculate_grade(birth_date, member_type)
                st.info(f"자동 계산 학년: {grade}")
            else:
                parent_name = ""
                parent_phone = ""
                school = ""
                grade = "성인"

            join_date = st.date_input(
                "가입일",
                value=pd.to_datetime(selected["join_date"]).date()
                if pd.notna(selected["join_date"]) and selected["join_date"] != ""
                else date.today()
            )

            status_options = ["재원", "휴원", "퇴원"]
            status = st.selectbox(
                "회원상태",
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
                if name.strip() == "":
                    st.warning("회원명을 입력하세요.")
                else:
                    cursor.execute("""
                    UPDATE members
                    SET
                        name=?,
                        gender=?,
                        birth_date=?,
                        member_type=?,
                        phone=?,
                        parent_name=?,
                        parent_phone=?,
                        school=?,
                        grade=?,
                        join_date=?,
                        status=?,
                        memo=?
                    WHERE id=?
                    """, (
                        name, gender, str(birth_date), member_type, phone,
                        parent_name, parent_phone, school, grade,
                        str(join_date), status, memo, selected_id
                    ))

                    conn.commit()
                    st.success("회원 정보 수정 완료")
                    st.rerun()

        with col_delete:
            if st.button("🗑 삭제", use_container_width=True):
                cursor.execute("DELETE FROM members WHERE id=?", (selected_id,))
                conn.commit()
                st.success("회원 삭제 완료")
                st.rerun()