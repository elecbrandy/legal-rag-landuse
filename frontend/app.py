import streamlit as st
import requests
import os

# 환경 변수에서 백엔드 URL 가져오기 (기본값 설정)
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="부동산공법 RAG 테스트", layout="wide")

st.title("🏠 부동산공법 RAG 시스템 테스트")
st.info("현재 백엔드 연결 상태를 확인하고 데이터를 검색합니다.")

# 1. 백엔드 상태 체크
try:
    response = requests.get(f"{BACKEND_URL}/")
    if response.status_code == 200:
        st.success(f"✅ 백엔드 연결 성공: {response.json().get('status')}")
except Exception as e:
    st.error(f"❌ 백엔드 연결 실패: {e}")

# 2. 질문 입력창
query = st.text_input("부동산공법 관련 질문을 입력하세요 (예: 건폐율이 뭐야?)")

if st.button("질문하기"):
    if query:
        with st.spinner("ChromaDB에서 찾는 중..."):
            try:
                # 백엔드의 /query 엔드포인트 호출
                res = requests.get(f"{BACKEND_URL}/query", params={"text": query})
                if res.status_code == 200:
                    results = res.json().get("results")
                    st.write("### 🔍 검색 결과")
                    st.json(results)
                else:
                    st.error("백엔드에서 결과를 가져오지 못했습니다.")
            except Exception as e:
                st.error(f"오류 발생: {e}")
    else:
        st.warning("질문을 입력해주세요.")