import streamlit as st

def render_buttons():
    """
    버튼 생성 로직을 처리하는 함수.
    
    Returns:
        str: 선택된 카테고리 텍스트 (None if no button is clicked)
    """
    selected_category = None
    questions = [
        "HR팀 직원 연락처 및 담당 업무 알려줘",
        "채용 담당자 연락처 알려줘",
        "탁구 대회 참가자 리스트에 대해 알려줘",
        "타운홀 미팅 장소 및 공유 내용에 대해 알려줘 ",
        "2024년 야유회 일정 및 장소에 대해 알려줘",
        "2024년 노벨 문학상 수상자에 대해 알려줘"
    ]

    columns = st.columns(len(questions))  # 질문 개수만큼 컬럼 생성

    for idx, question in enumerate(questions):
        with columns[idx]:  # 각 컬럼에 버튼 배치
            if st.button(question):
                selected_category = question

    return selected_category
