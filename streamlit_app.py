import os
import requests
import streamlit as st
from datetime import datetime
from pathlib import Path
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


# Multilingual UI Dictionary for English, Hindi, and Marathi
UI_STRINGS = {
    "en": {
        "title": "Roboserv 4i Enterprise Policy Assistant",
        "subtitle": "Grounded RAG Policy Q&A + Agentic HR Workflow with Confirmation Safety",
        "quick_prompts_title": "💡 Quick Prompts:",
        "p1_label": "How many casual leaves allowed?",
        "p1_query": "How many casual leaves are allowed?",
        "p2_label": "What is the WFH policy?",
        "p2_query": "What is the work-from-home policy?",
        "p3_label": "How many paid leaves do I have?",
        "p3_query": "How many paid leaves do I have?",
        "p4_label": "Apply leave from Oct 5 to Oct 7",
        "p4_query": "Apply casual leave from October 5 to October 7",
        "chat_placeholder": "Ask a policy question or apply for leave...",
        "analyzing": "Analyzing request and consulting policies...",
        "translating": "Translating response...",
        "confirm_required": "⚠️ **Confirmation Required:** A state-changing leave transaction is awaiting your authorization.",
        "confirm_btn": "✅ Confirm Leave Request",
        "submitting": "Submitting authorized leave request...",
        "cancel_btn": "❌ Cancel",
        "clear_btn": "🗑️ Clear Chat History",
        "policy_source": "📚 Policy Source:",
        "download_pdf": "📥 Download PDF",
        "view_pdf": "👁️ View PDF"
    },
    "hi": {
        "title": "Roboserv 4i एंटरप्राइज़ पॉलिसी असिस्टेंट",
        "subtitle": "सत्यापित RAG पॉलिसी प्रश्नोत्तर + सुरक्षा पुष्टिकरण के साथ Agentic HR वर्कफ़्लो",
        "quick_prompts_title": "💡 त्वरित प्रश्न (Quick Prompts):",
        "p1_label": "कैजुअल लीव कितने मिलते हैं?",
        "p1_query": "How many casual leaves are allowed?",
        "p2_label": "WFH (वर्क फ्रॉम होम) नीति क्या है?",
        "p2_query": "What is the work-from-home policy?",
        "p3_label": "मेरे पास कितने पेड लीव हैं?",
        "p3_query": "How many paid leaves do I have?",
        "p4_label": "5 से 7 अक्टूबर तक लीव अप्लाई करें",
        "p4_query": "Apply casual leave from October 5 to October 7",
        "chat_placeholder": "पॉलिसी प्रश्न पूछें या छुट्टी के लिए आवेदन करें...",
        "analyzing": "अनुरोध का विश्लेषण और नीतियों की समीक्षा हो रही है...",
        "translating": "उत्तर का अनुवाद किया जा रहा है...",
        "confirm_required": "⚠️ **पुष्टिकरण आवश्यक:** एक अवकाश आवेदन आपके अनुमोदन की प्रतीक्षा कर रहा है।",
        "confirm_btn": "✅ अवकाश अनुरोध की पुष्टि करें",
        "submitting": "अवकाश अनुरोध सबमिट किया जा रहा है...",
        "cancel_btn": "❌ रद्द करें",
        "clear_btn": "🗑️ चैट इतिहास साफ़ करें",
        "policy_source": "📚 पॉलिसी स्रोत:",
        "download_pdf": "📥 PDF डाउनलोड करें",
        "view_pdf": "👁️ PDF देखें"
    },
    "mr": {
        "title": "Roboserv 4i एंटरप्राइझ पॉलिसी सहाय्यक",
        "subtitle": "पुष्टीकरण सुरक्षेसह ग्राउंडेड RAG पॉलिसी प्रश्नोत्तरे + Agentic HR कार्यप्रवाह",
        "quick_prompts_title": "💡 जलद प्रश्न (Quick Prompts):",
        "p1_label": "किती कॅज्युअल रजा मिळतात?",
        "p1_query": "How many casual leaves are allowed?",
        "p2_label": "वर्क फ्रॉम होम (WFH) धोरण काय आहे?",
        "p2_query": "What is the work-from-home policy?",
        "p3_label": "माझ्याकडे किती सशुल्क रजा शिल्लक आहेत?",
        "p3_query": "How many paid leaves do I have?",
        "p4_label": "5 ते 7 ऑक्टोबरपर्यंत रजेसाठी अर्ज करा",
        "p4_query": "Apply casual leave from October 5 to October 7",
        "chat_placeholder": "धोरणाविषयी प्रश्न विचारा किंवा रजेसाठी अर्ज करा...",
        "analyzing": "विनंतीचे विश्लेषण आणि धोरणांची पडताळणी करत आहे...",
        "translating": "उत्तराचे भाषांतर करत आहे...",
        "confirm_required": "⚠️ **पुष्टीकरण आवश्यक:** रजेचा अर्ज तुमच्या मंजुरीच्या प्रतीक्षेत आहे.",
        "confirm_btn": "✅ रजेचा अर्ज मंजूर करा",
        "submitting": "रजेचा अर्ज सादर करत आहे...",
        "cancel_btn": "❌ रद्द करा",
        "clear_btn": "🗑️ चॅट इतिहास साफ करा",
        "policy_source": "📚 धोरण संदर्भ:",
        "download_pdf": "📥 PDF डाउनलोड करा",
        "view_pdf": "👁️ PDF पहा"
    }
}


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


def get_employee_requests_data(emp_id: str):
    """Retrieve recent leave requests for employee."""
    try:
        r = requests.get(f"{API_BASE_URL}/api/employee/{emp_id}/leave-requests", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass

    try:
        from app.tools.request_tool import get_employee_leave_requests
        return get_employee_leave_requests(emp_id)
    except Exception:
        return []


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

if "app_language" not in st.session_state:
    st.session_state.app_language = "en"


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
        "EMP001": "EMP001 — Abhishek Koli (Electrical & Embedded)",
        "EMP002": "EMP002 — Raj Teli (Robotic & Software Engg)",
        "EMP003": "EMP003 — Hrutvik Owal (Robotic-Design)",
        "EMP004": "EMP004 — Santosh Barai (Robotic-Design)",
        "EMP005": "EMP005 — Divyansh Jha (Electronics & IOT)",
        "EMP006": "EMP006 — Dev Gokha (Software Developer)"
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

    # Recent Leave Requests
    reqs_data = get_employee_requests_data(selected_emp_id)
    with st.expander(f"📋 My Leave Requests ({len(reqs_data)})", expanded=(len(reqs_data) > 0)):
        if reqs_data:
            for r in reqs_data[:5]:
                status = r.get("status", "Pending")
                status_icon = "🟢" if status == "Approved" else ("🟡" if status == "Pending" else "🔴")
                st.markdown(
                    f"**{r.get('request_id')}** — {r.get('leave_type', '').replace('_', ' ').title()}  \n"
                    f"📅 `{r.get('start_date')}` to `{r.get('end_date')}` ({r.get('days')} d)  \n"
                    f"Status: {status_icon} **{status}**"
                )
                st.markdown("---")
        else:
            st.caption("No submitted leave requests yet.")


    st.markdown("---")
    st.subheader("🌐 Language / भाषा")
    lang_map = {
        "en": "English 🇬🇧",
        "hi": "Hindi (हिंदी) 🇮🇳",
        "mr": "Marathi (मराठी) 🚩"
    }
    lang_keys = list(lang_map.keys())
    curr_l = st.session_state.get("app_language", "en")
    curr_idx = lang_keys.index(curr_l) if curr_l in lang_keys else 0
    selected_lang = st.selectbox(
        "Response Language / भाषा निवडा:",
        options=lang_keys,
        format_func=lambda x: lang_map[x],
        index=curr_idx
    )
    if selected_lang != st.session_state.app_language:
        st.session_state.app_language = selected_lang
        st.rerun()

    st.markdown("---")
    st.subheader("💡 Available Actions")
    st.markdown("""
    - 🔍 **Ask Policy Question** (e.g. *WFH rules, travel per diem*)
    - 📅 **Check Leave Balance**
    - 📝 **Apply Leave** (requires confirmation)
    - 🔎 **Track Request Status** (e.g. *Status for LV1025*)
    """)

    # Policy Document Repository Browser
    with st.expander("📁 Company Policy Documents"):
        doc_dir = Path("data/documents")
        if doc_dir.exists():
            pdf_files = sorted([p.name for p in doc_dir.glob("*.pdf")])
            sel_pdf = st.selectbox("Select Policy PDF:", options=pdf_files, key="sb_pdf_select")
            if sel_pdf:
                sel_path = doc_dir / sel_pdf
                with open(sel_path, "rb") as spf:
                    st.download_button(
                        label=f"📥 Download {sel_pdf}",
                        data=spf.read(),
                        file_name=sel_pdf,
                        mime="application/pdf",
                        key="sidebar_dl_pdf",
                        use_container_width=True
                    )
                st.link_button(
                    label=f"👁️ View {sel_pdf}",
                    url=f"{API_BASE_URL}/api/documents/{sel_pdf}",
                    use_container_width=True
                )

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_confirmation = None
        st.rerun()


# ---------------------------------------------------------
# MAIN PAGE: Chat Interface
# ---------------------------------------------------------

curr_lang = st.session_state.get("app_language", "en")
ui = UI_STRINGS.get(curr_lang, UI_STRINGS["en"])

st.markdown(f'<div class="main-title">{ui["title"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">{ui["subtitle"]}</div>', unsafe_allow_html=True)

# Quick Prompt Suggestions & Multilingual Language Switcher
col_head, col_lang_btns = st.columns([3, 2.2])
with col_head:
    st.markdown(f"**{ui['quick_prompts_title']}**")
with col_lang_btns:
    l_c1, l_c2, l_c3 = st.columns(3)
    with l_c1:
        if st.button("🇬🇧 English", key="top_l_en", type="primary" if curr_lang == "en" else "secondary", use_container_width=True):
            st.session_state.app_language = "en"
            st.rerun()
    with l_c2:
        if st.button("🇮🇳 हिंदी", key="top_l_hi", type="primary" if curr_lang == "hi" else "secondary", use_container_width=True):
            st.session_state.app_language = "hi"
            st.rerun()
    with l_c3:
        if st.button("🚩 मराठी", key="top_l_mr", type="primary" if curr_lang == "mr" else "secondary", use_container_width=True):
            st.session_state.app_language = "mr"
            st.rerun()

col_p1, col_p2, col_p3, col_p4 = st.columns(4)
with col_p1:
    if st.button(ui["p1_label"], use_container_width=True, key="qp_1"):
        st.session_state.queued_prompt = ui["p1_query"]
        st.session_state.queued_display = ui["p1_label"]
with col_p2:
    if st.button(ui["p2_label"], use_container_width=True, key="qp_2"):
        st.session_state.queued_prompt = ui["p2_query"]
        st.session_state.queued_display = ui["p2_label"]
with col_p3:
    if st.button(ui["p3_label"], use_container_width=True, key="qp_3"):
        st.session_state.queued_prompt = ui["p3_query"]
        st.session_state.queued_display = ui["p3_label"]
with col_p4:
    if st.button(ui["p4_label"], use_container_width=True, key="qp_4"):
        st.session_state.queued_prompt = ui["p4_query"]
        st.session_state.queued_display = ui["p4_label"]

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
        
        # Display policy citation if available (Option 2: Top relevant source)
        if msg.get("sources"):
            st.markdown(f"##### {ui['policy_source']}")
            for s in msg["sources"][:1]:
                doc_name = s.get("document", "")
                page_num = s.get("page", 1)
                dept = s.get("department", "HR")

                st.markdown(
                    f'<div class="citation-card">'
                    f'📄 <b>{doc_name}</b> — Page <b>{page_num}</b> | '
                    f'Department: <i>{dept}</i>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                # PDF Download and Browser View buttons
                pdf_path = Path("data/documents") / doc_name
                if pdf_path.exists():
                    p_col1, p_col2, _ = st.columns([1.5, 1.5, 3])
                    with open(pdf_path, "rb") as pf:
                        pdf_bytes = pf.read()
                    with p_col1:
                        st.download_button(
                            label=ui["download_pdf"],
                            data=pdf_bytes,
                            file_name=doc_name,
                            mime="application/pdf",
                            key=f"dl_msg_{idx}_{doc_name}",
                            help=f"Download official {doc_name}"
                        )
                    with p_col2:
                        st.link_button(
                            label=ui["view_pdf"],
                            url=f"{API_BASE_URL}/api/documents/{doc_name}",
                            help=f"Open {doc_name} in browser tab"
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
    st.warning(ui["confirm_required"])
    
    col_c1, col_c2 = st.columns([1, 4])
    with col_c1:
        if st.button(ui["confirm_btn"], type="primary", use_container_width=True):
            # Process confirmed leave request
            with st.spinner(ui.get("submitting", "Submitting authorized leave request...")):
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
        if st.button(ui["cancel_btn"], use_container_width=False):
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
user_input = st.chat_input(ui["chat_placeholder"])

# Check if a quick button was clicked
display_user_text = None
if "queued_prompt" in st.session_state and st.session_state.queued_prompt:
    user_input = st.session_state.queued_prompt
    display_user_text = st.session_state.get("queued_display", user_input)
    st.session_state.queued_prompt = None
    st.session_state.queued_display = None
else:
    display_user_text = user_input

if user_input:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": display_user_text})
    with st.chat_message("user"):
        st.markdown(display_user_text)

    # Invoke assistant
    with st.chat_message("assistant"):
        with st.spinner(ui["analyzing"]):
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
            curr_app_lang = st.session_state.get("app_language", "en")
            curr_lang = "en"
            trans_cache = {"en": answer}
            if curr_app_lang != "en":
                with st.spinner(ui["translating"]):
                    displayed_answer = call_translate_api(answer, curr_app_lang)
                    curr_lang = curr_app_lang
                    trans_cache[curr_app_lang] = displayed_answer

            st.markdown(displayed_answer)

            if sources:
                st.markdown(f"##### {ui['policy_source']}")
                for s in sources[:1]:
                    doc_name = s.get("document", "")
                    page_num = s.get("page", 1)
                    dept = s.get("department", "HR")

                    st.markdown(
                        f'<div class="citation-card">'
                        f'📄 <b>{doc_name}</b> — Page <b>{page_num}</b> | '
                        f'Department: <i>{dept}</i>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    pdf_path = Path("data/documents") / doc_name
                    if pdf_path.exists():
                        p_col1, p_col2, _ = st.columns([1.5, 1.5, 3])
                        with open(pdf_path, "rb") as pf:
                            pdf_bytes = pf.read()
                        with p_col1:
                            st.download_button(
                                label=ui["download_pdf"],
                                data=pdf_bytes,
                                file_name=doc_name,
                                mime="application/pdf",
                                key=f"dl_live_{doc_name}",
                                help=f"Download official {doc_name}"
                            )
                        with p_col2:
                            st.link_button(
                                label=ui["view_pdf"],
                                url=f"{API_BASE_URL}/api/documents/{doc_name}",
                                help=f"Open {doc_name} in browser tab"
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
