import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
from datetime import datetime

# =========================
# 1. Google Sheets 연결
# =========================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

creds = Credentials.from_service_account_info(
    st.secrets["GOOGLE_SERVICE_ACCOUNT"],
    scopes=SCOPES
)



client = gspread.authorize(creds)

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/19Qy8jp5wmRYH3KJpfslknXSfMlHYm4Wgf9YE4Va5cHM/edit"
spreadsheet = client.open_by_url(SPREADSHEET_URL)

# =========================
# 2. 시트 로드 (⚠️ 정확)
# =========================
profile_ws = spreadsheet.worksheet("면담 데이터")   # 직원 기본 정보
interview_ws = spreadsheet.worksheet("직원면담")   # 면담 이력

profile_df = pd.DataFrame(profile_ws.get_all_records())
interview_df = pd.DataFrame(interview_ws.get_all_records())

# =========================
# 3. 컬럼 정규화 (필수)
# =========================
profile_df.columns = profile_df.columns.str.strip().str.upper()
interview_df.columns = interview_df.columns.str.strip().str.upper()

# =========================
# 4. 타입 정리
# =========================
profile_df["EMPID"] = profile_df["EMPID"].astype(str)
profile_df["관리자"] = profile_df["관리자"].astype(str)

interview_df["EMPID"] = interview_df["EMPID"].astype(str)
interview_df["관리자"] = interview_df["관리자"].astype(str)

interview_df["INTERVIEWDATE"] = pd.to_datetime(
    interview_df["INTERVIEWDATE"],
    errors="coerce"
)

# =========================
# 5. OpenAI 설정
# =========================
ai_client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)

def generate_ai_coaching(emp_profile, recent_interviews):
    profile_text = "\n".join([
        f"{k}: {emp_profile[k]}"
        for k in emp_profile.index
        if k not in ["EMPID", "관리자"]
    ])

    interview_text = "\n".join([
        f"- ({row['INTERVIEWDATE'].date()} / {row['INTERVIEWTYPE']}) {row['SUMMARY_TEXT']}"
        for _, row in recent_interviews.head(3).iterrows()
    ])

    prompt = f"""
당신은 전설적인 실리콘밸리 리더십 코치 Bill Campbell 스타일의 AI 코치입니다.

[직원 정보]
{profile_text}

[최근 면담 기록]
{interview_text}

위 정보를 바탕으로,

1. 이 직원과 면담시 참고하면 좋을 리더십 명언 하나 (Bill Campbell 명언이 아닌 동서양을 막론한 명언으로 부탁해) 와

2. 관리자가 1:1 면담에서 도움이 될 실전 코칭가이드를 300 글자 내외로 조언해 주세요

3. 가장 최근면담 팔로업 방향성

4. 마지막으로 이 직원과 면담시 주의해야 할점 1가지도 알려주세요

조건:
- 이해가 잘 되도록 조언해 줄 것
- 평가하지 말 것
- 따뜻하지만 핵심을 찌를 것
- 한국어


"""

    response = ai_client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a leadership coach."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content

# =========================
# 6. Streamlit UI
# =========================
st.set_page_config(page_title="AI 면담 코치", layout="wide")
st.title("🧭 AI 기반 관리자 1:1 면담 코치")

manager_id = st.text_input("관리자 ID를 입력하세요 (예: 1)")

if not manager_id:
    st.stop()

# =========================
# 7. 직원 목록
# =========================
team_df = profile_df[profile_df["관리자"] == manager_id]

if team_df.empty:
    st.warning("해당 관리자에게 소속된 직원이 없습니다.")
    st.stop()

st.subheader("👥 담당 직원")
selected_emp = st.selectbox("직원 선택", team_df["EMPID"].tolist())

emp_profile = team_df[team_df["EMPID"] == selected_emp].iloc[0]

# =========================
# 8. 직원 정보
# =========================
st.subheader("📌 직원 기본 정보")
st.table(emp_profile)

# =========================
# 9. 면담 기록
# =========================
st.subheader("🗂 기존 면담 기록")

emp_interviews = (
    interview_df[
        (interview_df["EMPID"] == selected_emp)
        & (interview_df["관리자"] == manager_id)
    ]
    .sort_values("INTERVIEWDATE", ascending=False)
)

if emp_interviews.empty:
    st.info("면담 기록이 없습니다.")
else:
    for _, row in emp_interviews.iterrows():
        with st.expander(f"{row['INTERVIEWDATE'].date()} · {row['INTERVIEWTYPE']}"):
            st.write(row["SUMMARY_TEXT"])

# =========================
# 10. AI 코칭 멘트
# =========================
st.subheader("🤖 AI 코치의 면담 멘트")

if st.button("AI 면담 멘트 생성"):
    with st.spinner("AI가 직원 정보를 분석 중입니다..."):
        ai_text = generate_ai_coaching(emp_profile, emp_interviews)
    st.markdown(ai_text)

# =========================
# 11. 면담 결과 입력 & 저장
# =========================
st.subheader("✍️ 면담 결과 입력")

interview_type = st.selectbox(
    "면담 유형",
    ["수시면담", "고과면담", "복귀면담"]
)

interview_summary = st.text_area(
    "면담 결과 요약",
    height=200,
    placeholder="면담에서 논의된 핵심 내용, 합의 사항, 다음 액션 등을 입력하세요."
)

if st.button("📌 면담 결과 저장"):
    if interview_summary.strip() == "":
        st.warning("면담 결과를 입력하세요.")
    else:
        interview_ws.append_row([
            selected_emp,
            datetime.now().strftime("%Y-%m-%d"),
            interview_type,
            manager_id,
            interview_summary
        ])
        st.success("면담 결과가 직원면담 시트에 저장되었습니다.")
