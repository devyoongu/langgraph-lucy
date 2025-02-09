from langchain_core.runnables import RunnableConfig
import streamlit as st
from states import GraphState
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, StateGraph, START
from langgraph.checkpoint.memory import MemorySaver

def stream_graph(
    app,
    query: str,
    streamlit_container,
    thread_id: str,
):
    config = RunnableConfig(
        recursion_limit=30, 
        configurable={
            "thread_id": thread_id,
            "checkpointer": MemorySaver()
        }
    )

    # AgentState 객체를 활용하여 질문을 입력합니다.
    inputs = GraphState(question=query)

    # app.stream을 통해 입력된 메시지에 대한 출력을 스트리밍합니다.
    actions = {
        "retrieve": "🔍 문서를 조회하는 중입니다.",
        "grade_documents": "👀 조회한 문서 중 중요한 내용을 추려내는 중입니다.",
        "rag_answer": "🔥 문서를 기반으로 답변을 생성하는 중입니다.",
        "general_answer": "🔥 문서를 기반으로 답변을 생성하는 중입니다.",
        "web_search_node": "🛜 웹 검색을 진행하는 중입니다.",
    }

    try:
        # streamlit_container
        with streamlit_container.status(
            "😊 열심히 생각중 입니다...", expanded=True
        ) as status:
            st.write("🧑‍💻 질문의 의도를 분석하는 중입니다.")
            for output in app.stream(inputs, config=config):
                # 출력된 결과에서 키와 값을 순회합니다.
                for key, value in output.items():
                    # 노드의 이름과 해당 노드에서 나온 출력을 출력합니다.
                    if key in actions:
                        print(f"actions[key] is {actions[key]}")    
                        st.write(actions[key])
                # 출력 값을 예쁘게 출력합니다.
            status.update(label="답변 완료", state="complete", expanded=False)
    except GraphRecursionError as e:
        print(f"Recursion limit reached: {e}")
    return app.get_state(config=config).values