import streamlit as st

st.set_page_config(
    page_title="GROW DANCE",
    page_icon="💃",
    layout="wide"
)

st.markdown("""
<style>
.stApp { background-color: #F7F7F7; }

section[data-testid="stSidebar"] { background-color: #111827; }

section[data-testid="stSidebar"] * { color: white !important; }

h1 {
    color: #FF7A00;
    font-weight: 900;
}

h2, h3 { color: #1F2937; }

.stButton > button {
    border-radius: 12px;
    border: 1px solid #FF7A00;
    background-color: #FF7A00;
    color: white;
    font-weight: 700;
}

.stButton > button:hover {
    background-color: #E86D00;
    color: white;
    border: 1px solid #E86D00;
}

div[data-testid="stMetric"] {
    background-color: white;
    padding: 20px;
    border-radius: 18px;
    border-left: 8px solid #FF7A00;
    box-shadow: 0px 4px 14px rgba(0,0,0,0.08);
}
</style>
""", unsafe_allow_html=True)

# 로그인 상태 저장
if "login" not in st.session_state:
    st.session_state.login = False

ADMIN_ID = "admin"
ADMIN_PW = "1234"

# 로그인 화면
if not st.session_state.login:
    st.title("💃 GROW DANCE")
    st.subheader("관리자 로그인")

    user_id = st.text_input("아이디")
    user_pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if user_id == ADMIN_ID and user_pw == ADMIN_PW:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    st.info("테스트 계정: admin / 1234")

# 로그인 후 화면
else:
    st.sidebar.title("💃 GROW DANCE")

    menu = st.sidebar.radio(
        "메뉴 선택",
        [
            "🏠 대시보드",
            "👥 회원관리",
            "👨‍🏫 강사관리",
            "📚 수업마스터",
            "🏫 클래스관리",
            "✅ 출석관리",
            "🚪 로그아웃"
        ]
    )

    if menu == "🚪 로그아웃":
        st.session_state.login = False
        st.rerun()

    if menu == "🏠 대시보드":
        st.title("🏠 대시보드")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("전체 회원", "0명")
        col2.metric("수강 중 회원", "0명")
        col3.metric("등록 강사", "0명")
        col4.metric("오늘 출석", "0명")

        st.markdown("### Grow Dance 통합 관리 시스템")
        st.write("회원, 강사, 수업, 클래스, 출석 정보를 관리하는 화면입니다.")

    elif menu == "👥 회원관리":
        st.title("👥 회원관리")

        with st.form("member_form"):
            name = st.text_input("회원명")
            phone = st.text_input("연락처")
            member_type = st.selectbox("회원구분", ["유아", "학생", "성인", "기타"])
            school = st.text_input("학교명")
            parent_phone = st.text_input("보호자 연락처")
            memo = st.text_area("메모")

            submitted = st.form_submit_button("회원 등록")

            if submitted:
                st.success(f"{name} 회원이 등록되었습니다.")

    elif menu == "👨‍🏫 강사관리":
        st.title("👨‍🏫 강사관리")

        with st.form("teacher_form"):
            teacher_name = st.text_input("강사명")
            genre = st.text_input("담당 장르")
            phone = st.text_input("연락처")
            memo = st.text_area("메모")

            submitted = st.form_submit_button("강사 등록")

            if submitted:
                st.success(f"{teacher_name} 강사가 등록되었습니다.")

    elif menu == "📚 수업마스터":
        st.title("📚 수업마스터")

        with st.form("lesson_form"):
            lesson_name = st.text_input("수업명")
            genre = st.selectbox(
                "장르",
                ["K-POP", "힙합", "하우스댄스", "셔플댄스", "키즈댄스", "입시반", "퍼포먼스반"]
            )
            level = st.selectbox("레벨", ["입문", "초급", "중급", "고급"])
            memo = st.text_area("수업 설명")

            submitted = st.form_submit_button("수업 등록")

            if submitted:
                st.success(f"{lesson_name} 수업이 등록되었습니다.")

    elif menu == "🏫 클래스관리":
        st.title("🏫 클래스관리")

        with st.form("class_form"):
            class_name = st.text_input("클래스명")
            lesson = st.text_input("수업명")
            teacher = st.text_input("담당 강사")
            day = st.selectbox("요일", ["월", "화", "수", "목", "금", "토", "일"])
            time = st.text_input("수업 시간 예: 18:00~19:00")
            capacity = st.number_input("정원", min_value=1, step=1)

            submitted = st.form_submit_button("클래스 등록")

            if submitted:
                st.success(f"{class_name} 클래스가 등록되었습니다.")

    elif menu == "✅ 출석관리":
        st.title("✅ 출석관리")

        attendance_date = st.date_input("출석일")
        class_name = st.text_input("클래스명")
        member_name = st.text_input("회원명")
        status = st.selectbox("출석 상태", ["출석", "결석", "지각", "보강"])

        if st.button("출석 등록"):
            st.success(f"{member_name} 회원의 출석 정보가 등록되었습니다.")