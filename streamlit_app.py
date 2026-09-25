"""Streamlit Web Dashboard for Roboserv 4i Enterprise Policy Assistant."""

import os
import requests
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Roboserv 4i Enterprise Policy Assistant",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# Custom CSS for polished enterprise look
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .citation-card {
        background-color: #F8FAFC;
        border-left: 4px solid #2563EB;
        padding: 8px 12px;
        margin: 6px 0;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    .action-badge {
        display: inline-block;
        background-color: #EFF6FF;
        color: #1D4ED8;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .confirmation-box {
        background-color: #FEF3C7;
        border: 1px solid #F59E0B;
        border-radius: 8px;
        padding: 14px;
        margin: 10px 0;
    }
    .metric-card {
        background-color: #F1F5F9;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        margin-bottom: 8px;
    }
    .lang-badge {
        display: inline-block;
        background-color: #EEF2FF;
        color: #4F46E5;
        border: 1px solid #C7D2FE;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.76rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)


# Helper function to query backend or direct fallback
def get_employee_data(emp_id: str):
    """Retrieve employee details and leave balance from API or direct fallback."""
    try:
        r = requests.get(f"{API_BASE_URL}/api/employee/{emp_id}", timeout=3)
        if r.status_code == 200:
            emp = r.json()
            r_bal = requests.get(f"{API_BASE_URL}/api/employee/{emp_id}/leave-balance", timeout=3)
            bal = r_bal.json() if r_bal.status_code == 200 else {}
            return emp, bal
    except Exception:
        pass

    # Direct fallback if API service is not running
    try:
        from app.tools.employee_tool import get_employee
        from app.tools.leave_tool import get_leave_balance
        emp = get_employee(emp_id)
        bal = get_leave_balance(emp_id)
        return emp, bal
    except Exception:
        return None, None


def call_chat_api(emp_id: str, message: str, confirmed: bool = False, extra_state: dict = None):
    """Send chat request to FastAPI endpoint with fallback to internal graph."""
    payload = {
        "employee_id": emp_id,
        "message": message,
        "confirmed": confirmed,
        "extra_state": extra_state
    }
    try:
        res = requests.post(f"{API_BASE_URL}/api/chat", json=payload, timeout=20)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass

    # Direct LangGraph fallback
    try:
        from app.agent.graph import run_agent_workflow
        result = run_agent_workflow(
            query=message,
            employee_id=emp_id,
            confirmed=confirmed,
            extra_state=extra_state
        )
        return {
            "answer": result.get("final_response", ""),
            "intent": result.get("intent", "general_question"),
            "sources": result.get("sources", []),
            "actions": result.get("actions", []),
            "confirmation_required": result.get("confirmation_required", False),
            "confirmed": result.get("confirmed", False),
            "request_id": result.get("request_id"),
            "extra_state": {
                "start_date": result.get("start_date"),
                "end_date": result.get("end_date"),
                "leave_type": result.get("leave_type"),
                "requested_days": result.get("requested_days")
            }
        }
    except Exception as e:
        return {
            "answer": f"Error running assistant: {str(e)}",
            "intent": "error",
            "sources": [],
            "actions": [],
            "confirmation_required": False
        }


def call_translate_api(text: str, target_lang: str) -> str:
    """Translate text to Hindi or Marathi via backend API with local fallback."""
    if not text or target_lang in ("en", "english"):
        return text
    try:
        r = requests.post(f"{API_BASE_URL}/api/translate", json={"text": text, "target_lang": target_lang}, timeout=8)
        if r.status_code == 200:
            return r.json().get("translated_text", text)
    except Exception:
        pass

    # Direct fallback
    try:
        from app.agent.llm import translate_text
        return translate_text(text, target_lang)
    except Exception:
        return text


# Initialize Session State
if "messages" not in st.session_state:
    init_msg = (
        "Hello! I am your **Roboserv 4i Enterprise Policy Assistant**.\n\n"
        "I can help you answer company policy questions with exact source citations, "
        "check your leave balances, and submit leave requests safely with your confirmation."
    )
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": init_msg,
            "original_content": init_msg,
            "current_lang": "en",
            "translations": {"en": init_msg},
            "sources": [],
            "actions": []
        }
    ]

if "pending_confirmation" not in st.session_state:
    st.session_state.pending_confirmation = None


# ---------------------------------------------------------
# SIDEBAR: Employee Profile & Leave Balances
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/briefcase--v1.png", width=64)
    st.title("Roboserv 4i Portal")
    st.caption("Enterprise HRMS & Policy Suite")

    st.markdown("---")
    st.subheader("👤 Active Employee")

    employee_options = {
        "EMP001": "EMP001 — Dev Kumar (AI/ML)",
        "EMP002": "EMP002 — Priya Sharma (Cloud)",
        "EMP003": "EMP003 — Rohan Verma (Frontend)",
        "EMP004": "EMP004 — Ananya Iyer (HR)",
        "EMP005": "EMP005 — Vikram Malhotra (Executive)"
    }

    selected_emp_id = st.selectbox(
        "Select Active User:",
        options=list(employee_options.keys()),
        format_func=lambda x: employee_options[x],
        index=0
    )

    emp_info, bal_info = get_employee_data(selected_emp_id)

    if emp_info:
        st.write(f"**Name:** {emp_info.get('name')}")
        st.write(f"**Email:** `{emp_info.get('email')}`")
        st.write(f"**Department:** {emp_info.get('department')}")
        st.write(f"**Manager:** {emp_info.get('manager')}")
    else:
        st.info("Employee record loading...")

    st.markdown("---")
    st.subheader("📊 Leave Balance")

    if bal_info and "error" not in bal_info:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(label="Casual", value=f"{bal_info.get('casual_leave', 0)} d")
        with c2:
            st.metric(label="Sick", value=f"{bal_info.get('sick_leave', 0)} d")
        with c3:
            st.metric(label="Paid", value=f"{bal_info.get('paid_leave', 0)} d")
    else:
        st.info("Leave balances loading...")

    st.markdown("---")
    st.subheader("🌐 Language / भाषा")
    lang_map = {
        "en": "English 🇬🇧",
        "hi": "Hindi (हिंदी) 🇮🇳",
        "mr": "Marathi (मराठी) 🚩"
    }
    selected_lang = st.selectbox(
        "Response Language / भाषा निवडा:",
        options=list(lang_map.keys()),
        format_func=lambda x: lang_map[x],
        index=0
    )

    st.markdown("---")
    st.subheader("💡 Available Actions")
    st.markdown("""
    - 🔍 **Ask Policy Question** (e.g. *WFH rules, travel per diem*)
    - 📅 **Check Leave Balance**
    - 📝 **Apply Leave** (requires confirmation)
    - 🔎 **Track Request Status** (e.g. *Status for LV1025*)
    """)

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_confirmation = None
        st.rerun()


# ---------------------------------------------------------
# MAIN PAGE: Chat Interface
# ---------------------------------------------------------

st.markdown('<div class="main-title">Roboserv 4i Enterprise Policy Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Grounded RAG Policy Q&A + Agentic HR Workflow with Confirmation Safety</div>', unsafe_allow_html=True)

# Quick Prompt Suggestions
st.markdown("**Quick Prompts:**")
col_p1, col_p2, col_p3, col_p4 = st.columns(4)
with col_p1:
    if st.button("How many casual leaves allowed?", use_container_width=True):
        prompt_input = "How many casual leaves are allowed?"
        st.session_state.queued_prompt = prompt_input
with col_p2:
    if st.button("What is the WFH policy?", use_container_width=True):
        prompt_input = "What is the work-from-home policy?"
        st.session_state.queued_prompt = prompt_input
with col_p3:
    if st.button("How many paid leaves do I have?", use_container_width=True):
        prompt_input = "How many paid leaves do I have?"
        st.session_state.queued_prompt = prompt_input
with col_p4:
    if st.button("Apply leave from Oct 5 to Oct 7", use_container_width=True):
        prompt_input = "Apply casual leave from October 5 to October 7"
        st.session_state.queued_prompt = prompt_input

st.markdown("---")

# Display conversation messages
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        # Show active language indicator if translated
        curr_lang = msg.get("current_lang", "en")
        if curr_lang == "hi":
            st.markdown("<span class='lang-badge'>🌐 भाषा: <b>हिंदी (Hindi)</b></span>", unsafe_allow_html=True)
        elif curr_lang == "mr":
            st.markdown("<span class='lang-badge'>🌐 भाषा: <b>मराठी (Marathi)</b></span>", unsafe_allow_html=True)

        st.markdown(msg["content"])
        
        # Display policy citations if available
        if msg.get("sources"):
            st.markdown("##### 📚 Sources & Citations:")
            for s in msg["sources"]:
                st.markdown(
                    f'<div class="citation-card">'
                    f'📄 <b>{s.get("document")}</b> — Page <b>{s.get("page")}</b> | '
                    f'Department: <i>{s.get("department", "HR")}</i>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # Display Action badges if any
        if msg.get("actions"):
            for act in msg["actions"]:
                st.markdown(
                    f'<span class="action-badge">⚡ Action: {act.get("action")} ({act.get("status")})</span>',
                    unsafe_allow_html=True
                )

        # Quick Translate Action Buttons for Assistant responses
        if msg["role"] == "assistant" and msg.get("content"):
            if "translations" not in msg:
                msg["translations"] = {"en": msg.get("original_content", msg["content"])}
            if "original_content" not in msg:
                msg["original_content"] = msg["content"]
            if "current_lang" not in msg:
                msg["current_lang"] = "en"

            st.markdown("<div style='margin-top: 6px; margin-bottom: 2px;'></div>", unsafe_allow_html=True)
            col_t1, col_t2, col_t3, _ = st.columns([1.1, 1.1, 1.1, 3.5])
            with col_t1:
                if st.button("🇮🇳 हिंदी", key=f"tr_hi_{idx}", help="हिंदी में अनुवाद करें (Translate to Hindi)"):
                    if "hi" not in msg["translations"]:
                        with st.spinner("हिंदी में अनुवाद हो रहा है..."):
                            msg["translations"]["hi"] = call_translate_api(msg["original_content"], "hi")
                    msg["content"] = msg["translations"]["hi"]
                    msg["current_lang"] = "hi"
                    st.rerun()

            with col_t2:
                if st.button("🚩 मराठी", key=f"tr_mr_{idx}", help="मराठीत भाषांतर करा (Translate to Marathi)"):
                    if "mr" not in msg["translations"]:
                        with st.spinner("मराठीत भाषांतर करत आहे..."):
                            msg["translations"]["mr"] = call_translate_api(msg["original_content"], "mr")
                    msg["content"] = msg["translations"]["mr"]
                    msg["current_lang"] = "mr"
                    st.rerun()

            with col_t3:
                if st.button("🇬🇧 English", key=f"tr_en_{idx}", help="View original English response"):
                    msg["content"] = msg["translations"].get("en", msg["original_content"])
                    msg["current_lang"] = "en"
                    st.rerun()


# Interactive confirmation box if leave confirmation is pending
if st.session_state.pending_confirmation:
    pending = st.session_state.pending_confirmation
    st.markdown("---")
    st.warning("⚠️ **Confirmation Required:** A state-changing leave transaction is awaiting your authorization.")
    
    col_c1, col_c2 = st.columns([1, 4])
    with col_c1:
        if st.button("✅ Confirm Leave Request", type="primary", use_container_width=True):
            # Process confirmed leave request
            with st.spinner("Submitting leave request to database..."):
                resp = call_chat_api(
                    emp_id=selected_emp_id,
                    message="Yes, submit it.",
                    confirmed=True,
                    extra_state=pending
                )
                ans = resp.get("answer", "Request processed.")
                disp_ans = ans
                curr_l = "en"
                t_cache = {"en": ans}
                if selected_lang != "en":
                    disp_ans = call_translate_api(ans, selected_lang)
                    curr_l = selected_lang
                    t_cache[selected_lang] = disp_ans

                st.session_state.messages.append({
                    "role": "user",
                    "content": "Yes, submit it."
                })
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": disp_ans,
                    "original_content": ans,
                    "current_lang": curr_l,
                    "translations": t_cache,
                    "sources": resp.get("sources", []),
                    "actions": resp.get("actions", [])
                })
                st.session_state.pending_confirmation = None
                st.rerun()

    with col_c2:
        if st.button("❌ Cancel", use_container_width=False):
            cancel_msg = "Leave request has been cancelled. No changes were made."
            disp_cancel = cancel_msg
            curr_l = "en"
            t_cache = {"en": cancel_msg}
            if selected_lang != "en":
                disp_cancel = call_translate_api(cancel_msg, selected_lang)
                curr_l = selected_lang
                t_cache[selected_lang] = disp_cancel

            st.session_state.pending_confirmation = None
            st.session_state.messages.append({
                "role": "user",
                "content": "Cancel request."
            })
            st.session_state.messages.append({
                "role": "assistant",
                "content": disp_cancel,
                "original_content": cancel_msg,
                "current_lang": curr_l,
                "translations": t_cache,
                "sources": [],
                "actions": []
            })
            st.rerun()


# Chat Input
user_input = st.chat_input("Ask a policy question or apply for leave...")

# Check if a quick button was clicked
if "queued_prompt" in st.session_state and st.session_state.queued_prompt:
    user_input = st.session_state.queued_prompt
    st.session_state.queued_prompt = None

if user_input:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Invoke assistant
    with st.chat_message("assistant"):
        with st.spinner("Analyzing request and consulting policies..."):
            extra = st.session_state.pending_confirmation if st.session_state.pending_confirmation else None
            response_data = call_chat_api(
                emp_id=selected_emp_id,
                message=user_input,
                confirmed=False,
                extra_state=extra
            )

            answer = response_data.get("answer", "")
            sources = response_data.get("sources", [])
            actions = response_data.get("actions", [])
            conf_req = response_data.get("confirmation_required", False)

            # Auto-translate if user selected Hindi or Marathi
            displayed_answer = answer
            curr_lang = "en"
            trans_cache = {"en": answer}
            if selected_lang != "en":
                with st.spinner(f"Translating response to {lang_map.get(selected_lang)}..."):
                    displayed_answer = call_translate_api(answer, selected_lang)
                    curr_lang = selected_lang
                    trans_cache[selected_lang] = displayed_answer

            st.markdown(displayed_answer)

            if sources:
                st.markdown("##### 📚 Sources & Citations:")
                for s in sources:
                    st.markdown(
                        f'<div class="citation-card">'
                        f'📄 <b>{s.get("document")}</b> — Page <b>{s.get("page")}</b> | '
                        f'Department: <i>{s.get("department", "HR")}</i>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

            if actions:
                for act in actions:
                    st.markdown(
                        f'<span class="action-badge">⚡ Action: {act.get("action")} ({act.get("status")})</span>',
                        unsafe_allow_html=True
                    )

            # Store in session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": displayed_answer,
                "original_content": answer,
                "current_lang": curr_lang,
                "translations": trans_cache,
                "sources": sources,
                "actions": actions
            })

            # Check if confirmation is needed
            if conf_req:
                st.session_state.pending_confirmation = response_data.get("extra_state") or {
                    "start_date": response_data.get("start_date"),
                    "end_date": response_data.get("end_date"),
                    "leave_type": response_data.get("leave_type"),
                    "requested_days": response_data.get("requested_days")
                }
                st.rerun()
