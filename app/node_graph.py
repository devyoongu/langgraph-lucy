from langchain_core.runnables import RunnableConfig
from typing import List, Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.documents import Document
from retriever import load_existing_retriever
from questionRetrieval import retrieval_grader
from queryRewrite import question_rewriter
from web_search_tool import web_search_tool
from naiveRagChain import rag_chain as rag_chain
from langgraph.checkpoint.memory import MemorySaver
from states import GraphState
from routeChain import question_router
from sqlChain import sql_chain


# region 노드 정의
def route_retriever(state: GraphState):
    print("\n==== [ROUTING QUESTION ROUTER] ====\n")
    question = state["question"]
    print(f"Routing question: {question}")

    # ✅ LLM을 사용하여 질문의 적절한 데이터 소스 선택
    retriever_type = question_router.invoke({"question": question}).datasource

    print(f"Selected retriever: {retriever_type}")
    # 질문 라우팅 결과에 따른 노드 라우팅
    return {"retriever_type": retriever_type}

# 문서 검색 노드
def retrieve(state: GraphState):
    print("\n==== RETRIEVE ====\n")
    question = state["question"]
    retriever_type = state["retriever_type"]  # LLM이 선택한 인덱스

    print(f"Retrieving from index: {retriever_type}")
    retriever = load_existing_retriever(retriever_type)  # 선택된 인덱스에서 검색
    # 문서 검색 수행
    documents = retriever.invoke(question)

    return {"documents": documents}


def sql_generate(state: GraphState):
    print("\n==== GENERATE ====\n")
    question = state["question"]
    documents = state["documents"]

    print(f"sql_generate documents is {documents}")

    # RAG를 통한 SQL 쿼리 생성
    sql_query = sql_chain.invoke({"context": documents, "question": question})
    print(f"sql_generate sql_query is {sql_query}") 

    return {"generation": sql_query, "sql_query": sql_query}


# 답변 생성 노드
def generate(state: GraphState):
    print("\n==== GENERATE ====\n")
    question = state["question"]
    documents = state["documents"]

    print(f"generate documents is {documents}")
    print(f"generate question is {question}")

    # RAG를 사용한 답변 생성
    generation = rag_chain.invoke({"context": documents, "question": question})

    # metadata 체크 추가
    if documents and hasattr(documents[0], "metadata"):
        source = documents[0].metadata.get("source", "unknown")
        page = documents[0].metadata.get("page", 1)
        print(f"\n**Source**\n- {source} (page {page})")

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
    if relevant_doc_count == 0:
        web_search = "Yes"
    else:
        web_search = "No"
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
    print(f"web_search question is {question}")

    # 웹 검색 수행
    docs = web_search_tool.invoke({"query": question})

    # 각 검색 결과 출력
    print("\nSearch Results:")
    for i, doc in enumerate(docs):
        print(f"\nResult {i+1}:")
        print(f"Content: {doc['content']}")
        if "metadata" in doc:
            print(f"Metadata: {doc['metadata']}")

    # 검색 결과를 문서 형식으로 변환
    web_results = "\n".join([d["content"] for d in docs])
    web_results = Document(
        page_content=web_results, metadata={"source": "web_search", "page": 1}
    )
    documents.append(web_results)

    return {"documents": documents}


# 조건부 엣지 노드
def decide_to_question_router(state: GraphState):
    print("\n==== [ROUTING QUESTION ROUTER] ====\n")

    retriever_type = state["retriever_type"]
    # 질문 라우팅 결과에 따른 노드 라우팅
    if retriever_type == "documents":
        print("==== [ROUTE QUESTION TO grade_documents] ====")
        return "grade_documents"
    elif retriever_type == "department":
        print("==== [ROUTE QUESTION TO sql_generate] ====")
        return "sql_generate"

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
def create_graph():
    # 메모리 체크포인터 생성
    memory_checkpointer = MemorySaver()

    # 그래프 상태 초기화
    workflow = StateGraph(GraphState)

    # 노드 정의
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("generate", generate)
    workflow.add_node("query_rewrite", query_rewrite)
    workflow.add_node("web_search_node", web_search)
    workflow.add_node("sql_generate", sql_generate)
    workflow.add_node("route_retriever", route_retriever)
    # 엣지 연결 수정
    workflow.add_edge(START, "route_retriever") 
    workflow.add_edge("route_retriever", "retrieve")
    # workflow.add_edge("retrieve", "grade_documents")

    workflow.add_conditional_edges(
        "retrieve",
        decide_to_question_router,
        {
            "grade_documents": "grade_documents",
            "sql_generate": "sql_generate",
        },
    )

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
    workflow.add_edge("sql_generate", END)

    # 그래프 컴파일
    app = workflow.compile(checkpointer=memory_checkpointer)
    return app
