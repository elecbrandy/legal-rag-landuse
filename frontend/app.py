import streamlit as st
import requests
import os
from uuid import uuid4

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(
    page_title="부동산공법 AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 화이트톤 & Pretendard 폰트가 적용된 CSS 스타일
st.markdown("""
<style>
/* Pretendard 웹폰트 및 JetBrains Mono 로드 */
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

/* 전체 기본 폰트 적용 (일부 모노스페이스 제외) */
html, body, [class*="css"]  {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

/* 메인 배경 & 텍스트 색상 */
.stApp { background-color: #f8f9fa; color: #1f2937; }
[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e5e7eb; }

/* 헤더 및 타이틀 */
.main-header {
    font-size: 1.6rem; font-weight: 700;
    color: #111827; letter-spacing: -0.02em;
    padding: 0.5rem 0 1.5rem 0; border-bottom: 1px solid #e5e7eb; margin-bottom: 1.5rem;
}
.section-title {
    font-size: 0.85rem; font-weight: 700;
    color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.75rem;
}

/* 채팅 말풍선 (User & AI) */
.chat-user {
    background: #ffffff; border: 1px solid #e5e7eb;
    border-radius: 12px 12px 4px 12px; padding: 0.85rem 1.1rem;
    margin: 0.5rem 0 0.5rem 3rem; 
    font-size: 0.95rem; color: #374151; line-height: 1.6;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.chat-ai {
    background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #3b82f6;
    border-radius: 4px 12px 12px 12px; padding: 0.85rem 1.1rem;
    margin: 0.5rem 3rem 0.5rem 0;
    font-size: 0.95rem; color: #1f2937; line-height: 1.7;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}

/* 역할 라벨 및 뱃지 (JetBrains Mono 적용) */
.role-label { font-family: 'JetBrains Mono', monospace !important; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 0.3rem; }
.role-user  { color: #64748b; text-align: right; margin-right: 3rem; }
.role-ai    { color: #3b82f6; margin-left: 0.5rem; }

.model-badge {
    display: inline-block; background: #eff6ff; border: 1px solid #bfdbfe;
    color: #2563eb; padding: 2px 8px; border-radius: 99px;
    font-family: 'JetBrains Mono', monospace !important; font-size: 0.7rem; font-weight: 500;
}
.badge-ok  { background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; padding: 2px 8px; border-radius: 99px; font-size: 0.72rem; font-family: 'JetBrains Mono', monospace !important; font-weight: 600; }
.badge-err { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; padding: 2px 8px; border-radius: 99px; font-size: 0.72rem; font-family: 'JetBrains Mono', monospace !important; font-weight: 600; }

/* 출처(근거 조문) 카드 */
.source-card {
    background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px;
    padding: 0.75rem 1rem; margin-top: 0.5rem;
    font-size: 0.85rem; color: #4b5563; line-height: 1.5;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.source-law   { color: #1d4ed8; font-weight: 600; }
.source-score { font-family: 'JetBrains Mono', monospace !important; color: #059669; float: right; font-weight: 500; background: #ecfdf5; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem;}

/* 사이드바 법령 카드 */
.law-card {
    background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px;
    padding: 0.6rem 0.9rem; margin-bottom: 0.4rem;
}
.law-name  { font-size: 0.85rem; color: #111827; font-weight: 600; margin-bottom: 0.2rem; }
.law-count { font-family: 'JetBrains Mono', monospace !important; font-size: 0.75rem; color: #6b7280; }

hr { border-color: #e5e7eb; margin: 1.2rem 0; }

/* 입력창 및 버튼 (Streamlit 기본 위젯 스타일 덮어쓰기) */
.stButton > button {
    background: #ffffff; color: #374151; border: 1px solid #d1d5db;
    border-radius: 8px; font-weight: 600; transition: all 0.2s;
}
.stButton > button:hover { background: #f3f4f6; border-color: #9ca3af; color: #111827; }

.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #ffffff !important; border: 1px solid #d1d5db !important;
    color: #111827 !important; border-radius: 8px !important; 
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #3b82f6 !important; box-shadow: 0 0 0 1px #3b82f6 !important;
}
.stSelectbox > div > div {
    background: #ffffff !important; border: 1px solid #d1d5db !important; color: #111827 !important;
}
</style>
""", unsafe_allow_html=True)

# ── 세션 상태 초기화 ───────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_model" not in st.session_state:
    st.session_state.selected_model = None  # 백엔드 default 사용


# ── 유틸 ──────────────────────────────────────────────────────
def check_backend() -> bool:
    try:
        return requests.get(f"{BACKEND_URL}/", timeout=3).status_code == 200
    except Exception:
        return False

def fetch_models() -> dict:
    try:
        r = requests.get(f"{BACKEND_URL}/chat/models", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"models": {"gpt-4o": "openai:gpt-4o"}, "default": "openai:gpt-4o"}

def fetch_law_list() -> list[dict]:
    try:
        r = requests.get(f"{BACKEND_URL}/law/list", timeout=5)
        if r.status_code == 200:
            return r.json().get("laws", [])
    except Exception:
        pass
    return []

def do_ingest(law_ids: list[str]) -> dict | None:
    try:
        r = requests.post(f"{BACKEND_URL}/law/ingest", json={"law_ids": law_ids}, timeout=120)
        return r.json() if r.status_code == 200 else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}

def do_chat(session_id: str, message: str, model: str) -> dict | None:
    try:
        r = requests.post(
            f"{BACKEND_URL}/chat",
            params={"model": model},
            json={"session_id": session_id, "message": message},
            timeout=60,
        )
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def do_delete_law(law_id: str) -> bool:
    try:
        return requests.delete(f"{BACKEND_URL}/law/{law_id}", timeout=10).status_code == 200
    except Exception:
        return False


# ── 사이드바 ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="main-header">⚖️ 부동산공법 AI</div>', unsafe_allow_html=True)

    is_ok = check_backend()
    badge = '<span class="badge-ok">● ONLINE</span>' if is_ok else '<span class="badge-err">● OFFLINE</span>'
    st.markdown(f"**백엔드** {badge}", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── 모델 선택 ──────────────────────────────────────────────
    st.markdown('<div class="section-title">🤖 모델 선택</div>', unsafe_allow_html=True)

    model_info = fetch_models()
    model_labels = list(model_info["models"].keys())   # ["gpt-4o", "gpt-4o-mini", ...]
    model_values = list(model_info["models"].values())  # ["openai:gpt-4o", ...]

    default_value = model_info.get("default", model_values[0])
    default_idx = model_values.index(default_value) if default_value in model_values else 0

    selected_label = st.selectbox(
        "모델",
        options=model_labels,
        index=default_idx,
        label_visibility="collapsed",
    )
    selected_model = model_info["models"][selected_label]
    st.session_state.selected_model = selected_model

    st.markdown(
        f'<div style="margin-top:4px">'
        f'<span class="model-badge">{selected_model}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── 법령 인제스트 (ID 기반) ──────────────────────────────────
    st.markdown('<div class="section-title">📥 수동 법령 데이터 적재</div>', unsafe_allow_html=True)

    law_input = st.text_area(
        "법령 ID",
        placeholder="법령 ID를 한 줄에 하나씩 입력\n예)\n0000058811\n0000056524",
        height=110,
        label_visibility="collapsed",
    )

    col1, col2 = st.columns(2)
    with col1:
        ingest_btn = st.button("📥 ID로 적재", use_container_width=True)
    with col2:
        st.button("🔄 목록 갱신", use_container_width=True)

    if ingest_btn:
        ids = [x.strip() for x in law_input.strip().splitlines() if x.strip()]
        if not ids:
            st.warning("법령 ID를 입력해주세요.")
        else:
            with st.spinner(f"{len(ids)}개 법령 수집 중..."):
                result = do_ingest(ids)
            if result and "error" not in result:
                st.success(f"✅ {len(result['ingested_laws'])}개 법령 · {result['total_chunks']}개 청크")
                st.rerun()
            else:
                st.error(f"❌ {result.get('error', '알 수 없는 오류')}")
                
    st.markdown("<hr>", unsafe_allow_html=True)

    # ── [신규 추가] 필수 법령 일괄 적재 ────────────────────────────────────────
    st.markdown('<div class="section-title">📦 공인중개사 27종 일괄 적재</div>', unsafe_allow_html=True)
    
    if st.button("🚀 부동산공법 기본 법령 모두 수집", use_container_width=True):
        LAW_NAMES = [
            "공인중개사법", "공인중개사법 시행령", "공인중개사법 시행규칙",
            "부동산 거래신고 등에 관한 법률", "부동산 거래신고 등에 관한 법률 시행령", "부동산 거래신고 등에 관한 법률 시행규칙",
            "국토의 계획 및 이용에 관한 법률", "국토의 계획 및 이용에 관한 법률 시행령", "국토의 계획 및 이용에 관한 법률 시행규칙",
            "도시개발법", "도시개발법 시행령", "도시개발법 시행규칙",
            "도시 및 주거환경정비법", "도시 및 주거환경정비법 시행령", "도시 및 주거환경정비법 시행규칙",
            "건축법", "건축법 시행령", "건축법 시행규칙",
            "주택법", "주택법 시행령", "주택법 시행규칙",
            "농지법", "농지법 시행령", "농지법 시행규칙",
            "산지관리법", "산지관리법 시행령", "산지관리법 시행규칙",
        ]
        
        with st.spinner("27개 법령을 검색하고 임베딩하는 중입니다... (최대 5~10분 소요)"):
            try:
                # 600초(10분)로 넉넉한 타임아웃 부여
                r = requests.post(
                    f"{BACKEND_URL}/law/ingest/names", 
                    json={"law_names": LAW_NAMES}, 
                    timeout=600
                )
                if r.status_code == 200:
                    res_data = r.json()
                    st.success(f"✅ {len(res_data['ingested_laws'])}개 법령 · {res_data['total_chunks']}개 청크 적재 완료")
                    st.rerun()
                else:
                    st.error(f"❌ 오류: {r.text}")
            except Exception as e:
                st.error(f"❌ 요청 실패: {e}")

    # ── 저장된 법령 목록 ───────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">📚 저장된 법령</div>', unsafe_allow_html=True)

    laws = fetch_law_list()
    if not laws:
        st.caption("저장된 법령이 없습니다.")
    else:
        for law in laws:
            cols = st.columns([5, 1])
            with cols[0]:
                st.markdown(
                    f'<div class="law-card">'
                    f'<div class="law-name">{law["law_name"] or law["law_id"]}</div>'
                    f'<div class="law-count">{law["chunk_count"]} chunks</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with cols[1]:
                if st.button("🗑", key=f"del_{law['law_id']}", help="삭제"):
                    if do_delete_law(law["law_id"]):
                        st.rerun()

    # ── 세션 ───────────────────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">💬 세션 관리</div>', unsafe_allow_html=True)
    st.caption(f"`ID: {st.session_state.session_id[:8]}...`")
    if st.button("🆕 새 대화 시작", use_container_width=True):
        st.session_state.session_id = str(uuid4())
        st.session_state.messages = []
        st.rerun()


# ── 메인 채팅 영역 ─────────────────────────────────────────────
st.markdown('<div class="section-title" style="margin-top: 1rem;">💬 질문하기</div>', unsafe_allow_html=True)

chat_container = st.container()
with chat_container:
    if not st.session_state.messages:
        st.markdown(
            '<div style="text-align:center; color:#6b7280; padding: 4rem 0; '
            'font-weight: 500; font-size: 1rem;">'
            '좌측 메뉴에서 법령 데이터를 적재한 뒤 질문해보세요.<br><br>'
            '<span style="font-size:0.85rem; color:#9ca3af; background: #f3f4f6; padding: 4px 12px; border-radius: 99px;">'
            '💡 예: 건폐율이란 무엇인가요?</span>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="role-label role-user">YOU</div>'
                    f'<div class="chat-user">{msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                # 어떤 모델로 답했는지 표시
                model_tag = msg.get("model", "")
                model_html = f'<span class="model-badge" style="margin-left:8px">{model_tag}</span>' if model_tag else ""
                st.markdown(
                    f'<div class="role-label role-ai">⚖️ AI {model_html}</div>'
                    f'<div class="chat-ai">{msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
                sources = msg.get("sources", [])
                if sources:
                    with st.expander(f"📌 참조된 근거 조문 ({len(sources)}개)", expanded=False):
                        for src in sources:
                            st.markdown(
                                f'<div class="source-card">'
                                f'<span class="source-law">[{src["law_name"]} {src["article"]}]</span>'
                                f'<span class="source-score">{int(src["score"]*100)}% 일치</span><br>'
                                f'<div style="margin-top: 6px;">{src["content"]}</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

st.markdown("<hr>", unsafe_allow_html=True)

with st.form("chat_form", clear_on_submit=True):
    cols = st.columns([8, 1])
    with cols[0]:
        user_input = st.text_input(
            "질문",
            placeholder="부동산공법 관련 질문을 입력하세요...",
            label_visibility="collapsed",
        )
    with cols[1]:
        submitted = st.form_submit_button("전송", use_container_width=True)

if submitted and user_input.strip():
    if not is_ok:
        st.error("백엔드에 연결할 수 없습니다.")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        current_model = st.session_state.selected_model

        with st.spinner(f"[{selected_label}] 관련 법령을 분석 중입니다..."):
            resp = do_chat(st.session_state.session_id, user_input.strip(), current_model)

        if resp:
            st.session_state.messages.append({
                "role": "ai",
                "content": resp.get("answer", ""),
                "sources": resp.get("sources", []),
                "model": selected_label,
            })
        else:
            st.session_state.messages.append({
                "role": "ai",
                "content": "⚠️ 응답을 받지 못했습니다. 잠시 후 다시 시도해주세요.",
                "sources": [],
                "model": "",
            })
        st.rerun()