# app/main.py
"""
Enhanced Career Assistant frontend.
NO NEW PACKAGES NEEDED — uses only Streamlit + requests + pandas
(all already in your requirements.txt). Visual polish is done with
custom CSS/HTML and Streamlit's built-in bar_chart / line_chart / progress.
No backend/API changes required.
"""

import streamlit as st
import requests
import json
import pandas as pd

# ----------------------------------------------------------------------------
# Page configuration
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Career Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "http://localhost:8000"

# ----------------------------------------------------------------------------
# Custom CSS — gradients, cards, hover animation, badges, donut gauge
# ----------------------------------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background: #f5f6fa;
    }
    .main-header {
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 24px rgba(102,126,234,0.25);
    }
    .main-header h1 { margin: 0; font-size: 2rem; }
    .main-header p { margin: 0.3rem 0 0 0; opacity: 0.9; }

    .kpi-card {
        background: white;
        border-radius: 14px;
        padding: 1.3rem 1rem;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border-top: 4px solid #667eea;
        transition: transform 0.15s ease;
    }
    .kpi-card:hover { transform: translateY(-3px); }
    .kpi-value { font-size: 2rem; font-weight: 800; color: #333; margin: 0.2rem 0; }
    .kpi-label { font-size: 0.85rem; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }

    .job-card {
        background: white;
        border-radius: 16px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border-left: 5px solid #667eea;
        transition: box-shadow 0.15s ease, transform 0.15s ease;
    }
    .job-card:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.10);
        transform: translateY(-2px);
    }
    .job-card h3 { margin: 0 0 0.3rem 0; }

    .score-badge {
        display: inline-block;
        padding: 0.25rem 0.85rem;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.85rem;
        color: white;
    }
    .skill-chip {
        display: inline-block;
        padding: 0.25rem 0.7rem;
        margin: 0.15rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .chip-have { background: #d4edda; color: #1e7e34; }
    .chip-missing { background: #fde2e2; color: #c0392b; }

    .section-title {
        font-size: 1.15rem;
        font-weight: 700;
        margin: 0.5rem 0 0.8rem 0;
        color: #333;
    }

    .donut-wrap { display: flex; flex-direction: column; align-items: center; }
    .donut-center {
        width: 130px; height: 130px; background: white; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.7rem; font-weight: 800; color: #333;
    }

    /* --- 3D-style icon badges (pure CSS, no images/installs) --- */
    .icon3d {
        width: 58px; height: 58px; border-radius: 18px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.7rem; margin: 0 auto 0.6rem auto;
        box-shadow:
            6px 6px 14px rgba(0,0,0,0.18),
            -4px -4px 10px rgba(255,255,255,0.35),
            inset 0 2px 3px rgba(255,255,255,0.55),
            inset 0 -3px 5px rgba(0,0,0,0.15);
        transform: perspective(300px) rotateX(4deg);
    }
    .icon3d-purple { background: linear-gradient(145deg, #8a7cf0, #5f4bd6); }
    .icon3d-blue   { background: linear-gradient(145deg, #6bc4ff, #2e8fd6); }
    .icon3d-green  { background: linear-gradient(145deg, #7fe0a0, #2fae63); }
    .icon3d-orange { background: linear-gradient(145deg, #ffc27a, #f0932b); }
    .icon3d-pink   { background: linear-gradient(145deg, #ff9ac0, #e0507e); }
    .icon3d-teal   { background: linear-gradient(145deg, #7de0d9, #1fa39a); }

    .icon3d-inline {
        width: 46px; height: 46px; border-radius: 14px;
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 1.4rem; vertical-align: middle; margin-right: 0.6rem;
        box-shadow:
            4px 4px 10px rgba(0,0,0,0.18),
            inset 0 2px 3px rgba(255,255,255,0.5),
            inset 0 -2px 4px rgba(0,0,0,0.15);
        transform: perspective(300px) rotateX(4deg);
    }

    .hero-icon {
        width: 90px; height: 90px; border-radius: 26px;
        display: flex; align-items: center; justify-content: center;
        font-size: 2.6rem; float: right; margin-top: -0.5rem;
        background: linear-gradient(145deg, rgba(255,255,255,0.35), rgba(255,255,255,0.1));
        box-shadow:
            8px 8px 18px rgba(0,0,0,0.20),
            inset 0 2px 4px rgba(255,255,255,0.5),
            inset 0 -3px 6px rgba(0,0,0,0.15);
        transform: perspective(300px) rotateX(6deg) rotateY(-6deg);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1f2333 0%, #2b2f42 100%);
    }
    section[data-testid="stSidebar"] * { color: #eee !important; }
    section[data-testid="stSidebar"] .stRadio label { padding: 0.35rem 0; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
for key, default in [
    ('student_id', None),
    ('student_name', None),
    ('selected_job', None),
    ('interview_score_history', []),
    ('interview_questions', None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def score_color(score: float) -> str:
    if score >= 80:
        return "#28a745"
    elif score >= 60:
        return "#f0ad4e"
    return "#dc3545"


def donut_html(pct: float, label: str) -> str:
    color = score_color(pct)
    pct = max(0, min(100, pct))
    return f"""
    <div class="donut-wrap">
        <div style="width:150px;height:150px;border-radius:50%;
                    background:conic-gradient({color} 0% {pct}%, #e9ecef {pct}% 100%);
                    display:flex;align-items:center;justify-content:center;">
            <div class="donut-center">{pct:.0f}%</div>
        </div>
        <div style="margin-top:0.5rem;color:#888;font-size:0.85rem;">{label}</div>
    </div>
    """


# ----------------------------------------------------------------------------
# Cached API calls — avoids re-hitting the backend on every rerun/navigation
# ----------------------------------------------------------------------------
@st.cache_data(ttl=60, show_spinner=False)
def api_get_matches(student_id: int, query: str):
    try:
        resp = requests.get(f"{API_URL}/api/jobs/match/{student_id}", params={"query": query}, timeout=15)
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def api_get_skill_gap(student_id: int, job_id: int):
    try:
        resp = requests.get(f"{API_URL}/api/skill-gap/{student_id}/{job_id}", timeout=15)
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None


def clear_caches():
    api_get_matches.clear()
    api_get_skill_gap.clear()


# ----------------------------------------------------------------------------
# Sidebar / navigation (plain Streamlit — no extra package)
# ----------------------------------------------------------------------------
NAV_OPTIONS = [
    "🏠 Dashboard", "👤 Profile", "📄 Resume Upload",
    "💼 Job Recommendations", "📊 Skill Gap", "✏️ Resume Improvement",
    "📧 Cover Letter", "🎯 Interview Prep"
]

with st.sidebar:
    st.markdown('<div class="icon3d icon3d-purple" style="width:70px;height:70px;font-size:2.2rem;margin:0 auto 0.8rem auto;">🎓</div>', unsafe_allow_html=True)
    st.title("Career Assistant")

    if st.session_state.student_id:
        st.success(f"Welcome, {st.session_state.student_name}!")
        if st.button("🔄 Refresh data"):
            clear_caches()
            st.rerun()
        if st.button("Logout"):
            st.session_state.student_id = None
            st.session_state.student_name = None
            st.rerun()
    else:
        st.info("Please login or register")

    st.divider()

    if st.session_state.student_id:
        selected_page = st.radio("Navigation", NAV_OPTIONS, index=0, label_visibility="collapsed")
    else:
        selected_page = "Registration"

# ----------------------------------------------------------------------------
# Dashboard (home page)
# ----------------------------------------------------------------------------
def render_dashboard():
    st.markdown(
        f'<div class="main-header"><div class="hero-icon">🎓</div>'
        f'<h1>Welcome back, {st.session_state.student_name}</h1>'
        f'<p>Here\'s a quick look at where you stand</p></div>',
        unsafe_allow_html=True
    )

    data = api_get_matches(st.session_state.student_id, "")
    matches = data.get("matches", []) if data else []
    avg_score = round(sum(m.get('match_score', 0) for m in matches) / len(matches), 1) if matches else 0
    top_score = max((m.get('match_score', 0) for m in matches), default=0)

    c1, c2, c3, c4 = st.columns(4)
    kpis = [
        ("💼", "icon3d-purple", "Job Matches", len(matches), c1),
        ("🎯", "icon3d-blue", "Avg Match Score", f"{avg_score}%", c2),
        ("🏆", "icon3d-orange", "Best Match", f"{top_score}%", c3),
        ("🎤", "icon3d-teal", "Interview Attempts", len(st.session_state.interview_score_history), c4),
    ]
    for icon, icon_class, label, value, col in kpis:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="icon3d {icon_class}">{icon}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")
    col_a, col_b = st.columns([2, 1])

    with col_a:
        st.markdown('<div class="section-title"><span class="icon3d-inline icon3d-blue">📈</span>Match Score by Job</div>', unsafe_allow_html=True)
        if matches:
            df = pd.DataFrame([
                {"Job": m.get('job', {}).get('title', 'Unknown')[:22], "Score": m.get('match_score', 0)}
                for m in matches
            ]).set_index("Job")
            st.bar_chart(df, height=320)
        else:
            st.info("Upload your resume and complete your profile to see job matches here.")

    with col_b:
        st.markdown('<div class="section-title"><span class="icon3d-inline icon3d-green">🎯</span>Average Fit</div>', unsafe_allow_html=True)
        st.markdown(donut_html(avg_score, "average match score"), unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="section-title"><span class="icon3d-inline icon3d-pink">⚡</span>Quick Actions</div>', unsafe_allow_html=True)
    q1, q2, q3 = st.columns(3)
    quick_actions = [
        ("📄", "icon3d-purple", "Keep your resume up to date for better matches."),
        ("💼", "icon3d-blue", "Check Job Recommendations for new postings."),
        ("🎯", "icon3d-orange", "Practice interview questions for your top match."),
    ]
    for (icon, icon_class, text), col in zip(quick_actions, [q1, q2, q3]):
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="text-align:left;">
                <div class="icon3d {icon_class}" style="margin:0 0 0.6rem 0;">{icon}</div>
                <div style="color:#555; font-size:0.9rem;">{text}</div>
            </div>
            """, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Registration
# ----------------------------------------------------------------------------
def render_registration():
    st.markdown('<div class="main-header"><h1>🎓 Career Assistant Platform</h1>'
                '<p>Your AI-powered career development companion</p></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Login")
        with st.form("login_form"):
            email = st.text_input("Email")
            submitted = st.form_submit_button("Login")
            if submitted:
                st.session_state.student_id = 1  # demo placeholder — wire up real auth later
                st.session_state.student_name = "Student"
                st.success("Logged in successfully!")
                st.rerun()

    with col2:
        st.subheader("Register")
        with st.form("register_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            submitted = st.form_submit_button("Register")
            if submitted:
                try:
                    response = requests.post(
                        f"{API_URL}/api/students/register",
                        params={"email": email, "name": name}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.student_id = data['id']
                        st.session_state.student_name = data['name']
                        st.success("Registration successful!")
                        st.rerun()
                    else:
                        st.error(f"Registration failed: {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")


# ----------------------------------------------------------------------------
# Job Recommendations
# ----------------------------------------------------------------------------
def render_job_recommendations():
    st.title("💼 Job Recommendations")

    fcol1, fcol2, fcol3 = st.columns([2, 1, 1])
    with fcol1:
        search_query = st.text_input("Search jobs", placeholder="e.g., Data Scientist, Software Engineer...")
    with fcol2:
        min_score = st.slider("Minimum match score", 0, 100, 0)
    with fcol3:
        sort_by = st.selectbox("Sort by", ["Match Score", "Company", "Title"])

    data = api_get_matches(st.session_state.student_id, search_query)
    matches = data.get("matches", []) if data else []
    matches = [m for m in matches if m.get('match_score', 0) >= min_score]

    if sort_by == "Match Score":
        matches.sort(key=lambda m: m.get('match_score', 0), reverse=True)
    elif sort_by == "Company":
        matches.sort(key=lambda m: m.get('job', {}).get('company', ''))
    else:
        matches.sort(key=lambda m: m.get('job', {}).get('title', ''))

    if not matches:
        st.info("No matching jobs found. Try lowering the minimum score or updating your profile.")
        return

    st.success(f"Found {len(matches)} matching jobs")

    df = pd.DataFrame([
        {"Job": m.get('job', {}).get('title', 'Unknown')[:22], "Score": m.get('match_score', 0)}
        for m in matches[:10]
    ]).set_index("Job")
    st.bar_chart(df, height=280)

    for i, match in enumerate(matches):
        job = match.get('job', {})
        score = match.get('match_score', 0)
        color = score_color(score)

        st.markdown(f"""
        <div class="job-card">
            <div style="display:flex; align-items:flex-start; gap:0.9rem;">
                <div class="icon3d icon3d-purple" style="margin:0; flex-shrink:0;">💼</div>
                <div>
                    <h3>{job.get('title', 'Unknown Position')}</h3>
                    <p><strong>🏢 {job.get('company', 'Unknown Company')}</strong>
                    &nbsp;&nbsp;<span class="score-badge" style="background:{color};">{score}% match</span></p>
                    <p><strong>Required Skills:</strong> {', '.join(job.get('required_skills', [])[:5])}</p>
                    <p>{job.get('description', '')[:200]}...</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(min(int(score), 100) / 100)

        with st.expander("💡 Match Details"):
            st.write(f"**Strengths:** {', '.join(match.get('strengths', [])) or '—'}")
            st.write(f"**Areas to Improve:** {', '.join(match.get('weaknesses', [])) or '—'}")
            st.write(f"**Reasoning:** {match.get('reasoning', '—')}")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📊 Skill Gap", key=f"gap_{i}"):
                st.session_state.selected_job = job
                st.toast("Go to Skill Gap Analysis to view results")
        with col2:
            if st.button("📧 Cover Letter", key=f"letter_{i}"):
                st.session_state.selected_job = job
                st.toast("Go to Cover Letter to generate it")
        with col3:
            if st.button("🎯 Interview", key=f"interview_{i}"):
                st.session_state.selected_job = job
                st.toast("Go to Interview Prep to practice")


# ----------------------------------------------------------------------------
# Skill Gap
# ----------------------------------------------------------------------------
def render_skill_gap():
    st.title("📊 Skill Gap Analysis")

    if not st.session_state.selected_job:
        st.info("Select a job from Recommendations to analyze skill gaps")
        return

    job = st.session_state.selected_job
    data = api_get_skill_gap(st.session_state.student_id, job.get('id', 0))
    if not data:
        st.error("Failed to analyze skill gaps")
        return

    st.markdown(f'<div class="section-title"><span class="icon3d-inline icon3d-orange">📊</span>Skill Gap for {job.get("title", "Job")}</div>', unsafe_allow_html=True)

    missing = data.get('missing_skills', [])
    required = job.get('required_skills', [])
    have = [s for s in required if s not in missing]

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(donut_html(
            (len(have) / len(required) * 100) if required else 0,
            "skills you already have"
        ), unsafe_allow_html=True)
        st.metric("Priority", data.get('priority', 'Medium'))

    with col2:
        st.markdown('<div class="section-title"><span class="icon3d-inline icon3d-green">✅</span>Your Skill Coverage</div>', unsafe_allow_html=True)
        chips = "".join(f'<span class="skill-chip chip-have">✅ {s}</span>' for s in have)
        chips += "".join(f'<span class="skill-chip chip-missing">⚠️ {s}</span>' for s in missing)
        st.markdown(chips or "No required skills listed", unsafe_allow_html=True)

    st.write("")
    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="section-title">Missing Skills</div>', unsafe_allow_html=True)
        if missing:
            for skill in missing:
                st.warning(f"⚠️ {skill}")
        else:
            st.success("✅ No missing skills")
    with col4:
        st.markdown('<div class="section-title">Learning Path</div>', unsafe_allow_html=True)
        for i, step in enumerate(data.get('learning_path', []), 1):
            st.info(f"{i}. {step}")


# ----------------------------------------------------------------------------
# Interview Prep
# ----------------------------------------------------------------------------
def render_interview_prep():
    st.title("🎯 Interview Preparation")

    if not st.session_state.selected_job:
        st.info("Select a job from Recommendations to prepare for interviews")
        return

    job = st.session_state.selected_job
    question_types = st.multiselect(
        "Question Types", ["technical", "behavioral", "problem-solving"],
        default=["technical", "behavioral", "problem-solving"]
    )

    if st.button("Generate Questions", type="primary"):
        with st.spinner("Generating interview questions..."):
            try:
                response = requests.post(
                    f"{API_URL}/api/interview/questions",
                    params={"job_id": job.get('id', 0)},
                    json=question_types
                )
                if response.status_code == 200:
                    st.session_state.interview_questions = response.json()
                else:
                    st.error("Failed to generate questions")
            except Exception as e:
                st.error(f"Error: {e}")

    questions_data = st.session_state.interview_questions
    if questions_data:
        tabs = st.tabs(["Technical", "Behavioral", "Problem Solving"])
        keys = ["technical", "behavioral", "problem_solving"]
        for tab, key in zip(tabs, keys):
            with tab:
                for i, q in enumerate(questions_data.get(key, []), 1):
                    with st.expander(f"Question {i}"):
                        st.write(q)
                        answer = st.text_area("Your Answer", key=f"{key}_ans_{i}")
                        if answer and st.button("Get Feedback", key=f"{key}_fb_{i}"):
                            evaluate_answer(q, answer)

    if st.session_state.interview_score_history:
        st.markdown('<div class="section-title"><span class="icon3d-inline icon3d-teal">🎤</span>Your Progress</div>', unsafe_allow_html=True)
        df = pd.DataFrame({
            "Attempt": list(range(1, len(st.session_state.interview_score_history) + 1)),
            "Score": st.session_state.interview_score_history
        }).set_index("Attempt")
        st.line_chart(df, height=280)


def evaluate_answer(question, answer):
    with st.spinner("Evaluating your answer..."):
        try:
            response = requests.post(
                f"{API_URL}/api/interview/evaluate",
                json={"question": question, "answer": answer}
            )
            if response.status_code == 200:
                data = response.json()
                st.session_state.interview_score_history.append(data.get('score', 0))

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Score", f"{data.get('score', 0)}%")
                    st.subheader("Strengths")
                    for s in data.get('strengths', []):
                        st.success(f"✅ {s}")
                with col2:
                    st.subheader("Areas for Improvement")
                    for a in data.get('areas_for_improvement', []):
                        st.warning(f"⚠️ {a}")
                    st.subheader("Suggested Approach")
                    st.info(data.get('suggested_approach', ''))
            else:
                st.error("Failed to evaluate answer")
        except Exception as e:
            st.error(f"Error: {e}")


# ----------------------------------------------------------------------------
# Profile / Resume Upload / Resume Improvement / Cover Letter
# ----------------------------------------------------------------------------
def render_profile():
    st.title("👤 My Profile")
    with st.form("profile_form"):
        st.text_input("Full Name", st.session_state.student_name)
        skills_text = st.text_area("Skills (comma-separated)", placeholder="Python, React, SQL, ...")
        skills = [s.strip() for s in skills_text.split(",") if s.strip()]
        education_json = st.text_area(
            "Education (JSON format)",
            value='[{"degree": "B.S. Computer Science", "institution": "University", "year": "2024"}]'
        )
        interests_text = st.text_area("Interests (comma-separated)", placeholder="AI, Web Development, ...")
        interests = [i.strip() for i in interests_text.split(",") if i.strip()]

        if st.form_submit_button("Update Profile"):
            profile_data = {
                "skills": skills,
                "education": json.loads(education_json) if education_json else [],
                "interests": interests,
                "experience": [],
                "projects": []
            }
            try:
                response = requests.post(
                    f"{API_URL}/api/students/profile",
                    params={"student_id": st.session_state.student_id},
                    json=profile_data
                )
                if response.status_code == 200:
                    clear_caches()
                    st.success("Profile updated successfully!")
                else:
                    st.error("Failed to update profile")
            except Exception as e:
                st.error(f"Error: {e}")


def render_resume_upload():
    st.title("📄 Resume Upload")
    uploaded_file = st.file_uploader("Choose your resume file", type=['pdf', 'docx'])
    if uploaded_file and st.button("Upload and Parse Resume"):
        with st.spinner("Uploading and parsing your resume..."):
            try:
                files = {'file': (uploaded_file.name, uploaded_file, uploaded_file.type)}
                response = requests.post(
                    f"{API_URL}/api/resume/upload",
                    params={"student_id": st.session_state.student_id},
                    files=files
                )
                if response.status_code == 200:
                    clear_caches()
                    data = response.json()
                    st.success("Resume uploaded and parsed successfully!")
                    with st.expander("View Parsed Data"):
                        st.json(data.get('parsed_data', {}))
                else:
                    st.error(f"Upload failed: {response.text}")
            except Exception as e:
                st.error(f"Error: {e}")


def render_resume_improvement():
    st.title("✏️ Resume Improvement")
    if st.button("Get Resume Suggestions"):
        with st.spinner("Analyzing your resume..."):
            try:
                response = requests.post(f"{API_URL}/api/resume/improve/{st.session_state.student_id}")
                if response.status_code == 200:
                    data = response.json()
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Strengths")
                        for s in data.get('strengths', []):
                            st.success(f"✅ {s}")
                        st.subheader("Areas for Improvement")
                        for a in data.get('areas_for_improvement', []):
                            st.warning(f"⚠️ {a}")
                    with col2:
                        st.subheader("Suggestions")
                        for s in data.get('suggestions', []):
                            st.info(f"💡 {s}")
                        st.subheader("Keywords to Add")
                        for k in data.get('keywords_to_add', []):
                            st.code(k)
                else:
                    st.error("Failed to get suggestions")
            except Exception as e:
                st.error(f"Error: {e}")


def render_cover_letter():
    st.title("📧 Cover Letter Generator")
    if not st.session_state.selected_job:
        st.info("Select a job from Recommendations to generate a cover letter")
        return
    style = st.selectbox("Letter Style", ["professional", "enthusiastic", "concise"])
    if st.button("Generate Cover Letter", type="primary"):
        with st.spinner("Writing your cover letter..."):
            try:
                job = st.session_state.selected_job
                response = requests.post(
                    f"{API_URL}/api/cover-letter/generate",
                    params={"student_id": st.session_state.student_id, "job_id": job.get('id', 0), "style": style}
                )
                if response.status_code == 200:
                    letter = response.json().get('cover_letter', '')
                    st.subheader("Your Cover Letter")
                    st.markdown(f'<div class="job-card" style="white-space:pre-wrap;">{letter}</div>',
                                unsafe_allow_html=True)
                    st.download_button("📥 Download", data=letter,
                                        file_name=f"cover_letter_{job.get('title', 'job')}.txt", mime="text/plain")
                else:
                    st.error("Failed to generate cover letter")
            except Exception as e:
                st.error(f"Error: {e}")


# ----------------------------------------------------------------------------
# Router
# ----------------------------------------------------------------------------
def main():
    if not st.session_state.student_id:
        render_registration()
        return

    page_map = {
        "🏠 Dashboard": render_dashboard,
        "👤 Profile": render_profile,
        "📄 Resume Upload": render_resume_upload,
        "💼 Job Recommendations": render_job_recommendations,
        "📊 Skill Gap": render_skill_gap,
        "✏️ Resume Improvement": render_resume_improvement,
        "📧 Cover Letter": render_cover_letter,
        "🎯 Interview Prep": render_interview_prep,
    }
    page_map.get(selected_page, render_dashboard)()


if __name__ == "__main__":
    main()