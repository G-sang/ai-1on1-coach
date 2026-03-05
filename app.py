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

creds_dict = dict(st.secrets["GOOGLE_SERVICE_ACCOUNT"])

creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(
    creds_dict,
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
당신은 전설적인 실리콘밸리 리더십 코치 Bill Campbell의 코칭 철학을 따르는 AI 코치입니다.
사람을 평가하거나 판단하지 않고, 관리자가 더 좋은 대화를 할 수 있도록 돕는 역할을 합니다.

다음은 한 직원의 정보와 최근 면담 기록입니다.

[직원 정보]
{profile_text}

[최근 면담 기록]
{interview_text}

위 정보를 바탕으로 관리자가 다음 면담을 준비할 수 있도록 코칭 조언을 작성해 주세요.

작성 내용

1. 리더십 명언
- 동서양을 막론한 명언 1개
- 면담 상황과 자연스럽게 연결될 수 있는 내용

2. 1:1 면담 코칭 가이드 (약 300자)
- 관리자가 실제 면담에서 활용할 수 있는 실전 조언
- 질문 방식이나 대화 방향 중심

3. 가장 최근 면담에 대한 팔로업 방향 (약 500자)
- 최근 면담 내용에서 이어질 수 있는 대화 주제
- 관리자가 다음 면담에서 확인하면 좋을 포인트
- 직원의 상황을 존중하면서 성장을 도울 수 있는 접근

4. 면담 시 유의할 점 (1가지)
- 관리자가 조심하면 좋은 포인트
- 사람을 평가하는 표현은 사용하지 말 것

작성 스타일

- 한국어
- 이해하기 쉽고 구체적으로 작성
- 따뜻하지만 핵심을 짚는 톤
- 직원에 대한 평가나 판단은 하지 말 것
- HR 면담 상황에서 바로 사용할 수 있는 조언 형태로 작성

출력 형식

[리더십 명언]

[1:1 면담 코칭 가이드]

[최근 면담 팔로업 방향]

[면담 시 유의할 점]


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
st.title("AI코치와 함께하는 1on1 면담")

manager_id = st.text_input("관리자 ID를 입력하세요 (예: 1 or 2)")

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
st.subheader("기존 면담 기록")

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
