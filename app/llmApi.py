import requests
import streamlit as st


# API 요청 함수
def send_chat_log_to_api(chat_logs):
    url = "http://localhost:8080/api/chat-log"
    payload = {
        "chatThreadId": st.session_state.get("chat_thread_id"),
        "chatLogs": chat_logs,
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        response_data = response.json()
    except requests.RequestException as e:
        # 백엔드(:8080)가 없으면 채팅로그 저장만 건너뛰고 답변 흐름은 유지한다.
        print(f"[WARN] chat-log API 전송 실패(무시): {e}")
        return
    if "data" in response_data and "id" in response_data["data"]:
        chat_thread_id = response_data["data"]["id"]
        st.session_state["chat_thread_id"] = chat_thread_id


def call_external_api(sqlQuery):
    """외부 API 호출."""
    api_url = "http://localhost:8080/api/sqldeck/execute"
    api_headers = {"Content-Type": "application/json"}
    api_body = {"sqlQuery": sqlQuery}
    try:
        api_response = requests.post(api_url, headers=api_headers, json=api_body)
        api_response.raise_for_status()
        return api_response.json()
    except requests.RequestException as e:
        # assistant chat_message 컨테이너 안에서 호출되므로 chat_message 를
        # 다시 열면 중첩 예외가 난다. inline 으로 표시한다.
        st.error(f"External API call failed: {str(e)}")
        return {"error": "API call failed"}
