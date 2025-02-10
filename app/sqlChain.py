from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from chainUtils import MODEL_NAME
from langchain_teddynote.prompts import load_prompt

# LangChain Hub에서 RAG 프롬프트를 가져와 사용
prompt = load_prompt("prompts/00_sql-generator.yaml", encoding="utf-8")

# LLM 초기화
llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)

# 체인 생성
sql_chain = prompt | llm | StrOutputParser()