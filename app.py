import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
from datetime import datetime
 
# ─────────────────────────────────────────
#  커스텀 CSS — 다크 모드 세련된 UI
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=DM+Mono:wght@400;500&display=swap');
 
/* 전체 배경 */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #080c14 !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}
 
[data-testid="stHeader"] {
    background-color: #080c14 !important;
}
 
/* 사이드바 */
[data-testid="stSidebar"] {
    background-color: #0d1117 !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
 
/* 메인 컨테이너 여백 */
.block-container {
    padding: 2rem 2.5rem !important;
    max-width: 1100px !important;
}
 
/* 모든 텍스트 기본색 */
* { color: #dde2f0; }
 
/* ── 헤더 ── */
.app-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 2rem;
    padding: 1rem 0 1.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    flex-wrap: wrap;
}
.app-logo {
    width: 40px; height: 40px;
    background: linear-gradient(135deg, #3d7fff, #00c8e0);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    flex-shrink: 0;
}
.app-title-block {}
.app-title {
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #fff;
    margin: 0;
    white-space: nowrap;
}
.app-subtitle {
    font-size: 10px;
    color: #5a6480;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin: 2px 0 0;
    white-space: nowrap;
}
 
/* ── 섹션 레이블 ── */
.section-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #3d7fff;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-label::before {
    content: '';
    display: inline-block;
    width: 16px; height: 1px;
    background: #3d7fff;
}
 
/* ── 카드 ── */
.info-card {
    background: #0d1117;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 20px 22px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
}
.info-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #3d7fff, #00c8e0, transparent);
}
 
/* ── 직원 프로필 그리드 ── */
.profile-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-top: 4px;
}
.profile-item {
    background: #131920;
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 8px;
    padding: 12px 14px;
}
.profile-key {
    font-size: 10px;
    color: #4a5570;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.profile-val {
    font-size: 15px;
    font-weight: 500;
    color: #dde2f0;
    font-family: 'DM Mono', monospace;
}
 
/* ── 면담 기록 아이템 ── */
.interview-item {
    background: #0d1117;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 8px;
    transition: border-color 0.2s;
}
.interview-item:hover {
    border-color: rgba(61,127,255,0.3);
}
.interview-date {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: #3d7fff;
    margin-bottom: 4px;
}
.interview-type-badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    margin-left: 8px;
    vertical-align: middle;
}
.badge-고과 { background: rgba(240,165,0,0.15); color: #f0a500; }
.badge-수시 { background: rgba(61,127,255,0.15); color: #3d7fff; }
.badge-복귀 { background: rgba(0,212,138,0.15); color: #00d48a; }
 
/* ── AI 코칭 결과 ── */
.coaching-result {
    background: linear-gradient(135deg, #0d1117, #111a2e);
    border: 1px solid rgba(61,127,255,0.2);
    border-radius: 12px;
    padding: 24px 26px;
    margin-top: 12px;
    box-shadow: 0 0 40px rgba(61,127,255,0.05);
}
.coaching-section {
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.coaching-section:last-child {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
}
.coaching-section-title {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #00c8e0;
    margin-bottom: 10px;
}
.coaching-section-body {
    font-size: 14px;
    line-height: 1.8;
    color: #b0bcd4;
}
 
/* ── 입력 필드 커스텀 ── */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] select,
[data-testid="stTextArea"] textarea {
    background: #0d1117 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #dde2f0 !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: rgba(61,127,255,0.5) !important;
    box-shadow: 0 0 0 2px rgba(61,127,255,0.1) !important;
}
 
/* ── 버튼 ── */
[data-testid="stButton"] button {
    background: linear-gradient(135deg, #3d7fff, #2563eb) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    padding: 0.5rem 1.5rem !important;
    transition: all 0.2s !important;
}
[data-testid="stButton"] button:hover {
    opacity: 0.85 !important;
    transform: translateY(-1px) !important;
}
 
/* ── 구분선 ── */
hr { border-color: rgba(255,255,255,0.06) !important; }
 
/* ── 성공/경고 메시지 ── */
[data-testid="stSuccess"] {
    background: rgba(0,212,138,0.08) !important;
    border: 1px solid rgba(0,212,138,0.2) !important;
    border-radius: 8px !important;
}
[data-testid="stWarning"] {
    background: rgba(240,165,0,0.08) !important;
    border: 1px solid rgba(240,165,0,0.2) !important;
    border-radius: 8px !important;
}
 
/* selectbox 드롭다운 — 선택 박스 */
[data-testid="stSelectbox"] > div > div {
    background: #0d1117 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #dde2f0 !important;
}
 
/* selectbox 팝업 리스트 전체 */
[data-baseweb="popover"],
[data-baseweb="menu"],
ul[data-baseweb="menu"],
[data-baseweb="select"] ul {
    background: #0d1117 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important;
}
 
/* 팝업 각 항목 */
[data-baseweb="menu"] li,
[role="option"] {
    background: #0d1117 !important;
    color: #dde2f0 !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 13px !important;
}
 
/* 호버 */
[data-baseweb="menu"] li:hover,
[role="option"]:hover {
    background: rgba(61,127,255,0.12) !important;
    color: #fff !important;
}
 
/* 선택된 항목 */
[aria-selected="true"] {
    background: rgba(61,127,255,0.2) !important;
    color: #3d7fff !important;
}
 
/* spinner */
[data-testid="stSpinner"] { color: #3d7fff !important; }
 
/* 라벨 */
[data-testid="stWidgetLabel"] p {
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    color: #4a5570 !important;
}
 
/* expander */
[data-testid="stExpander"] {
    background: #0d1117 !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)
 
 
# ─────────────────────────────────────────
#  Google Sheets 연결
# ─────────────────────────────────────────
@st.cache_resource
def get_spreadsheet():
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds_dict = dict(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/19Qy8jp5wmRYH3KJpfslknXSfMlHYm4Wgf9YE4Va5cHM/edit"
    return client.open_by_url(SPREADSHEET_URL)
 
@st.cache_data(ttl=60)
def load_data():
    spreadsheet = get_spreadsheet()
    profile_ws   = spreadsheet.worksheet("면담 데이터")
    interview_ws = spreadsheet.worksheet("직원면담")
 
    profile_df   = pd.DataFrame(profile_ws.get_all_records())
    interview_df = pd.DataFrame(interview_ws.get_all_records())
 
    profile_df.columns   = profile_df.columns.str.strip().str.upper()
    interview_df.columns = interview_df.columns.str.strip().str.upper()
 
    profile_df["EMPID"]   = profile_df["EMPID"].astype(str)
    profile_df["관리자"]  = profile_df["관리자"].astype(str)
    interview_df["EMPID"] = interview_df["EMPID"].astype(str)
    interview_df["관리자"]= interview_df["관리자"].astype(str)
    interview_df["INTERVIEWDATE"] = pd.to_datetime(
        interview_df["INTERVIEWDATE"], errors="coerce"
    )
    return profile_df, interview_df
 
# ─────────────────────────────────────────
#  AI 코칭 생성
# ─────────────────────────────────────────
def generate_ai_coaching(emp_profile, recent_interviews):
    ai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
 
    profile_text = "\n".join([
        f"{k}: {emp_profile[k]}"
        for k in emp_profile.index
        if k not in ["EMPID", "관리자"]
    ])
 
    interview_text = "\n".join([
        f"- ({row['INTERVIEWDATE'].date()} / {row['INTERVIEWTYPE']}) {row['SUMMARY_TEXT']}"
        for _, row in recent_interviews.head(3).iterrows()
    ]) if not recent_interviews.empty else "면담 기록 없음"
 
    prompt = f"""
당신은 전설적인 실리콘밸리 리더십 코치 Bill Campbell의 코칭 철학을 따르는 AI 코치입니다.
사람을 평가하거나 판단하지 않고, 관리자가 더 좋은 대화를 할 수 있도록 돕는 역할을 합니다.
 
[직원 정보]
{profile_text}
 
[최근 면담 기록]
{interview_text}
 
아래 형식으로 정확하게 출력하세요. 각 섹션 제목은 그대로 유지하세요.
 
[리더십 명언]
동서양 명언 1개 + 면담 상황과 연결되는 한 문장
 
[1:1 면담 코칭 가이드]
관리자가 실제 면담에서 활용할 수 있는 실전 조언 (약 200자)
 
[최근 면담 팔로업 방향]
최근 면담에서 이어질 대화 주제와 확인 포인트 (약 300자)
 
[면담 시 유의할 점]
관리자가 조심해야 할 포인트 1가지
"""
 
    response = ai_client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a leadership coach. Respond in Korean only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content
 
 
def parse_coaching(text):
    """AI 결과를 섹션별로 파싱"""
    sections = {}
    keys = ["리더십 명언", "1:1 면담 코칭 가이드", "최근 면담 팔로업 방향", "면담 시 유의할 점"]
    for i, key in enumerate(keys):
        start_marker = f"[{key}]"
        end_marker   = f"[{keys[i+1]}]" if i+1 < len(keys) else None
        start = text.find(start_marker)
        if start == -1:
            sections[key] = ""
            continue
        start += len(start_marker)
        end = text.find(end_marker) if end_marker else len(text)
        sections[key] = text[start:end].strip()
    return sections
 
 
# ─────────────────────────────────────────
#  UI 시작
# ─────────────────────────────────────────
st.set_page_config(page_title="1on1 면담 코치", layout="wide", page_icon="🤝")
 
# 헤더
st.markdown("""
<div class="app-header">
    <div class="app-logo">🤝</div>
    <div class="app-title-block">
        <p class="app-title">AI 1on1 면담 코치</p>
        <p class="app-subtitle">Powered by Bill Campbell's Coaching Philosophy</p>
    </div>
</div>
""", unsafe_allow_html=True)
 
# 데이터 로드
try:
    profile_df, interview_df = load_data()
    spreadsheet = get_spreadsheet()
    interview_ws = spreadsheet.worksheet("직원면담")
except Exception as e:
    st.error(f"데이터 연결 실패: {e}")
    st.stop()
 
# ─────────────────────────────────────────
#  사이드바 — 관리자 로그인 + 직원 선택
# ─────────────────────────────────────────
with st.sidebar:
    # 모바일 안내 배너
    st.markdown("""
    <div style="margin-bottom:20px;padding:10px 12px;
                background:rgba(0,200,224,0.07);
                border:1px solid rgba(0,200,224,0.15);
                border-radius:8px;font-size:11px;
                color:#5a8090;line-height:1.6;">
        📱 모바일이라면 화면 왼쪽 상단<br>
        <b style="color:#00c8e0;">＞</b> 버튼을 눌러 메뉴를 여세요
    </div>
    """, unsafe_allow_html=True)
 
    st.markdown("""
    <div style="margin-bottom:16px;">
        <div style="font-size:10px;font-weight:700;letter-spacing:0.12em;
                    text-transform:uppercase;color:#3d7fff;margin-bottom:12px;">
            관리자 접속
        </div>
    </div>
    """, unsafe_allow_html=True)
 
    manager_id = st.text_input(
        "관리자 ID",
        placeholder="예: 1",
        label_visibility="visible"
    )
 
    if not manager_id:
        st.markdown("""
        <div style="margin-top:12px;padding:14px;background:rgba(61,127,255,0.06);
                    border:1px solid rgba(61,127,255,0.15);border-radius:8px;
                    font-size:12px;color:#5a6480;line-height:1.7;">
            위 칸에 <b style="color:#3d7fff;">관리자 사번</b>을 입력하면<br>
            담당 직원 목록이 나타납니다.<br><br>
            <span style="color:#3a4560;font-size:11px;">예) 1, 2, 3 ...</span>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
 
    team_df = profile_df[profile_df["관리자"] == manager_id]
 
    if team_df.empty:
        st.warning("소속 직원이 없습니다.")
        st.stop()
 
    st.markdown(f"""
    <div style="margin:16px 0 8px;font-size:10px;font-weight:700;
                letter-spacing:0.1em;text-transform:uppercase;color:#4a5570;">
        담당 직원 ({len(team_df)}명)
    </div>
    """, unsafe_allow_html=True)
 
    selected_emp = st.selectbox(
        "직원 선택",
        team_df["EMPID"].tolist(),
        label_visibility="collapsed"
    )
 
    # 직원 퀵 스탯
    emp_interviews_all = interview_df[
        (interview_df["EMPID"] == selected_emp) &
        (interview_df["관리자"] == manager_id)
    ]
    last_date = emp_interviews_all["INTERVIEWDATE"].max()
    last_date_str = last_date.strftime("%Y.%m.%d") if pd.notna(last_date) else "기록 없음"
 
    st.markdown(f"""
    <div style="margin-top:16px;padding:14px;background:rgba(0,200,224,0.05);
                border:1px solid rgba(0,200,224,0.12);border-radius:8px;">
        <div style="font-size:10px;color:#4a5570;margin-bottom:6px;
                    font-weight:600;letter-spacing:0.06em;text-transform:uppercase;">
            최근 면담
        </div>
        <div style="font-family:'DM Mono',monospace;font-size:13px;color:#00c8e0;">
            {last_date_str}
        </div>
        <div style="font-size:11px;color:#4a5570;margin-top:4px;">
            총 {len(emp_interviews_all)}회 면담 기록
        </div>
    </div>
    """, unsafe_allow_html=True)
 
 
# ─────────────────────────────────────────
#  메인 영역
# ─────────────────────────────────────────
emp_profile  = team_df[team_df["EMPID"] == selected_emp].iloc[0]
emp_interviews = (
    interview_df[
        (interview_df["EMPID"] == selected_emp) &
        (interview_df["관리자"] == manager_id)
    ].sort_values("INTERVIEWDATE", ascending=False)
)
 
col_left, col_right = st.columns([1, 1], gap="large")
 
# ── 왼쪽: 직원 정보 + 면담 기록 ──
with col_left:
 
    # 직원 기본 정보
    st.markdown('<div class="section-label">직원 기본 정보</div>', unsafe_allow_html=True)
 
    skip_keys = ["EMPID", "관리자"]
    items = [(k, str(v)) for k, v in emp_profile.items() if k not in skip_keys]
 
    grid_html = '<div class="profile-grid">'
    for k, v in items:
        grid_html += f"""
        <div class="profile-item">
            <div class="profile-key">{k}</div>
            <div class="profile-val">{v if v else "—"}</div>
        </div>"""
    grid_html += '</div>'
    st.markdown(f'<div class="info-card">{grid_html}</div>', unsafe_allow_html=True)
 
    # 면담 기록
    st.markdown('<div class="section-label" style="margin-top:24px;">면담 기록</div>', unsafe_allow_html=True)
 
    if emp_interviews.empty:
        st.markdown("""
        <div style="padding:20px;text-align:center;color:#4a5570;
                    border:1px dashed rgba(255,255,255,0.06);border-radius:10px;
                    font-size:13px;">
            아직 면담 기록이 없습니다
        </div>
        """, unsafe_allow_html=True)
    else:
        for _, row in emp_interviews.iterrows():
            itype = row['INTERVIEWTYPE']
            badge_class = f"badge-{itype[:2]}" if itype else "badge-수시"
            date_str = row['INTERVIEWDATE'].strftime("%Y.%m.%d") if pd.notna(row['INTERVIEWDATE']) else "—"
            summary  = row.get('SUMMARY_TEXT', '')
 
            with st.expander(f"{date_str}  ·  {itype}"):
                st.markdown(f"""
                <div style="font-size:13px;line-height:1.7;color:#9aa3bc;padding:4px 0;">
                    {summary if summary else '<span style="color:#4a5570;">내용 없음</span>'}
                </div>
                """, unsafe_allow_html=True)
 
 
# ── 오른쪽: AI 코칭 + 면담 입력 ──
with col_right:
 
    # AI 코칭
    st.markdown('<div class="section-label">AI 코칭</div>', unsafe_allow_html=True)
 
    if st.button("✦  AI 면담 코칭 생성", use_container_width=True):
        with st.spinner("Bill Campbell의 코칭 철학으로 분석 중..."):
            raw = generate_ai_coaching(emp_profile, emp_interviews)
            sections = parse_coaching(raw)
            st.session_state["coaching_result"] = sections
 
    if "coaching_result" in st.session_state:
        s = st.session_state["coaching_result"]
 
        icon_map = {
            "리더십 명언":         ("💬", "#f0a500"),
            "1:1 면담 코칭 가이드": ("🎯", "#3d7fff"),
            "최근 면담 팔로업 방향": ("🔁", "#00d48a"),
            "면담 시 유의할 점":    ("⚠️", "#ff4d6d"),
        }
 
        html = '<div class="coaching-result">'
        for title, (icon, color) in icon_map.items():
            content = s.get(title, "")
            if content:
                html += f"""
                <div class="coaching-section">
                    <div class="coaching-section-title" style="color:{color};">
                        {icon} &nbsp;{title}
                    </div>
                    <div class="coaching-section-body">{content}</div>
                </div>"""
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
 
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
 
    # 면담 결과 입력
    st.markdown('<div class="section-label">면담 결과 입력</div>', unsafe_allow_html=True)
 
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
 
    interview_type = st.selectbox(
        "면담 유형",
        ["수시면담", "고과면담", "복귀면담"]
    )
 
    interview_summary = st.text_area(
        "면담 결과 요약",
        height=160,
        placeholder="면담에서 논의된 핵심 내용, 합의 사항, 다음 액션 등을 입력하세요."
    )
 
    st.markdown('</div>', unsafe_allow_html=True)
 
    if st.button("저장", use_container_width=True):
        if not interview_summary.strip():
            st.warning("면담 결과를 입력해 주세요.")
        else:
            interview_ws.append_row([
                selected_emp,
                datetime.now().strftime("%Y-%m-%d"),
                interview_type,
                manager_id,
                interview_summary
            ])
            st.cache_data.clear()
            st.success("✓  면담 결과가 저장되었습니다.")
 
