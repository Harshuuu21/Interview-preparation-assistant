import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Interview Prep Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { max-width: 900px; padding-top: 2rem; }
h1 { font-weight: 300 !important; letter-spacing: 1px; }

/* Hero header */
.hero-header {
    text-align: center; padding: 2rem 0 1rem;
    border-bottom: 1px solid #334155; margin-bottom: 2rem;
}
.hero-header h1 { font-size: 2.2rem; margin: 0; }
.hero-sub { color: #94a3b8; font-size: 0.95rem; margin-top: 0.3rem; }

/* Question cards */
.q-card {
    background: rgba(30,41,59,0.7); border: 1px solid #334155;
    border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.6rem;
    transition: border-color 0.2s, background 0.2s; cursor: pointer;
}
.q-card:hover { border-color: #3b82f6; background: #1a2035; }
.q-badge {
    display: inline-block; font-size: 10px; text-transform: uppercase;
    letter-spacing: 0.05em; padding: 3px 8px; border-radius: 4px;
    font-weight: 600; margin-right: 10px;
}
.q-badge.behavioural { background: #1e3a5f; color: #64a9f0; }
.q-badge.technical   { background: #1e3b2e; color: #5dbf8a; }
.q-badge.coding      { background: #3b2e1e; color: #e0965a; }
.q-badge.situational { background: #2e1e3b; color: #b07ae0; }
.q-badge.general     { background: #2a3148; color: #8a9bc0; }

/* Score displays */
.score-big {
    font-size: 3rem; font-weight: 700; text-align: center; line-height: 1;
}
.score-high { color: #10b981; }
.score-mid  { color: #f59e0b; }
.score-low  { color: #ef4444; }
.score-label { font-size: 0.85rem; color: #94a3b8; text-align: center; }

/* Breakdown bar */
.bar-track {
    background: #1e293b; height: 6px; border-radius: 3px;
    overflow: hidden; margin: 4px 0;
}
.bar-fill {
    height: 100%; border-radius: 3px; background: #3b82f6;
    transition: width 0.6s ease;
}

/* Feedback sections */
.feedback-card {
    background: rgba(30,41,59,0.7); border: 1px solid #334155;
    border-radius: 10px; padding: 1.5rem; margin-top: 1rem;
}
.section-title {
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.07em; color: #64748b; margin-bottom: 8px;
}

/* Resume review */
.score-circle {
    width: 100px; height: 100px; border-radius: 50%;
    border: 4px solid #334155; display: flex; flex-direction: column;
    align-items: center; justify-content: center; margin: 0 auto 12px;
}
.score-circle.high { border-color: #10b981; }
.score-circle.mid  { border-color: #f59e0b; }
.score-circle.low  { border-color: #ef4444; }
.circle-num { font-size: 28px; font-weight: 700; line-height: 1; }

.improvement-card {
    background: #141c2e; border: 1px solid #1e293b;
    border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;
}
.priority-high   { background: #3d1a1a; color: #ef4444; }
.priority-medium { background: #3d2e10; color: #f59e0b; }
.priority-low    { background: #1a2e1a; color: #10b981; }
.priority-badge {
    display: inline-block; font-size: 10px; padding: 2px 7px;
    border-radius: 3px; font-weight: 600; text-transform: uppercase;
}
.missing-chip {
    display: inline-block; background: #2a1e1e; color: #e07a7a;
    border: 1px solid #3d2a2a; font-size: 12px; padding: 3px 10px;
    border-radius: 4px; margin: 3px 3px 0 0;
}
.verdict-box {
    background: #141c2e; border: 1px solid #1e293b;
    border-left: 3px solid #3b82f6; border-radius: 0 6px 6px 0;
    padding: 12px 14px; font-size: 13px; color: #c0d0f0;
    line-height: 1.6; font-style: italic;
}
.strength-dot {
    display: inline-block; width: 6px; height: 6px; border-radius: 50%;
    background: #10b981; margin-right: 8px; vertical-align: middle;
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    border-radius: 6px 6px 0 0; padding: 8px 20px;
}
</style>
""", unsafe_allow_html=True)

# ── Session State Init ──
for key in ["session", "current_q_idx", "feedback", "iteration", "resume_review", "page"]:
    if key not in st.session_state:
        st.session_state[key] = None
if "page" not in st.session_state or st.session_state.page is None:
    st.session_state.page = "input"
if "iteration" not in st.session_state or st.session_state.iteration is None:
    st.session_state.iteration = 0


def score_class(score, max_val=10):
    pct = score / max_val if max_val else 0
    if pct >= 0.7: return "high"
    if pct >= 0.5: return "mid"
    return "low"


def render_breakdown_bar(label, value, max_val):
    pct = (value / max_val * 100) if max_val else 0
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin:4px 0;">
        <span style="width:120px;font-size:13px;color:#8a9bc0;">{label}</span>
        <div class="bar-track" style="flex:1;">
            <div class="bar-fill" style="width:{pct}%;"></div>
        </div>
        <span style="width:50px;font-size:13px;color:#c0d0f0;text-align:right;">{value}/{max_val}</span>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════
#  PAGE: INPUT
# ══════════════════════════════════════
if st.session_state.page == "input":
    st.markdown('<div class="hero-header"><h1>🎯 Interview Prep Assistant</h1><div class="hero-sub">AI-powered interview preparation with multi-agent intelligence</div></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    company = col1.text_input("Company", placeholder="e.g., Google")
    role = col2.text_input("Role", placeholder="e.g., Software Engineer")

    resume_file = st.file_uploader("Upload Resume (optional)", type=["pdf", "txt"], help="PDF or TXT, max 2MB")

    resume_text = ""
    if resume_file:
        if resume_file.type == "application/pdf":
            import fitz
            doc = fitz.open(stream=resume_file.read(), filetype="pdf")
            resume_text = "\n".join(page.get_text() for page in doc)
        else:
            resume_text = resume_file.read().decode("utf-8", errors="ignore")
        if resume_text.strip():
            st.success(f"✅ Resume loaded: {resume_file.name}")

    if st.button("🚀 Generate Questions", type="primary", use_container_width=True):
        if not company or not role:
            st.error("Please enter both company and role.")
        else:
            from agents.orchestrator import generate_question_set, run_resume_review

            status_container = st.status("Preparing your interview...", expanded=True)

            def update_status(msg):
                status_container.update(label=msg)
                status_container.write(msg)

            session = generate_question_set(
                company, role,
                resume_text=resume_text,
                progress_callback=update_status,
            )

            if session.status == "ready":
                st.session_state.session = session
                st.session_state.page = "questions"

                # Run resume review if we have text
                if resume_text.strip():
                    status_container.update(label="📄 Analyzing your resume...")
                    status_container.write("📄 Analyzing your resume...")
                    try:
                        review = run_resume_review(resume_text, role, company)
                        review["_role"] = role
                        st.session_state.resume_review = review
                    except Exception as e:
                        print(f"Resume review error: {e}")

                status_container.update(label="✅ All done!", state="complete")
                st.rerun()
            else:
                status_container.update(label="❌ Failed to generate questions", state="error")
                st.error("Failed to generate questions. Please try again.")


# ══════════════════════════════════════
#  PAGE: QUESTION LIST
# ══════════════════════════════════════
elif st.session_state.page == "questions":
    session = st.session_state.session

    st.markdown('<div class="hero-header"><h1>🎯 Interview Prep Assistant</h1></div>', unsafe_allow_html=True)
    st.markdown(f"### Your Question Set")
    st.caption(f"**{session.company}** — {session.role} · {len(session.final_questions)} questions")

    # Tabs: Questions + Resume Review (if available)
    tabs = ["📋 Questions"]
    if st.session_state.resume_review:
        tabs.append("📄 Resume Review")

    tab_objects = st.tabs(tabs)

    with tab_objects[0]:
        for idx, q in enumerate(session.final_questions):
            cat = (q.category or "general").lower()
            with st.expander(f"**{q.text}**", expanded=False):
                badge_html = f'<span class="q-badge {cat}">{cat}</span>'
                if q.difficulty:
                    badge_html += f' <span style="font-size:12px;color:#64748b;">Difficulty: {q.difficulty}</span>'
                st.markdown(badge_html, unsafe_allow_html=True)

                col1, col2 = st.columns([1, 1])
                if col1.button("✍️ Answer this question", key=f"ans_{idx}", use_container_width=True):
                    st.session_state.current_q_idx = idx
                    st.session_state.feedback = None
                    st.session_state.iteration = 0
                    st.session_state.page = "answer"
                    st.rerun()

    # Resume Review Tab
    if st.session_state.resume_review and len(tab_objects) > 1:
        with tab_objects[1]:
            review = st.session_state.resume_review
            tier = score_class(review.get("overall_score", 0), 100)

            # Score circle
            st.markdown(f"""
            <div style="text-align:center;margin-bottom:1.5rem;">
                <div class="score-circle {tier}">
                    <span class="circle-num score-{tier}">{review.get('overall_score', 0)}</span>
                    <span style="font-size:10px;color:#64748b;">/ 100</span>
                </div>
                <span class="priority-badge priority-{tier}" style="font-size:13px;padding:4px 14px;">
                    {review.get('overall_grade', '')}
                </span>
            </div>
            """, unsafe_allow_html=True)

            # Verdict
            if review.get("verdict"):
                st.markdown(f'<div class="verdict-box">{review["verdict"]}</div>', unsafe_allow_html=True)
                st.write("")

            # ATS + Keyword scores
            c1, c2 = st.columns(2)
            c1.metric("ATS Score", f"{review.get('ats_score', 0)}/100")
            c2.metric("Keyword Match", f"{review.get('keyword_match_score', 0)}/100")

            # Score breakdown
            st.markdown('<div class="section-title">Score Breakdown</div>', unsafe_allow_html=True)
            for key, item in (review.get("score_breakdown") or {}).items():
                if isinstance(item, dict):
                    render_breakdown_bar(item.get("label", key), item.get("score", 0), item.get("max", 25))

            # Strengths
            if review.get("strengths"):
                st.markdown('<div class="section-title" style="margin-top:16px;">Strengths</div>', unsafe_allow_html=True)
                for s in review["strengths"]:
                    st.markdown(f'<div style="font-size:13px;color:#c0d0f0;margin-bottom:5px;"><span class="strength-dot"></span>{s}</div>', unsafe_allow_html=True)

            # Improvements
            if review.get("improvements"):
                st.markdown('<div class="section-title" style="margin-top:16px;">Suggested Improvements</div>', unsafe_allow_html=True)
                for imp in sorted(review["improvements"], key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("priority", "medium"), 1)):
                    priority = imp.get("priority", "medium")
                    st.markdown(f"""
                    <div class="improvement-card">
                        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                            <span style="font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;">{imp.get('section','')}</span>
                            <span class="priority-badge priority-{priority}">{priority}</span>
                        </div>
                        <div style="font-size:13px;color:#8a9bc0;margin-bottom:3px;">{imp.get('issue','')}</div>
                        <div style="font-size:13px;color:#c0d0f0;">
                            <span style="color:#3b82f6;font-weight:600;font-size:11px;">Fix →</span> {imp.get('suggestion','')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Missing skills
            if review.get("missing_for_role"):
                st.markdown(f'<div class="section-title" style="margin-top:16px;">Missing for {review.get("_role", "this role")}</div>', unsafe_allow_html=True)
                chips = "".join(f'<span class="missing-chip">{s}</span>' for s in review["missing_for_role"])
                st.markdown(chips, unsafe_allow_html=True)

    st.write("")
    c1, c2 = st.columns([1, 1])
    if c2.button("🏁 End Session & Summary", use_container_width=True):
        st.session_state.page = "summary"
        st.rerun()
    if c1.button("🔄 New Session", use_container_width=True):
        for k in ["session", "current_q_idx", "feedback", "iteration", "resume_review"]:
            st.session_state[k] = None
        st.session_state.page = "input"
        st.rerun()


# ══════════════════════════════════════
#  PAGE: ANSWER + FEEDBACK
# ══════════════════════════════════════
elif st.session_state.page == "answer":
    session = st.session_state.session
    q = session.final_questions[st.session_state.current_q_idx]
    cat = (q.category or "general").lower()

    if st.button("← Back to Questions"):
        st.session_state.page = "questions"
        st.session_state.feedback = None
        st.rerun()

    st.markdown(f'<span class="q-badge {cat}">{cat}</span>', unsafe_allow_html=True)
    st.markdown(f"### {q.text}")

    answer = st.text_area("Your Answer", height=200, placeholder="Type your answer here...", key="user_answer_input")

    btn_label = "Submit Refined Answer" if st.session_state.feedback else "Evaluate Answer"
    if st.button(f"📝 {btn_label}", type="primary", use_container_width=True):
        if not answer.strip():
            st.warning("Please provide an answer first.")
        else:
            st.session_state.iteration += 1
            with st.spinner("Judge agent is evaluating your answer..."):
                from agents.judge import execute as judge_execute
                feedback = judge_execute(
                    q.text, answer, session.role, session.company,
                    st.session_state.iteration,
                )
                st.session_state.feedback = feedback.model_dump()
            st.rerun()

    # Render feedback if available
    if st.session_state.feedback:
        fb = st.session_state.feedback

        st.markdown('<div class="feedback-card">', unsafe_allow_html=True)

        # Score
        tier = score_class(fb["score"], 10)
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:1rem;">
            <div class="score-big score-{tier}">{fb['score']}</div>
            <div class="score-label">out of 10</div>
        </div>
        """, unsafe_allow_html=True)

        # Breakdown
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="section-title">Score Breakdown</div>', unsafe_allow_html=True)
            for label, key in [("Clarity","clarity"),("Depth","depth"),("Relevance","relevance"),("STAR Format","starFormat"),("Role Fit","roleFit")]:
                val = fb["breakdown"].get(key, 0)
                render_breakdown_bar(label, val, 10)

        with col2:
            st.markdown('<div class="section-title">Gaps Identified</div>', unsafe_allow_html=True)
            for g in fb.get("gaps", []):
                st.markdown(f"- {g}")

            st.markdown('<div class="section-title" style="margin-top:12px;">Actionable Tips</div>', unsafe_allow_html=True)
            for t in fb.get("tips", []):
                st.markdown(f"- {t}")

        # Improved answer
        st.markdown('<div class="section-title" style="margin-top:16px;">Improved Answer Example</div>', unsafe_allow_html=True)
        st.info(fb.get("improvedAnswer", ""))

        st.markdown('</div>', unsafe_allow_html=True)

        # Refinement prompt
        if fb["score"] < 7 and st.session_state.iteration < 5:
            st.warning("**Score below 7** — refine your answer above using the feedback and try again.")


# ══════════════════════════════════════
#  PAGE: SUMMARY
# ══════════════════════════════════════
elif st.session_state.page == "summary":
    session = st.session_state.session

    st.markdown('<div class="hero-header"><h1>🎯 Session Complete</h1></div>', unsafe_allow_html=True)

    st.markdown(f"""
    ### Session Summary

    | Detail | Value |
    |--------|-------|
    | **Company** | {session.company} |
    | **Role** | {session.role} |
    | **Questions Generated** | {len(session.final_questions)} |
    """)

    # Category breakdown
    cats = {}
    for q in session.final_questions:
        c = (q.category or "General").title()
        cats[c] = cats.get(c, 0) + 1

    st.markdown("#### Question Breakdown")
    for cat, count in sorted(cats.items()):
        st.markdown(f"- **{cat}**: {count} questions")

    if st.button("🔄 Start New Session", type="primary", use_container_width=True):
        for k in ["session", "current_q_idx", "feedback", "iteration", "resume_review"]:
            st.session_state[k] = None
        st.session_state.page = "input"
        st.rerun()
