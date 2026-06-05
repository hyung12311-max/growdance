import streamlit as st

st.set_page_config(
    page_title="GROW DANCE",
    page_icon="💃",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #F7F7F7;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

h1 {
    color: #FF7A00;
    font-weight: 900;
}

h2, h3 {
    color: #1F2937;
}

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

st.title("💃 GROW DANCE")

st.markdown("""
## Grow Dance 통합 관리 시스템

왼쪽 메뉴를 선택하세요.

### 제공 기능

- 🏠 대시보드
- 👥 회원관리
- 👨‍🏫 강사관리
- 📚 수업마스터
- 🏫 Class관리
- ✅ 출석관리
""")