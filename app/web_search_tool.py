from langchain_teddynote.tools.tavily import TavilySearch
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 최대 검색 결과를 3으로 설정
web_search_tool = TavilySearch(max_results=3)