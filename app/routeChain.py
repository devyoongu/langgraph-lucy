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

Use "department" ONLY for questions about:
- Organization structure (조직도)
- Employee information (직원 정보)
- Department names and roles (부서명과 역할)
- Contact details (연락처)
- Job titles and positions (직책과 직위)

Use "document" for all other questions, including:
- Company policies (회사 정책)
- Meeting information (회의 정보)
- Event details (행사 정보)
- General documents (일반 문서)
- Reports and announcements (보고서와 공지사항)
- Training materials (교육 자료)
- Company news (회사 소식)

Return only "document" or "department".

Examples:
Q: "타운홀 미팅 장소가 어디인가요?" -> document (회의 정보는 document)
Q: "HR팀 담당자 연락처 알려주세요" -> department (직원 연락처는 department)
Q: "신입사원 교육 일정이 어떻게 되나요?" -> document (교육 정보는 document)
Q: "개발팀은 몇 층에 있나요?" -> department (부서 위치는 department)
"""

# ✅ 프롬프트 템플릿 생성
route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{question}"),
    ]
)

# ✅ 프롬프트와 LLM 라우터 결합
question_router = route_prompt | structured_llm_router
