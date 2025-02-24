from retriever import process_file
from questionRetrieval import retrieval_grader
from queryRewrite import question_rewriter
from web_search_tool import web_search_tool
from naiveRagChain import rag_chain
from sidebar import render_sidebar
from initialize import initialize_environment, initialize_session
from typing import Annotated, List
from typing_extensions import TypedDict
from langchain.schema import Document
import streamlit as st
from langgraph.graph import END, StateGraph, START
from langchain_core.runnables import RunnableConfig
from langchain_teddynote.messages import random_uuid
from langchain_core.messages.chat import ChatMessage
from langchain_teddynote import logging
from dotenv import load_dotenv
from graph_wrapper import stream_graph
from node_graph import create_graph
from button import render_buttons
import time
from llmApi import send_chat_log_to_api

logging.langsmith("[Project] theDream RAG")

load_dotenv()

# 초기화 함수 호출 추가
initialize_environment()
initialize_session()

# 사이드바 렌더링
uploaded_file, uploaded_dept_file = render_sidebar()
selected_category = render_buttons()

# 파일이 업로드 되었을 때
if uploaded_file:
    process_file(uploaded_file, "document")
    # 파일 업로드 후 세션 상태 갱신
    if "last_uploaded_file" not in st.session_state:
        st.session_state.last_uploaded_file = None

    if st.session_state.last_uploaded_file != uploaded_file.name:
        st.session_state.last_uploaded_file = uploaded_file.name
        st.rerun()

elif uploaded_dept_file:
    process_file(uploaded_dept_file, "department")
    # 파일 업로드 후 세션 상태 갱신
    if "last_uploaded_dept_file" not in st.session_state:
        st.session_state.last_uploaded_dept_file = None

    if st.session_state.last_uploaded_dept_file != uploaded_dept_file.name:
        st.session_state.last_uploaded_dept_file = uploaded_dept_file.name
        st.rerun()


# 이전 대화를 출력
def print_messages():
    for chat_message in st.session_state["messages"]:
        st.chat_message(chat_message.role).write(chat_message.content)


# 이전 대화 기록 출력
print_messages()
# 사용자의 입력
user_input = st.chat_input("궁금한 내용을 물어보세요!")


# 새로운 메시지를 추가
def add_message(role, message):
    st.session_state["messages"].append(ChatMessage(role=role, content=message))


# 체인 생성
if "graph" not in st.session_state:
    st.session_state["graph"] = create_graph()

# 사용자 입력 또는 카테고리 선택 처리
if user_input or selected_category:
    # 실제 처리할 입력 결정
    input_text = user_input if user_input else selected_category

    # 사용자의 입력을 화면에 표시
    st.chat_message("user", avatar="🙎‍♂️").write(input_text)
    # 세션 상태에서 그래프 객체를 가져옴
    graph = st.session_state["graph"]

    # AI 답변을 화면에 표시
    with st.chat_message("assistant", avatar="😊"):
        streamlit_container = st.empty()
        # 그래프를 호출하여 응답 생성
        response = stream_graph(
            graph,
            input_text,
            streamlit_container,
            thread_id=random_uuid(),
        )

        # 응답에서 AI 답변 추출
        ai_answer = response["generation"]

        st.write(ai_answer)

        # 평가 폼을 위한 빈 컨테이너 생성
        eval_container = st.empty()

    # 대화기록을 저장한다.
    add_message("user", input_text)
    add_message("assistant", ai_answer)
