from typing import List
from typing_extensions import TypedDict, Annotated


# 그래프의 상태 정의
class GraphState(TypedDict):
    question: Annotated[str, "The question to answer"]
    generation: Annotated[str, "The generation from the LLM"]
    web_search: Annotated[str, "Whether to add search"]
    retriever_type: Annotated[str, "The type of retriever to use"]
    documents: Annotated[List[str], "The documents retrieved"]
    sql_query: Annotated[str, "The current SQL query"]
    sql_queries: Annotated[List[str], "The history of SQL queries"]
    api_result: Annotated[str, "The result of the API call"]