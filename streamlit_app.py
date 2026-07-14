import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AEGIS", page_icon="🛡️")
st.title("AEGIS — Trust-Verified Jira Automation")
st.caption("Type a request. Low-risk actions execute immediately; high-risk actions go to Slack for approval.")

if "history" not in st.session_state:
    st.session_state.history = []

text = st.chat_input("e.g. add a comment on AG-1 saying deployment is complete")

if text:
    with st.spinner("AEGIS is interpreting and risk-scoring your request..."):
        resp = requests.post(f"{API_BASE_URL}/aegis/request", json={"text": text}, timeout=30)
        resp.raise_for_status()
        st.session_state.history.append({"request": text, "response": resp.json()})

for item in reversed(st.session_state.history):
    with st.chat_message("user"):
        st.write(item["request"])

    with st.chat_message("assistant"):
        body = item["response"]
        status = body["status"]

        if status == "auto_executed":
            st.success(f"Executed immediately (low risk).\n\n```{body['detail']}```")
        elif status == "pending_approval":
            detail = body["detail"]
            st.warning(
                f"Pending human approval in Slack — risk {detail['risk_score']}/100.\n\n"
                f"**Rationale:** {detail['rationale']}"
            )
            if st.button("Check status", key=body["request_id"]):
                status_resp = requests.get(f"{API_BASE_URL}/aegis/status/{body['request_id']}", timeout=10)
                st.json(status_resp.json())
        else:
            st.error(f"{status}: {body['detail']}")
