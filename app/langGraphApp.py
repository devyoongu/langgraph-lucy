from retriever import load_existing_retriever, process_file
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
from langchain_teddynote.messages import stream_graph, invoke_graph, random_uuid
from langchain_core.messages.chat import ChatMessage
from langchain_teddynote import logging
from dotenv import load_dotenv

logging.langsmith("[Project] theDream RAG")

load_dotenv()

# 초기화 함수 호출 추가
initialize_environment()
initialize_session()

# 사이드바 렌더링
uploaded_file, uploaded_dept_file = render_sidebar()

# 파일이 업로드 되었을 때
if uploaded_file:
    process_file(uploaded_file, "document")
elif uploaded_dept_file:
    process_file(uploaded_dept_file, "department")
else:
    load_existing_retriever("document")
    load_existing_retriever("department")

pdf_retriever = st.session_state["document_retriever"]
dept_retriever = st.session_state["department_retriever"]

# 이전 대화를 출력
def print_messages():
    for chat_message in st.session_state["messages"]:
        st.chat_message(chat_message.role).write(chat_message.content)

# 이전 대화 기록 출력
print_messages()
# 사용자의 입력
user_input = st.chat_input("궁금한 내용을 물어보세요!")

# 상태 정의
class GraphState(TypedDict):
    question: Annotated[str, "The question to answer"]
    generation: Annotated[str, "The generation from the LLM"]
    web_search: Annotated[str, "Whether to add search"]
    documents: Annotated[List[str], "The documents retrieved"]

# region 노드 정의 
# 문서 검색 노드
def retrieve(state: GraphState):
    print("\n==== RETRIEVE ====\n")
    question = state["question"]

    print(f"question is {question}")

    # 문서 검색 수행
    documents = pdf_retriever.invoke(question)

    return {"documents": documents}


# 답변 생성 노드
def generate(state: GraphState):
    print("\n==== GENERATE ====\n")
    question = state["question"]
    documents = state["documents"]

    print(f"generate documents is {documents}")
    print(f"generate question is {question}")

    # RAG를 사용한 답변 생성
    generation = rag_chain.invoke({"context": documents, "question": question})
    print(f"\n**Source**\n- {documents[0].metadata['source']} (page {documents[0].metadata['page']})")
    
    # 응답 반환
    return {"generation": generation}


# 문서 평가 노드
def grade_documents(state: GraphState):
    print("\n==== [CHECK DOCUMENT RELEVANCE TO QUESTION] ====\n")
    question = state["question"]
    print(f"grade_documents question is {question}")
    documents = state["documents"]

    print(f"grade_documents documents is {documents}")

    # 필터링된 문서
    filtered_docs = []
    relevant_doc_count = 0

    for d in documents:
        # Question-Document 의 관련성 평가
        score = retrieval_grader.invoke(
            {"question": question, "document": d.page_content}
        )
        grade = score.binary_score

        if grade == "yes":
            print("==== [GRADE: DOCUMENT RELEVANT] ====")
            # 관련 있는 문서를 filtered_docs 에 추가
            filtered_docs.append(d)
            relevant_doc_count += 1
        else:
            print("==== [GRADE: DOCUMENT NOT RELEVANT] ====")
            continue

    # 관련 문서가 없으면 웹 검색 수행
    web_search = "Yes" if relevant_doc_count == 0 else "No"
    return {"documents": filtered_docs, "web_search": web_search}


# 쿼리 재작성 노드
def query_rewrite(state: GraphState):
    print("\n==== [REWRITE QUERY] ====\n")
    question = state["question"]
    print(f"question is {question}")

    # 질문 재작성
    better_question = question_rewriter.invoke({"question": question})
    return {"question": better_question}


# 웹 검색 노드
def web_search(state: GraphState):
    print("\n==== [WEB SEARCH] ====\n")
    question = state["question"]
    documents = state["documents"]

    # 웹 검색 수행
    docs = web_search_tool.invoke({"query": question})
    # 검색 결과를 문서 형식으로 변환
    web_results = "\n".join([d["content"] for d in docs])
    web_results = Document(page_content=web_results)
    documents.append(web_results)

    return {"documents": documents}

# 조건부 엣지 노드 
def decide_to_generate(state: GraphState):
    # 평가된 문서를 기반으로 다음 단계 결정
    print("==== [ASSESS GRADED DOCUMENTS] ====")
    # 웹 검색 필요 여부
    web_search = state["web_search"]
    print(f"decide_to_generate web_search is {web_search}")

    if web_search == "Yes":
        # 웹 검색으로 정보 보강이 필요한 경우
        print(
            "==== [DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, QUERY REWRITE] ===="
        )
        # 쿼리 재작성 노드로 라우팅
        return "query_rewrite"
    else:
        # 관련 문서가 존재하므로 답변 생성 단계(generate) 로 진행
        print("==== [DECISION: GENERATE] ====")
        return "generate"
# endregion 

### 그래프 생성 

# 그래프 상태 초기화
workflow = StateGraph(GraphState)

# 노드 정의
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)
workflow.add_node("query_rewrite", query_rewrite)
workflow.add_node("web_search_node", web_search)

# 엣지 연결
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "grade_documents")

# 문서 평가 노드에서 조건부 엣지 추가
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "query_rewrite": "query_rewrite",
        "generate": "generate",
    },
)

# 엣지 연결
workflow.add_edge("query_rewrite", "web_search_node")
workflow.add_edge("web_search_node", "generate")
workflow.add_edge("generate", END)

# 그래프 컴파일
app = workflow.compile()

# 새로운 메시지를 추가
def add_message(role, message):
    st.session_state["messages"].append(ChatMessage(role=role, content=message))

# 사용자 입력 처리 함수
def process_input(input_text):
    chat_thread_id = st.session_state.get("chat_thread_id")
    # 사용자 메시지 출력
    st.chat_message("user").write(input_text)
    add_message("user", input_text)

    ### 그래프 실행 
    config = RunnableConfig(recursion_limit=10, configurable={"thread_id": random_uuid()})
    inputs = {
        "question": input_text,
    }

    # AI 응답을 위한 채팅 메시지 컨테이너 생성
    with st.chat_message("assistant"):
        container = st.empty()
        
        try:
            # invoke_graph 사용
            response = invoke_graph(app, inputs, config)

            print(f"response is >>> {response}")
            
            if response and "generation" in response:
                full_response = response["generation"]
                container.markdown(full_response)
                add_message("assistant", full_response)
                
        except Exception as e:
            print(f"Error during graph execution: {str(e)}")
            st.error("응답 생성 중 오류가 발생했습니다.")

# 사용자 입력 처리
if user_input:
    process_input(user_input)