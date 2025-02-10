import streamlit as st
import requests
import os
from retriever import EMBEDDINGS_RECORD_FILE
from langchain_teddynote.graphs import visualize_graph
from langgraph.graph import StateGraph


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

        # 구분선 추가
        st.divider()
        
        # 그래프 시각화 버튼
        if st.button("🔍 그래프 플로우 보기"):
            if "graph" in st.session_state:
                # 메인 영역에 그래프 표시
                st.write("### 🎯 RAG 플로우 다이어그램")
                graph = st.session_state["graph"]
                
                try:
                    # visualize_graph 함수를 통해 이미지 데이터 직접 가져오기
                    image_data = graph.get_graph().draw_mermaid_png(
                        background_color="white"
                    )
                    if image_data:
                        st.image(image_data, caption="RAG 플로우 다이어그램")
                    else:
                        st.warning("그래프 이미지를 생성할 수 없습니다.")
                except Exception as e:
                    st.error(f"그래프 시각화 중 오류 발생: {str(e)}")
            else:
                st.warning("그래프가 아직 초기화되지 않았습니다.")

        return uploaded_file, uploaded_dept_file
