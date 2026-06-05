import streamlit as st
import os

USERS = {
    "admin": "1234",
    "grow": "grow1234"
}

LOGO_PATH = "assets/grow_logo.png"

def login_check():
    if "login_success" not in st.session_state:
        st.session_state.login_success = False

    if not st.session_state.login_success:
        left, center, right = st.columns([2, 1.4, 2])

        with center:
            if os.path.exists(LOGO_PATH):
                st.image(LOGO_PATH, use_container_width=True)

            st.markdown(
                "<div style='text-align:center; color:#777; margin-bottom:25px;'>관리자 로그인</div>",
                unsafe_allow_html=True
            )

            user_id = st.text_input("아이디", placeholder="아이디 입력")
            password = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력")

            if st.button("로그인", use_container_width=True):
                if user_id in USERS and USERS[user_id] == password:
                    st.session_state.login_success = True
                    st.session_state.login_user = user_id
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

            st.markdown(
                "<div style='text-align:center; color:#999; margin-top:30px;'>© GROW DANCE STUDIO</div>",
                unsafe_allow_html=True
            )

        st.stop()

def logout_button():
    with st.sidebar:
        st.divider()
        st.write(f"👤 {st.session_state.get('login_user', '')}")

        if st.button("로그아웃", use_container_width=True):
            st.session_state.login_success = False
            st.session_state.login_user = ""
            st.rerun()