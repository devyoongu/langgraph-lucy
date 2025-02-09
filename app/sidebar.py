import streamlit as st
import requests
import os
from retriever import EMBEDDINGS_RECORD_FILE


def render_sidebar():
    """사이드바 렌더링 함수"""
    with st.sidebar:
        # 파일 업로드
        uploaded_file = st.file_uploader("문서 업로드", type=["pdf"])
        uploaded_dept_file = st.file_uploader("조직도 업로드", type=["pdf"])

        # 구분선 추가
        st.divider()
        
        # 임베딩된 파일 목록 표시
        st.write("### 📚 임베딩된 파일 목록")
        
        # 세션 상태에서 파일 목록 가져오기
        if "embedded_files" not in st.session_state:
            st.session_state.embedded_files = []
            
        if os.path.exists(EMBEDDINGS_RECORD_FILE):
            with open(EMBEDDINGS_RECORD_FILE, "r", encoding='utf-8') as f:
                st.session_state.embedded_files = [
                    line.strip() for line in f.readlines() if line.strip()
                ]
        
        # 파일 목록 표시
        if st.session_state.embedded_files:
            for file_path in st.session_state.embedded_files:
                file_name = os.path.basename(file_path)
                st.text(f"📄 {file_name}")
        else:
            st.info("아직 임베딩된 파일이 없습니다.")


        return uploaded_file, uploaded_dept_file
