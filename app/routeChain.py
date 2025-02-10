from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from chainUtils import MODEL_NAME

# ✅ LLM 인스턴스 생성
llm = ChatOpenAI(model=MODEL_NAME, temperature=0)

# ✅ 질문을 라우팅할 데이터 모델 정의
class RouteQuery(BaseModel):
    """질문을 가장 관련성이 높은 벡터스토어로 라우팅"""

    # 질문이 벡터스토어("document", "department") 중 어디로 가야 하는지 판단
    datasource: Literal["document", "department"] = Field(
        ..., description="Route the question to the appropriate vectorstore."
    )

# ✅ 구조화된 LLM 라우터 생성
structured_llm_router = llm.with_structured_output(RouteQuery)

# ✅ LLM 기반 질문 분석 프롬프트 정의
system_prompt = """You are an expert at routing user questions to the correct knowledge source.
- If the question is related to organizational structure, department names, or contact details, use "department".
- If the question is related to general document information, laws, or reports, use "document".
Return only "document" or "department"."""

# ✅ 프롬프트 템플릿 생성
route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{question}"),
    ]
)

# ✅ 프롬프트와 LLM 라우터 결합
question_router = route_prompt | structured_llm_router
