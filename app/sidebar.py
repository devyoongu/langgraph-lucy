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

        # # 폼 UI
        # st.write("상담이 필요한 경우 연락처를 남겨주세요")

        # # 연락처 FORM 추가
        # with st.form(key="contact_form"):
        #     # 지역 선택 추가
        #     region = (
        #         st.selectbox(
        #             "Select your region",
        #             [
        #                 "Seoul",
        #                 "Busan",
        #                 "Daegu",
        #                 "Incheon",
        #                 "Gwangju",
        #                 "Daejeon",
        #                 "Ulsan",
        #                 "Other",
        #             ],
        #         ),
        #     )
        #     name = st.text_input("Name")
        #     phone_number = st.text_input("Phone Number")
        #     submit_button = st.form_submit_button(label="Submit")

        # # 버튼 클릭 후 상태 관리
        # if submit_button:
        #     st.session_state["form_submitted"] = True

        #     # 세션 상태에 저장
        #     st.session_state["form_data"] = {
        #         "region": region[0],
        #         "name": name,
        #         "phoneNumber": phone_number,
        #         "chatThreadId": st.session_state.get("chat_thread_id"),
        #     }

        #     st.write("Form submitted successfully!")
        #     st.write(st.session_state["form_data"])

        # # API 요청 처리
        # if st.session_state.get("form_submitted", False):
        #     form_data = st.session_state.get("form_data", {})
        #     try:
        #         response = requests.post(
        #             "http://localhost:8080/api/contact",
        #             json=form_data,
        #         )
        #         if response.status_code == 200:
        #             st.success("감사합니다! 연락처가 성공적으로 제출되었습니다.")
        #             st.session_state["form_submitted"] = False  # 상태 초기화
        #         else:
        #             st.error(f"요청이 실패했습니다. 상태 코드: {response.status_code}")
        #             st.error(f"응답 메시지: {response.text}")
        #     except Exception as e:
        #         st.error(f"API 요청 중 오류 발생: {str(e)}")

        return uploaded_file, uploaded_dept_file
