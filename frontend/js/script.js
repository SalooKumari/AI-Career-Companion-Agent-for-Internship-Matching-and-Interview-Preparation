// ---------------------------------------------------------
// Config
// ---------------------------------------------------------
const API_BASE_URL = "http://127.0.0.1:8000";

// ---------------------------------------------------------
// Auth state (persisted so a page refresh doesn't log you out)
// ---------------------------------------------------------
let authToken = localStorage.getItem("cc_token") || null;
let studentId = localStorage.getItem("cc_student_id") || null;
let studentName = localStorage.getItem("cc_student_name") || "";

// Cache of job_posting_id -> application status, so job cards across
// Dashboard 03/04 can show "Applied" without an extra round trip each time.
let appliedJobIds = new Set();
let savedJobIds = new Set();

// ---------------------------------------------------------
// Elements — auth screen
// ---------------------------------------------------------
const authScreen = document.getElementById("authScreen");
const appShell = document.getElementById("appShell");

const tabLogin = document.getElementById("tabLogin");
const tabRegister = document.getElementById("tabRegister");
const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const loginFeedback = document.getElementById("loginFeedback");
const registerFeedback = document.getElementById("registerFeedback");

const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");

// ---------------------------------------------------------
// Elements — app shell
// ---------------------------------------------------------
const sidebarAvatar = document.getElementById("sidebarAvatar");
const sidebarUserName = document.getElementById("sidebarUserName");
const logoutBtn = document.getElementById("logoutBtn");
const navItems = document.querySelectorAll(".nav-item");
const dashboardViews = document.querySelectorAll(".dashboard-view");

// ---------------------------------------------------------
// API helper
// ---------------------------------------------------------
async function apiFetch(path, options = {}) {
  const headers = options.headers || {};
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    logout("Your session expired — please log in again.");
    throw new Error("Session expired.");
  }

  const isJson = res.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await res.json() : null;

  if (!res.ok) {
    throw new Error((data && data.detail) || `Request failed (${res.status})`);
  }
  return data;
}

// ---------------------------------------------------------
// Backend health check
// ---------------------------------------------------------
async function checkBackendStatus() {
  try {
    const res = await fetch(`${API_BASE_URL}/`);
    if (!res.ok) throw new Error("bad response");
    statusDot.classList.add("online");
    statusText.textContent = "backend connected";
  } catch (err) {
    statusDot.classList.add("offline");
    statusText.textContent = "backend not reachable — is uvicorn running?";
  }
}
checkBackendStatus();

// ---------------------------------------------------------
// Auth: tabs
// ---------------------------------------------------------
tabLogin.addEventListener("click", () => setAuthTab("login"));
tabRegister.addEventListener("click", () => setAuthTab("register"));

function setAuthTab(which) {
  const isLogin = which === "login";
  loginForm.hidden = !isLogin;
  registerForm.hidden = isLogin;

  document.getElementById("switchLoginText").hidden = !isLogin;
  document.getElementById("switchRegisterText").hidden = isLogin;

  document.getElementById("authEyebrowSmall").textContent = isLogin ? "Welcome back" : "Get started";
  document.getElementById("authTitle").textContent = isLogin ? "Sign in to your account" : "Create your account";
  document.getElementById("authSubtitleText").textContent = isLogin
    ? "Enter your credentials to continue to Intence Find."
    : "Set up your profile to start finding better-matched internships.";
}

document.querySelectorAll(".eye-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const input = document.getElementById(btn.dataset.target);
    const showing = input.type === "text";
    input.type = showing ? "password" : "text";
    btn.textContent = showing ? "👁" : "🙈";
  });
});

// ---------------------------------------------------------
// Auth: register
// ---------------------------------------------------------
registerForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  setFeedback(registerFeedback, "Creating your account…", "");

  const payload = {
    full_name: document.getElementById("registerName").value.trim(),
    email: document.getElementById("registerEmail").value.trim(),
    password: document.getElementById("registerPassword").value,
  };

  try {
    const data = await apiFetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    onAuthSuccess(data);
  } catch (err) {
    setFeedback(registerFeedback, err.message, "error");
  }
});

// ---------------------------------------------------------
// Auth: login
// ---------------------------------------------------------
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  setFeedback(loginFeedback, "Logging in…", "");

  const payload = {
    email: document.getElementById("loginEmail").value.trim(),
    password: document.getElementById("loginPassword").value,
  };

  try {
    const data = await apiFetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    onAuthSuccess(data);
  } catch (err) {
    setFeedback(loginFeedback, err.message, "error");
  }
});

function onAuthSuccess(data) {
  authToken = data.access_token;
  studentId = data.student_id;
  studentName = data.full_name;

  localStorage.setItem("cc_token", authToken);
  localStorage.setItem("cc_student_id", studentId);
  localStorage.setItem("cc_student_name", studentName);

  enterApp();
}

function logout(message) {
  authToken = null;
  studentId = null;
  studentName = "";
  localStorage.removeItem("cc_token");
  localStorage.removeItem("cc_student_id");
  localStorage.removeItem("cc_student_name");

  appShell.hidden = true;
  authScreen.hidden = false;
  loginForm.reset();
  registerForm.reset();
  setAuthTab("login");
  if (message) setFeedback(loginFeedback, message, "error");
}

logoutBtn.addEventListener("click", () => logout());

// ---------------------------------------------------------
// Entering the app (after login/register, or on page load with a saved token)
// ---------------------------------------------------------
async function enterApp(viewName = "profile") {
  authScreen.hidden = true;
  appShell.hidden = false;

  sidebarUserName.textContent = studentName;
  sidebarAvatar.textContent = studentName ? studentName[0].toUpperCase() : "?";

  switchView(viewName);
}

// If a token is already saved (page refresh), try to resume the session.
(async function tryResumeSession() {
  if (!authToken || !studentId) return;
  try {
    const me = await apiFetch("/auth/me");
    studentName = me.full_name;
    localStorage.setItem("cc_student_name", studentName);
    const savedView = sessionStorage.getItem("cc_active_view");
    const viewName = [...navItems].some((btn) => btn.dataset.view === savedView)
      ? savedView
      : "profile";
    enterApp(viewName);
  } catch {
    // apiFetch already calls logout() on a 401
  }
})();

// ---------------------------------------------------------
// Sidebar navigation
// ---------------------------------------------------------
navItems.forEach((btn) => {
  btn.addEventListener("click", () => switchView(btn.dataset.view));
});

function switchView(viewName) {
  sessionStorage.setItem("cc_active_view", viewName);
  navItems.forEach((btn) => btn.classList.toggle("active", btn.dataset.view === viewName));
  dashboardViews.forEach((section) => {
    section.hidden = section.id !== `view-${viewName}`;
  });

  if (viewName === "profile") loadProfileView();
  if (viewName === "matches") loadMatchesView();
  if (viewName === "applications") loadApplicationsView();
  if (viewName === "interview") loadInterviewStartView();
  if (viewName === "interview-history") loadInterviewHistoryView();
  if (viewName === "toolkit") loadToolkitView();
  if (viewName === "chat") loadChatView();
}

// ---------------------------------------------------------
// DASHBOARD 01 — Student Profile
// ---------------------------------------------------------
const photoPreview = document.getElementById("photoPreview");
const photoInput = document.getElementById("photoInput");
const profileForm = document.getElementById("profileForm");
const profileFeedback = document.getElementById("profileFeedback");
const profileName = document.getElementById("profileName");
const profileEmail = document.getElementById("profileEmail");
const profilePhone = document.getElementById("profilePhone");
const skillsEditor = document.getElementById("skillsEditor");
const newSkillInput = document.getElementById("newSkillInput");
const educationList = document.getElementById("educationList");
const experienceList = document.getElementById("experienceList");
const projectsList = document.getElementById("projectsList");

let currentSkills = []; // [{name, category, proficiency}]

async function loadProfileView() {
  try {
    const profile = await apiFetch(`/students/${studentId}/profile`);
    renderProfile(profile);
  } catch (err) {
    setFeedback(profileFeedback, err.message, "error");
  }
}

function renderProfile(profile) {
  const s = profile.student;
  profileName.value = s.full_name || "";
  profileEmail.value = s.email || "";
  profilePhone.value = s.phone || "";

  if (s.photo_path) {
    const url = photoUrl(s.photo_path);
    photoPreview.style.backgroundImage = `url(${url})`;
    photoPreview.textContent = "";
    sidebarAvatar.style.backgroundImage = `url(${url})`;
    sidebarAvatar.textContent = "";
  } else {
    photoPreview.style.backgroundImage = "";
    photoPreview.textContent = s.full_name ? s.full_name[0].toUpperCase() : "?";
  }

  currentSkills = (profile.skills || []).map((s) => ({ name: s.name, category: s.category, proficiency: s.proficiency }));
  renderSkillsEditor();

  renderEntryList(educationList, profile.education, (ed) => ({
    title: `${ed.degree || "Degree"}${ed.field_of_study ? " · " + ed.field_of_study : ""}`,
    sub: `${ed.institution}${formatDateRange(ed.start_date, ed.end_date)}${ed.grade ? " · " + ed.grade : ""}`,
    desc: "",
  }));
  renderEntryList(experienceList, profile.experience, (exp) => ({
    title: exp.title,
    sub: `${exp.organization || ""}${formatDateRange(exp.start_date, exp.end_date)}`,
    desc: exp.description || "",
  }));
  renderEntryList(projectsList, profile.projects, (p) => ({
    title: p.title,
    sub: p.tech_stack || "",
    desc: [p.description, p.link].filter(Boolean).join(" — "),
  }));
}

profileForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  setFeedback(profileFeedback, "Saving…", "");
  try {
    await apiFetch(`/students/${studentId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        full_name: profileName.value.trim(),
        phone: profilePhone.value.trim() || null,
      }),
    });
    studentName = profileName.value.trim();
    localStorage.setItem("cc_student_name", studentName);
    sidebarUserName.textContent = studentName;
    setFeedback(profileFeedback, "Profile updated.", "success");
  } catch (err) {
    setFeedback(profileFeedback, err.message, "error");
  }
});

photoInput.addEventListener("change", async () => {
  const file = photoInput.files[0];
  if (!file) return;
 
  const formData = new FormData();
  formData.append("file", file);
 
  setFeedback(profileFeedback, "Uploading photo…", "");
  try {
    const student = await apiFetch(`/students/${studentId}/photo`, {
      method: "POST",
      body: formData,
    });
    const url = photoUrl(student.photo_path);
    photoPreview.style.backgroundImage = `url(${url})`;
    photoPreview.textContent = "";
    sidebarAvatar.style.backgroundImage = `url(${url})`;
    sidebarAvatar.textContent = "";
    setFeedback(profileFeedback, "Photo updated.", "success");
  } catch (err) {
    setFeedback(profileFeedback, err.message, "error");
  }
});

function renderSkillsEditor() {
  skillsEditor.innerHTML = "";
  if (currentSkills.length === 0) {
    skillsEditor.innerHTML = `<p class="empty-note">No skills yet — add one below, or parse a resume.</p>`;
    return;
  }
  currentSkills.forEach((skill, idx) => {
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.innerHTML = `${escapeHtml(skill.name)} <button type="button" data-idx="${idx}" aria-label="Remove">×</button>`;
    tag.querySelector("button").addEventListener("click", () => removeSkill(idx));
    skillsEditor.appendChild(tag);
  });
}

newSkillInput.addEventListener("keypress", (e) => {
  if (e.key !== "Enter") return;
  e.preventDefault();
  const value = newSkillInput.value.trim();
  if (!value) return;
  currentSkills.push({ name: value, category: null, proficiency: null });
  newSkillInput.value = "";
  renderSkillsEditor();
  saveSkills();
});

async function removeSkill(idx) {
  currentSkills.splice(idx, 1);
  renderSkillsEditor();
  saveSkills();
}

async function saveSkills() {
  try {
    await apiFetch(`/students/${studentId}/skills`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ skills: currentSkills }),
    });
  } catch (err) {
    setFeedback(profileFeedback, err.message, "error");
  }
}

// ---------------------------------------------------------
// DASHBOARD 02 — Upload Resume & Parse
// ---------------------------------------------------------
const resumeForm = document.getElementById("resumeForm");
const resumeFeedback = document.getElementById("resumeFeedback");
const resumeFileInput = document.getElementById("resumeFile");
const fileLabel = document.getElementById("fileLabel");
const parseBtn = document.getElementById("parseBtn");
const parseFeedback = document.getElementById("parseFeedback");
const resumeUploadedKey = () => `cc_resume_uploaded_${studentId}`;
parseBtn.disabled = sessionStorage.getItem(resumeUploadedKey()) !== "true";

const MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB
const ALLOWED_RESUME_EXTENSIONS = [".pdf", ".docx", ".txt"];

function isAllowedResumeFile(file) {
  const filename = file.name.toLowerCase();
  return ALLOWED_RESUME_EXTENSIONS.some((extension) => filename.endsWith(extension));
}

resumeFileInput.addEventListener("change", () => {
  const file = resumeFileInput.files[0];
  fileLabel.textContent = file ? file.name : "Choose a resume file…";

  if (!file) return;

  if (!isAllowedResumeFile(file)) {
    setFeedback(resumeFeedback, "Only PDF, DOCX, or TXT files are accepted.", "error");
    resumeFileInput.value = "";
    fileLabel.textContent = "Choose a resume file…";
    return;
  }
  if (file.size > MAX_RESUME_SIZE_BYTES) {
    setFeedback(resumeFeedback, "Resume is larger than 5 MB.", "error");
    resumeFileInput.value = "";
    fileLabel.textContent = "Choose a resume file…";
    return;
  }
  setFeedback(resumeFeedback, "", "");
});

resumeForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = resumeFileInput.files[0];
  if (!file) {
    setFeedback(resumeFeedback, "Choose a file first.", "error");
    return;
  }
  if (!isAllowedResumeFile(file)) {
    setFeedback(resumeFeedback, "Only PDF, DOCX, or TXT files are accepted.", "error");
    return;
  }
  if (file.size > MAX_RESUME_SIZE_BYTES) {
    setFeedback(resumeFeedback, "Resume is larger than 5 MB.", "error");
    return;
  }

  setFeedback(resumeFeedback, "Uploading…", "");
  const formData = new FormData();
  formData.append("file", file);

  try {
    const data = await apiFetch(`/students/${studentId}/resume`, {
      method: "POST",
      body: formData,
    });
    setFeedback(resumeFeedback, `Uploaded "${data.file_name}". Ready to parse.`, "success");
    sessionStorage.setItem(resumeUploadedKey(), "true");
    parseBtn.disabled = false;
  } catch (err) {
    setFeedback(resumeFeedback, err.message, "error");
  }
});

parseBtn.addEventListener("click", async () => {
  parseBtn.disabled = true;
  setFeedback(parseFeedback, "Parsing resume and extracting structured data — this can take a few seconds…", "");

  try {
    const profile = await apiFetch(`/students/${studentId}/resume/parse`, { method: "POST" });
    setFeedback(parseFeedback, "Done — see your updated profile on Dashboard 01.", "success");
    renderProfile(profile); // keeps Dashboard 01 in sync even if the user hasn't clicked over yet
  } catch (err) {
    setFeedback(parseFeedback, err.message, "error");
  } finally {
    parseBtn.disabled = false;
  }
});

// ---------------------------------------------------------
// DASHBOARD 03 — Find Matching Internships
// ---------------------------------------------------------
const jobSearchInput = document.getElementById("jobSearchInput");
const jobSearchBtn = document.getElementById("jobSearchBtn");
const searchFeedback = document.getElementById("searchFeedback");
const searchResults = document.getElementById("searchResults");

const findMatchesBtn = document.getElementById("findMatchesBtn");
const matchesFeedback = document.getElementById("matchesFeedback");
const matchResults = document.getElementById("matchResults");

async function loadMatchesView() {
  try {
    appliedJobIds = await fetchAppliedJobIds();
  } catch {
    // non-fatal — Apply buttons just won't pre-disable
  }

  try {
    savedJobIds = await fetchSavedJobIds();
  } catch {
    // non-fatal — Save buttons just won't pre-fill
  }

  try {
    const matches = await apiFetch(`/students/${studentId}/matches`);
    if (matches.length) renderJobCards(matchResults, matches, { showScore: true });
  } catch {
    // no matches computed yet — leave empty, user clicks "Find my matches"
  }
}

jobSearchBtn.addEventListener("click", runJobSearch);
jobSearchInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") { e.preventDefault(); runJobSearch(); }
});

async function runJobSearch() {
  const q = jobSearchInput.value.trim();
  if (!q) return;

  setFeedback(searchFeedback, "Searching…", "");
  try {
    const results = await apiFetch(`/jobs/search?q=${encodeURIComponent(q)}&top_k=10`);
    setFeedback(searchFeedback, `${results.length} result(s).`, "success");
    renderJobCards(searchResults, results.map((r) => ({ job: r.job, similarity: r.similarity })), { showScore: false });
  } catch (err) {
    setFeedback(searchFeedback, err.message, "error");
  }
}

findMatchesBtn.addEventListener("click", async () => {
  findMatchesBtn.disabled = true;
  setFeedback(matchesFeedback, "Retrieving candidate roles and scoring each one against your profile — this can take up to a minute…", "");

  try {
    const matches = await apiFetch(`/students/${studentId}/matches?top_k=8`, { method: "POST" });
    setFeedback(matchesFeedback, `Ranked ${matches.length} internship(s).`, "success");
    renderJobCards(matchResults, matches, { showScore: true });
  } catch (err) {
    setFeedback(matchesFeedback, err.message, "error");
  } finally {
    findMatchesBtn.disabled = false;
  }
});

// ---------------------------------------------------------
// DASHBOARD 04 — Applied Internships
// ---------------------------------------------------------
const applicationsCount = document.getElementById("applicationsCount");
const applicationsList = document.getElementById("applicationsList");
const applicationsSearchInput = document.getElementById("applicationsSearchInput");
const applicationsSortSelect = document.getElementById("applicationsSortSelect");
const applicationsStatsRow = document.getElementById("applicationsStatsRow");

let currentStatusFilter = "";
let searchDebounceTimer = null;

async function loadApplicationsView() {
  await loadApplicationsStats();
  await loadApplicationsList();
}

async function loadApplicationsStats() {
  try {
    const stats = await apiFetch(`/students/${studentId}/applications/stats`);
    applicationsStatsRow.innerHTML = `
      <div class="stat-chip"><span class="stat-chip-value">${stats.total}</span><span class="stat-chip-label">Total</span></div>
      <div class="stat-chip"><span class="stat-chip-value">${stats.active}</span><span class="stat-chip-label">Active</span></div>
      <div class="stat-chip"><span class="stat-chip-value">${stats.upcoming_deadlines}</span><span class="stat-chip-label">Upcoming deadlines</span></div>
      <div class="stat-chip"><span class="stat-chip-value">${stats.interviews_scheduled}</span><span class="stat-chip-label">Interviews scheduled</span></div>
      <div class="stat-chip"><span class="stat-chip-value">${stats.offers_received}</span><span class="stat-chip-label">Offers received</span></div>
      <div class="stat-chip"><span class="stat-chip-value">${stats.rejected}</span><span class="stat-chip-label">Rejected</span></div>
    `;
  } catch {
    applicationsStatsRow.innerHTML = "";
  }
}

async function loadApplicationsList() {
  try {
    const params = new URLSearchParams();
    if (currentStatusFilter) params.set("status", currentStatusFilter);
    if (applicationsSearchInput.value.trim()) params.set("search", applicationsSearchInput.value.trim());
    params.set("sort_by", applicationsSortSelect.value);

    const applications = await apiFetch(`/students/${studentId}/applications?${params.toString()}`);

    applicationsCount.textContent = applications.length
      ? `${applications.length} internship${applications.length === 1 ? "" : "s"}${currentStatusFilter ? ` (filtered: ${currentStatusFilter.replace(/_/g, " ")})` : ""}.`
      : currentStatusFilter || applicationsSearchInput.value.trim()
        ? "No applications match this filter/search."
        : "You haven't applied to any internships yet — find some on Dashboard 03.";

    applicationsList.innerHTML = "";
    applications.forEach((app) => {
      applicationsList.appendChild(buildApplicationCard(app));
    });
  } catch (err) {
    applicationsCount.textContent = err.message;
  }
}

document.querySelectorAll("[data-status-filter]").forEach((btn) => {
  btn.addEventListener("click", () => {
    currentStatusFilter = btn.dataset.statusFilter;
    document.querySelectorAll("[data-status-filter]").forEach((b) => b.classList.toggle("active", b === btn));
    loadApplicationsList();
  });
});

applicationsSearchInput.addEventListener("input", () => {
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(loadApplicationsList, 350);
});

applicationsSortSelect.addEventListener("change", loadApplicationsList);

const APPLICATION_STATUS_LABELS = {
  applied: "Applied",
  under_review: "Under Review",
  shortlisted: "Shortlisted",
  interview_scheduled: "Interview Scheduled",
  interview_completed: "Interview Completed",
  offer_received: "Offer Received",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
};

function buildApplicationCard(app) {
  const card = document.createElement("div");
  card.className = "job-card";
  const job = app.job;

  const statusOptions = Object.keys(APPLICATION_STATUS_LABELS)
    .map((s) => `<option value="${s}" ${s === app.status ? "selected" : ""}>${APPLICATION_STATUS_LABELS[s]}</option>`)
    .join("");

  card.innerHTML = `
    <div class="job-card-top">
      <div>
        <div class="job-card-title">${escapeHtml(job.title)}</div>
        <div class="job-card-sub">${escapeHtml(job.company)} · ${escapeHtml(job.location)}</div>
      </div>
      <div style="display:flex; align-items:flex-start; gap:12px;">
        ${job.source && job.source !== "synthetic" ? `<span class="job-card-real-badge">Real posting ✓</span>` : ""}
        <span class="status-pill ${app.status}">${APPLICATION_STATUS_LABELS[app.status] || app.status}</span>
      </div>
    </div>
    <p class="job-card-reasoning">Applied ${formatDate(app.applied_at)}${job.application_url ? ` · <a href="${escapeHtml(job.application_url)}" target="_blank" rel="noopener noreferrer">View real posting ↗</a>` : ""}</p>
    <div class="job-card-footer" style="flex-wrap: wrap;">
      <label class="deadline-row">
        Status:
        <select class="status-select" data-app-id="${app.id}">${statusOptions}</select>
      </label>
      <label class="deadline-row">
        Deadline reminder:
        <input type="date" data-app-deadline-id="${app.id}" value="${app.deadline || ""}" />
      </label>
      <label class="deadline-row">
        Interview date:
        <input type="date" data-app-interview-id="${app.id}" value="${app.interview_date || ""}" />
      </label>
    </div>
    <div class="application-notes-row">
      <textarea class="notes-textarea" data-app-notes-id="${app.id}" placeholder="Notes — recruiter contact, referral, follow-up reminders…">${escapeHtml(app.notes || "")}</textarea>
    </div>
    <div class="application-materials-row" id="materials-${app.id}"></div>
    <p class="feedback" id="app-feedback-${app.id}"></p>
  `;

  const feedbackEl = card.querySelector(`#app-feedback-${app.id}`);

  card.querySelector("[data-app-id]").addEventListener("change", async (e) => {
    try {
      await apiFetch(`/students/${studentId}/applications/${app.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: e.target.value }),
      });
      app.status = e.target.value;
      card.querySelector(".status-pill").textContent = APPLICATION_STATUS_LABELS[e.target.value] || e.target.value;
      card.querySelector(".status-pill").className = `status-pill ${e.target.value}`;
      setFeedback(feedbackEl, "Saved.", "success");
      loadApplicationsStats();
    } catch (err) {
      setFeedback(feedbackEl, err.message, "error");
    }
  });

  card.querySelector("[data-app-deadline-id]").addEventListener("change", async (e) => {
    try {
      await apiFetch(`/students/${studentId}/applications/${app.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ deadline: e.target.value || null }),
      });
      setFeedback(feedbackEl, "Saved.", "success");
      loadApplicationsStats();
    } catch (err) {
      setFeedback(feedbackEl, err.message, "error");
    }
  });

  card.querySelector("[data-app-interview-id]").addEventListener("change", async (e) => {
    try {
      await apiFetch(`/students/${studentId}/applications/${app.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interview_date: e.target.value || null }),
      });
      setFeedback(feedbackEl, "Saved.", "success");
      loadApplicationsStats();
    } catch (err) {
      setFeedback(feedbackEl, err.message, "error");
    }
  });

  const notesTextarea = card.querySelector("[data-app-notes-id]");
  let notesDebounce = null;
  notesTextarea.addEventListener("input", () => {
    clearTimeout(notesDebounce);
    notesDebounce = setTimeout(async () => {
      try {
        await apiFetch(`/students/${studentId}/applications/${app.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ notes: notesTextarea.value }),
        });
        setFeedback(feedbackEl, "Notes saved.", "success");
      } catch (err) {
        setFeedback(feedbackEl, err.message, "error");
      }
    }, 600);
  });

  loadApplicationMaterialsLink(app, card.querySelector(`#materials-${app.id}`));

  return card;
}

async function loadApplicationMaterialsLink(app, container) {
  try {
    const material = await apiFetch(`/students/${studentId}/materials/${app.job.id}`);
    if (material.resume_content || material.cover_letter_content) {
      container.innerHTML = `<button class="btn-secondary view-materials-btn" type="button">📄 View generated resume/cover letter</button>`;
      container.querySelector(".view-materials-btn").addEventListener("click", () => {
        switchView("toolkit");
        setTimeout(() => {
          if (toolkitJobSelect) {
            toolkitJobSelect.value = String(app.job.id);
            toolkitJobSelect.dispatchEvent(new Event("change"));
          }
        }, 300);
      });
    }
  } catch {
    // no materials generated yet for this job — leave the row empty
  }
}

// ---------------------------------------------------------
// Job card rendering (shared by search / matches / applications)
// ---------------------------------------------------------
async function fetchAppliedJobIds() {
  const applications = await apiFetch(`/students/${studentId}/applications`);
  return new Set(applications.map((a) => a.job.id));
}

async function fetchSavedJobIds() {
  const saved = await apiFetch(`/students/${studentId}/saved-jobs`);
  return new Set(saved.map((s) => s.job.id));
}

function renderJobCards(container, items, { showScore }) {
  container.innerHTML = "";
  if (!items.length) {
    container.innerHTML = `<p class="empty-note">No results yet.</p>`;
    return;
  }
  items.forEach((item) => {
    container.appendChild(buildJobCard(item.job, {
      showApply: true,
      showSave: true,
      score: showScore ? item.score : null,
      similarity: !showScore ? item.similarity : null,
      reasoning: item.reasoning || null,
      matchedSkills: item.matched_skills || [],
      missingSkills: item.missing_skills || [],
      scoreBreakdown: showScore ? {
        skills_score: item.skills_score,
        education_score: item.education_score,
        project_score: item.project_score,
        domain_fit_score: item.domain_fit_score,
      } : null,
    }));
  });
}

function buildJobCard(job, opts) {
  const card = document.createElement("div");
  card.className = "job-card";

  const alreadyApplied = appliedJobIds.has(job.id);
  const alreadySaved = savedJobIds.has(job.id);

  const scoreHtml = opts.score != null
    ? `<div class="job-card-score">${opts.score}<span>match score</span></div>`
    : opts.similarity != null
      ? `<div class="job-card-score">${(opts.similarity * 100).toFixed(0)}%<span>similarity</span></div>`
      : "";

  const breakdown = opts.scoreBreakdown;
  const hasBreakdown = breakdown && [breakdown.skills_score, breakdown.education_score, breakdown.project_score, breakdown.domain_fit_score].some((v) => v != null);
  const breakdownHtml = hasBreakdown
    ? `<div class="score-breakdown">
        ${breakdown.skills_score != null ? `<span class="score-chip">Skills ${breakdown.skills_score}</span>` : ""}
        ${breakdown.education_score != null ? `<span class="score-chip">Education ${breakdown.education_score}</span>` : ""}
        ${breakdown.project_score != null ? `<span class="score-chip">Projects ${breakdown.project_score}</span>` : ""}
        ${breakdown.domain_fit_score != null ? `<span class="score-chip">Domain fit ${breakdown.domain_fit_score}</span>` : ""}
      </div>`
    : "";

  const reasoningHtml = opts.reasoning
    ? `<p class="job-card-reasoning"><strong>Why this matches:</strong> ${escapeHtml(opts.reasoning)}</p>`
    : "";

  const skillsHtml = (opts.matchedSkills && opts.matchedSkills.length) || (opts.missingSkills && opts.missingSkills.length)
    ? `<div class="job-card-skills">
        ${(opts.matchedSkills || []).map((s) => `<span class="skill-chip matched">✓ ${escapeHtml(s)}</span>`).join("")}
        ${(opts.missingSkills || []).map((s) => `<span class="skill-chip missing">missing: ${escapeHtml(s)}</span>`).join("")}
      </div>`
    : "";

  const saveBtnHtml = opts.showSave
    ? `<button class="btn-secondary save-btn ${alreadySaved ? "saved" : ""}" data-save-job-id="${job.id}" type="button" aria-label="${alreadySaved ? "Unsave" : "Save"}">
        ${alreadySaved ? "🔖 Saved" : "🔖 Save"}
      </button>`
    : "";

  const footerHtml = opts.showApply
    ? `<div class="job-card-footer">
        <span class="job-card-status ${alreadyApplied ? "applied" : ""}">${alreadyApplied ? "Applied ✓" : ""}</span>
        <div class="job-card-footer-actions">
          ${saveBtnHtml}
          ${job.application_url
            ? `<a class="btn-secondary job-card-view-link" href="${escapeHtml(job.application_url)}" target="_blank" rel="noopener noreferrer">View real posting ↗</a>`
            : ""}
          <button class="btn-secondary" ${alreadyApplied ? "disabled" : ""} data-job-id="${job.id}" data-apply-url="${job.application_url ? escapeHtml(job.application_url) : ""}">
            ${alreadyApplied ? "Already applied" : job.application_url ? "Apply on company site →" : "Apply"}
          </button>
        </div>
      </div>`
    : opts.statusLabel
      ? `<div class="job-card-footer">
          <span class="job-card-status applied">${escapeHtml(opts.statusLabel)}</span>
          <div class="job-card-footer-actions">
            ${saveBtnHtml}
            ${job.application_url ? `<a class="btn-secondary job-card-view-link" href="${escapeHtml(job.application_url)}" target="_blank" rel="noopener noreferrer">View real posting ↗</a>` : ""}
          </div>
        </div>`
      : "";

  card.innerHTML = `
    <div class="job-card-top">
      <div>
        <div class="job-card-title">${escapeHtml(job.title)}</div>
        <div class="job-card-sub">${escapeHtml(job.company)} · ${escapeHtml(job.location)}</div>
      </div>
      <div style="display:flex; align-items:flex-start; gap:12px;">
        ${job.source && job.source !== "synthetic" ? `<span class="job-card-real-badge">Real posting ✓</span>` : ""}
        ${job.domain ? `<span class="job-card-domain">${escapeHtml(job.domain)}</span>` : ""}
        ${scoreHtml}
      </div>
    </div>
    ${breakdownHtml}
    ${reasoningHtml}
    ${skillsHtml}
    ${footerHtml}
  `;

  const applyBtn = card.querySelector("[data-job-id]");
  if (applyBtn) {
    applyBtn.addEventListener("click", () => applyToJob(job.id, card, applyBtn.dataset.applyUrl || null));
  }

  const saveBtn = card.querySelector("[data-save-job-id]");
  if (saveBtn) {
    saveBtn.addEventListener("click", () => toggleSaveJob(job.id, saveBtn));
  }

  return card;
}

async function toggleSaveJob(jobPostingId, btn) {
  btn.disabled = true;
  const isSaved = savedJobIds.has(jobPostingId);
  try {
    if (isSaved) {
      await apiFetch(`/students/${studentId}/saved-jobs/${jobPostingId}`, { method: "DELETE" });
      savedJobIds.delete(jobPostingId);
      btn.classList.remove("saved");
      btn.textContent = "🔖 Save";
    } else {
      await apiFetch(`/students/${studentId}/saved-jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_posting_id: jobPostingId }),
      });
      savedJobIds.add(jobPostingId);
      btn.classList.add("saved");
      btn.textContent = "🔖 Saved";
    }
  } catch {
    // leave the button as-is on failure — safe to just retry
  } finally {
    btn.disabled = false;
  }
}

async function applyToJob(jobPostingId, card, applicationUrl) {
  const btn = card.querySelector("[data-job-id]");
  const statusEl = card.querySelector(".job-card-status");

  // Real posting: open it in a new tab so the student can actually apply
  // there. We still record the application internally right after, so it
  // shows up in "Applied Internships" either way.
  if (applicationUrl) {
    window.open(applicationUrl, "_blank", "noopener,noreferrer");
  }

  btn.disabled = true;
  btn.textContent = "Applying…";
  try {
    await apiFetch(`/students/${studentId}/applications`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_posting_id: jobPostingId }),
    });
    appliedJobIds.add(jobPostingId);
    btn.textContent = "Already applied";
    if (statusEl) {
      statusEl.textContent = "Applied ✓";
      statusEl.classList.add("applied");
    }
  } catch (err) {
    btn.disabled = false;
    btn.textContent = applicationUrl ? "Apply on company site →" : "Apply";
    if (statusEl) {
      statusEl.textContent = err.message;
      statusEl.classList.add("error-text");
    }
  }
}

// ---------------------------------------------------------
// DASHBOARD 05 — AI Chat Bot (Mock Interview)
// ---------------------------------------------------------
const interviewJobSelect = document.getElementById("interviewJobSelect");
const interviewDomainSelect = document.getElementById("interviewDomainSelect");
const startInterviewBtn = document.getElementById("startInterviewBtn");
const interviewStartFeedback = document.getElementById("interviewStartFeedback");
const interviewStart = document.getElementById("interviewStart");
const interviewRoom = document.getElementById("interviewRoom");
const chatLog = document.getElementById("chatLog");
const interviewProgressText = document.getElementById("interviewProgressText");
const progressFill = document.getElementById("progressFill");
const micBtn = document.getElementById("micBtn");
const micHint = document.getElementById("micHint");
const answerText = document.getElementById("answerText");
const skipQuestionBtn = document.getElementById("skipQuestionBtn");
const nextQuestionBtn = document.getElementById("nextQuestionBtn");
const submitInterviewBtn = document.getElementById("submitInterviewBtn");
const interviewRoomFeedback = document.getElementById("interviewRoomFeedback");
const interviewFeedbackPanel = document.getElementById("interviewFeedbackPanel");
const feedbackScore = document.getElementById("feedbackScore");
const feedbackStrengths = document.getElementById("feedbackStrengths");
const feedbackImprovements = document.getElementById("feedbackImprovements");
const feedbackRecommendations = document.getElementById("feedbackRecommendations");
const startAnotherBtn = document.getElementById("startAnotherBtn");

let currentInterview = null; // full InterviewSetOut from the backend
let currentQuestionPos = 0; // 0-indexed position into currentInterview.questions
let domainsLoaded = false;

// --- Web Speech API setup (best-effort — Chrome-based browsers only) ---
const SpeechRecognitionImpl = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognizer = null;
let isRecording = false;

if (SpeechRecognitionImpl) {
  recognizer = new SpeechRecognitionImpl();
  recognizer.continuous = true;
  recognizer.interimResults = true;
  recognizer.lang = "en-US";

  recognizer.addEventListener("result", (event) => {
    let transcript = "";
    for (let i = 0; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }
    answerText.value = transcript;
  });

  recognizer.addEventListener("end", () => {
    isRecording = false;
    micBtn.classList.remove("recording");
    micHint.textContent = "Tap to speak your answer";
  });
} else {
  micHint.textContent = "Voice input isn't supported in this browser — type your answer instead.";
  micBtn.disabled = true;
}

micBtn.addEventListener("click", () => {
  if (!recognizer) return;
  if (isRecording) {
    recognizer.stop();
    isRecording = false;
    micBtn.classList.remove("recording");
    micHint.textContent = "Tap to speak your answer";
  } else {
    answerText.value = "";
    recognizer.start();
    isRecording = true;
    micBtn.classList.add("recording");
    micHint.textContent = "Listening… tap again to stop";
  }
});

function speakQuestion(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.98;
  window.speechSynthesis.speak(utterance);
}

async function loadInterviewStartView() {
  interviewFeedbackPanel.hidden = true;
  interviewRoom.hidden = true;
  interviewStart.hidden = false;

  const jobs = await fetchJobOptionsForStudent().catch(() => []);
  populateJobSelect(interviewJobSelect, jobs, "General practice — pick a domain below instead");

  if (!domainsLoaded) {
    try {
      const domains = await apiFetch(`/jobs/domains`);
      domains.forEach((d) => {
        const opt = document.createElement("option");
        opt.value = d;
        opt.textContent = d;
        interviewDomainSelect.appendChild(opt);
      });
      domainsLoaded = true;
    } catch {
      // Non-fatal — auto-detect option still works without the list.
    }
  }
}

startInterviewBtn.addEventListener("click", async () => {
  startInterviewBtn.disabled = true;

  const jobPostingId = interviewJobSelect.value ? Number(interviewJobSelect.value) : null;
  setFeedback(
    interviewStartFeedback,
    jobPostingId
      ? "Building a mock interview grounded in this specific internship — this can take a bit longer than general practice…"
      : "Building your question set…",
    ""
  );

  try {
    const body = jobPostingId
      ? { job_posting_id: jobPostingId }
      : { domain: interviewDomainSelect.value || null };
    currentInterview = await apiFetch(`/students/${studentId}/interviews`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    currentQuestionPos = 0;
    interviewStart.hidden = true;
    interviewRoom.hidden = false;
    chatLog.innerHTML = "";
    renderCurrentQuestion();
  } catch (err) {
    setFeedback(interviewStartFeedback, err.message, "error");
  } finally {
    startInterviewBtn.disabled = false;
  }
});

function renderCurrentQuestion() {
  const total = currentInterview.questions.length;
  const q = currentInterview.questions[currentQuestionPos];

  interviewProgressText.textContent = `Question ${currentQuestionPos + 1} / ${total}`;
  progressFill.style.width = `${((currentQuestionPos) / total) * 100}%`;

  const bubble = document.createElement("div");
  bubble.className = "chat-bubble question";
  bubble.innerHTML = `<span class="chat-bubble-label">AI Interviewer · ${escapeHtml(q.category || "question")}</span>${escapeHtml(q.question_text)}`;
  chatLog.appendChild(bubble);
  chatLog.scrollTop = chatLog.scrollHeight;

  speakQuestion(q.question_text);

  answerText.value = "";
  setFeedback(interviewRoomFeedback, "", "");

  const isLast = currentQuestionPos === total - 1;
  nextQuestionBtn.hidden = false;
  submitInterviewBtn.hidden = !isLast;
  nextQuestionBtn.textContent = isLast ? "Save answer →" : "Save & Next →";
}

async function saveCurrentAnswer() {
  const q = currentInterview.questions[currentQuestionPos];
  const answer = answerText.value.trim();

  if (answer) {
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble answer";
    bubble.innerHTML = `<span class="chat-bubble-label">You</span>${escapeHtml(answer)}`;
    chatLog.appendChild(bubble);
    chatLog.scrollTop = chatLog.scrollHeight;

    try {
      await apiFetch(`/students/${studentId}/interviews/${currentInterview.id}/answers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers: [{ question_id: q.id, answer_text: answer }] }),
      });
      q.answer_text = answer;
    } catch (err) {
      setFeedback(interviewRoomFeedback, err.message, "error");
      return false;
    }
  }
  return true;
}

nextQuestionBtn.addEventListener("click", async () => {
  nextQuestionBtn.disabled = true;
  const saved = await saveCurrentAnswer();
  nextQuestionBtn.disabled = false;
  if (!saved) return;

  if (currentQuestionPos < currentInterview.questions.length - 1) {
    currentQuestionPos += 1;
    renderCurrentQuestion();
  }
});

skipQuestionBtn.addEventListener("click", () => {
  if (currentQuestionPos < currentInterview.questions.length - 1) {
    currentQuestionPos += 1;
    renderCurrentQuestion();
  } else {
    setFeedback(interviewRoomFeedback, "This is the last question — save your answer or submit for feedback.", "");
  }
});

submitInterviewBtn.addEventListener("click", async () => {
  submitInterviewBtn.disabled = true;
  setFeedback(interviewRoomFeedback, "Saving your last answer and generating feedback — this can take a bit…", "");

  const saved = await saveCurrentAnswer();
  if (!saved) {
    submitInterviewBtn.disabled = false;
    return;
  }

  try {
    const result = await apiFetch(`/students/${studentId}/interviews/${currentInterview.id}/submit`, {
      method: "POST",
    });
    renderFeedback(result.feedback);
    interviewRoom.hidden = true;
    interviewFeedbackPanel.hidden = false;
  } catch (err) {
    setFeedback(interviewRoomFeedback, err.message, "error");
  } finally {
    submitInterviewBtn.disabled = false;
  }
});

function renderImprovementsList(listEl, improvements) {
  if (!improvements || improvements.length === 0) {
    listEl.innerHTML = `<li class="empty-note">Nothing noted.</li>`;
    return;
  }
  listEl.innerHTML = improvements.map((imp) => `
    <li>
      <div class="entry-title">${escapeHtml(imp.area || "")}</div>
      <p class="entry-desc">${escapeHtml(imp.why_it_matters || "")}</p>
      ${(imp.resources && imp.resources.length) ? `
        <div class="tag-list" style="margin-top:8px;">
          ${imp.resources.map((r) => `<span class="tag">${escapeHtml(r)}</span>`).join("")}
        </div>
      ` : ""}
    </li>
  `).join("");
}

function renderFeedback(feedback) {
  if (!feedback) return;
  feedbackScore.textContent = feedback.overall_score;
  feedbackStrengths.innerHTML = (feedback.strengths || [])
    .map((s) => `<li><p class="entry-desc">${escapeHtml(s)}</p></li>`)
    .join("") || `<li class="empty-note">Nothing noted.</li>`;
  renderImprovementsList(feedbackImprovements, feedback.improvements);
  feedbackRecommendations.textContent = feedback.recommendations || "";
}

startAnotherBtn.addEventListener("click", () => {
  interviewFeedbackPanel.hidden = true;
  loadInterviewStartView();
});

// ---------------------------------------------------------
// DASHBOARD 06 — My Mock Interviews (history)
// ---------------------------------------------------------
const interviewHistoryList = document.getElementById("interviewHistoryList");
const interviewHistoryDetail = document.getElementById("interviewHistoryDetail");
const backToHistoryBtn = document.getElementById("backToHistoryBtn");
const historyDetailTitle = document.getElementById("historyDetailTitle");
const historyDetailScore = document.getElementById("historyDetailScore");
const historyDetailStrengths = document.getElementById("historyDetailStrengths");
const historyDetailImprovements = document.getElementById("historyDetailImprovements");
const historyDetailRecommendations = document.getElementById("historyDetailRecommendations");
const historyDetailTranscript = document.getElementById("historyDetailTranscript");

async function loadInterviewHistoryView() {
  interviewHistoryDetail.hidden = true;
  interviewHistoryList.hidden = false;
  interviewHistoryList.innerHTML = `<p class="empty-note">Loading…</p>`;

  try {
    const sets = await apiFetch(`/students/${studentId}/interviews`);
    renderInterviewHistoryList(sets);
  } catch (err) {
    interviewHistoryList.innerHTML = `<p class="empty-note">${escapeHtml(err.message)}</p>`;
  }
}

function renderInterviewHistoryList(sets) {
  interviewHistoryList.innerHTML = "";
  if (!sets.length) {
    interviewHistoryList.innerHTML = `<p class="empty-note">No mock interviews yet — start one from the AI Chat Bot tab.</p>`;
    return;
  }
  sets.forEach((s) => {
    const card = document.createElement("div");
    card.className = "job-card";
    const statusLabel = s.status === "completed" ? "Completed" : "In progress";
    card.innerHTML = `
      <div class="job-card-top">
        <div>
          <div class="job-card-title">${escapeHtml(s.domain || "General")} mock interview</div>
          <div class="job-card-sub">${statusLabel} · ${formatDate(s.created_at)}</div>
        </div>
        ${s.overall_score != null ? `<div class="job-card-score">${s.overall_score}<span>score</span></div>` : ""}
      </div>
      <div class="job-card-footer">
        <span></span>
        <button class="btn-secondary" data-interview-id="${s.id}">View details</button>
      </div>
    `;
    card.querySelector("[data-interview-id]").addEventListener("click", () => openInterviewDetail(s.id));
    interviewHistoryList.appendChild(card);
  });
}

async function openInterviewDetail(interviewId) {
  try {
    const detail = await apiFetch(`/students/${studentId}/interviews/${interviewId}`);
    interviewHistoryList.hidden = true;
    interviewHistoryDetail.hidden = false;

    historyDetailTitle.textContent = `${detail.domain || "General"} mock interview — ${formatDate(detail.created_at)}`;

    if (detail.feedback) {
      historyDetailScore.hidden = false;
      historyDetailScore.textContent = detail.feedback.overall_score;
      historyDetailStrengths.innerHTML = (detail.feedback.strengths || [])
        .map((s) => `<li><p class="entry-desc">${escapeHtml(s)}</p></li>`).join("");
      renderImprovementsList(historyDetailImprovements, detail.feedback.improvements);
      historyDetailRecommendations.textContent = detail.feedback.recommendations || "";
    } else {
      historyDetailScore.hidden = true;
      historyDetailStrengths.innerHTML = `<li class="empty-note">This set wasn't submitted for feedback.</li>`;
      historyDetailImprovements.innerHTML = "";
      historyDetailRecommendations.textContent = "";
    }

    historyDetailTranscript.innerHTML = "";
    detail.questions.forEach((q) => {
      const qBubble = document.createElement("div");
      qBubble.className = "chat-bubble question";
      qBubble.innerHTML = `<span class="chat-bubble-label">AI Interviewer · ${escapeHtml(q.category || "question")}</span>${escapeHtml(q.question_text)}`;
      historyDetailTranscript.appendChild(qBubble);

      if (q.answer_text) {
        const aBubble = document.createElement("div");
        aBubble.className = "chat-bubble answer";
        aBubble.innerHTML = `<span class="chat-bubble-label">You</span>${escapeHtml(q.answer_text)}`;
        historyDetailTranscript.appendChild(aBubble);
      }
    });
  } catch (err) {
    interviewHistoryList.innerHTML = `<p class="empty-note">${escapeHtml(err.message)}</p>`;
  }
}

backToHistoryBtn.addEventListener("click", () => {
  interviewHistoryDetail.hidden = true;
  interviewHistoryList.hidden = false;
});

// ---------------------------------------------------------
// Shared helper — job picker dropdowns (Toolkit + Career Assistant)
// ---------------------------------------------------------
async function fetchJobOptionsForStudent() {
  // Union of matched + applied jobs, deduped by id, for job-picker dropdowns.
  const jobsById = new Map();
  try {
    const matches = await apiFetch(`/students/${studentId}/matches`);
    matches.forEach((m) => { if (m.job) jobsById.set(m.job.id, m.job); });
  } catch { /* no matches yet */ }
  try {
    const applications = await apiFetch(`/students/${studentId}/applications`);
    applications.forEach((a) => { if (a.job) jobsById.set(a.job.id, a.job); });
  } catch { /* no applications yet */ }
  return Array.from(jobsById.values());
}

function populateJobSelect(selectEl, jobs, placeholderText) {
  const previousValue = selectEl.value;
  selectEl.innerHTML = `<option value="">${escapeHtml(placeholderText)}</option>`;
  jobs.forEach((job) => {
    const opt = document.createElement("option");
    opt.value = job.id;
    opt.textContent = `${job.title} — ${job.company}`;
    selectEl.appendChild(opt);
  });
  if (previousValue && jobs.some((j) => String(j.id) === previousValue)) {
    selectEl.value = previousValue;
  }
}

function renderList(listEl, items, mapFn, emptyMsg) {
  listEl.innerHTML = "";
  if (!items || items.length === 0) {
    listEl.innerHTML = `<li class="empty-note">${escapeHtml(emptyMsg)}</li>`;
    return;
  }
  items.forEach((item) => {
    const mapped = mapFn(item);
    const li = document.createElement("li");
    li.innerHTML = `
      <div class="entry-title">${escapeHtml(mapped.title)}</div>
      ${mapped.desc ? `<p class="entry-desc">${escapeHtml(mapped.desc)}</p>` : ""}
    `;
    listEl.appendChild(li);
  });
}

function renderTags(container, items, emptyMsg) {
  container.innerHTML = "";
  if (!items || items.length === 0) {
    container.innerHTML = `<p class="empty-note">${escapeHtml(emptyMsg)}</p>`;
    return;
  }
  items.forEach((text) => {
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.textContent = text;
    container.appendChild(tag);
  });
}

function downloadTextFile(text, filename) {
  const blob = new Blob([text || ""], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------
// DASHBOARD 07 — Application Toolkit (Skill Gap / Resume / Cover Letter / Interview Prep)
// ---------------------------------------------------------
const toolkitJobSelect = document.getElementById("toolkitJobSelect");
const toolkitJobFeedback = document.getElementById("toolkitJobFeedback");
const toolkitBody = document.getElementById("toolkitBody");

const subtabButtons = document.querySelectorAll(".subtab");
const subtabPanels = document.querySelectorAll(".subtab-panel");

const analyzeGapBtn = document.getElementById("analyzeGapBtn");
const gapFeedback = document.getElementById("gapFeedback");
const gapOutput = document.getElementById("gapOutput");
const gapCritical = document.getElementById("gapCritical");
const gapPartial = document.getElementById("gapPartial");
const gapPreferred = document.getElementById("gapPreferred");
const gapExperience = document.getElementById("gapExperience");
const gapQualification = document.getElementById("gapQualification");
const gapRecommendations = document.getElementById("gapRecommendations");

const generateResumeBtn = document.getElementById("generateResumeBtn");
const resumeGenFeedback = document.getElementById("resumeGenFeedback");
const resumeOutput = document.getElementById("resumeOutput");
const tailoredResumeText = document.getElementById("tailoredResumeText");
const saveResumeBtn = document.getElementById("saveResumeBtn");
const downloadResumeBtn = document.getElementById("downloadResumeBtn");

const generateCoverBtn = document.getElementById("generateCoverBtn");
const coverGenFeedback = document.getElementById("coverGenFeedback");
const coverOutput = document.getElementById("coverOutput");
const coverLetterText = document.getElementById("coverLetterText");
const saveCoverBtn = document.getElementById("saveCoverBtn");
const downloadCoverBtn = document.getElementById("downloadCoverBtn");

const generatePrepBtn = document.getElementById("generatePrepBtn");
const prepFeedback = document.getElementById("prepFeedback");
const prepOutput = document.getElementById("prepOutput");
const prepRevisionTopics = document.getElementById("prepRevisionTopics");
const prepTechnical = document.getElementById("prepTechnical");
const prepResumeBased = document.getElementById("prepResumeBased");
const prepProjectBased = document.getElementById("prepProjectBased");
const prepRoleSpecific = document.getElementById("prepRoleSpecific");
const prepHR = document.getElementById("prepHR");

let toolkitJobId = null;

async function loadToolkitView() {
  toolkitBody.hidden = true;
  setFeedback(toolkitJobFeedback, "Loading your matched/applied internships…", "");

  const jobs = await fetchJobOptionsForStudent().catch(() => []);
  populateJobSelect(toolkitJobSelect, jobs, "Choose from your matches or applications…");

  setFeedback(
    toolkitJobFeedback,
    jobs.length === 0 ? "No internships yet — find matches or apply to one on Dashboard 03 first." : "",
    ""
  );
}

toolkitJobSelect.addEventListener("change", () => {
  toolkitJobId = toolkitJobSelect.value ? Number(toolkitJobSelect.value) : null;
  resetToolkitOutputs();

  if (!toolkitJobId) {
    toolkitBody.hidden = true;
    return;
  }
  toolkitBody.hidden = false;

  // Silently load anything already generated for this job so revisiting
  // doesn't force a re-generate.
  loadExistingGap(toolkitJobId);
  loadExistingMaterials(toolkitJobId);
  loadExistingPrep(toolkitJobId);
});

function resetToolkitOutputs() {
  gapOutput.hidden = true;
  resumeOutput.hidden = true;
  coverOutput.hidden = true;
  prepOutput.hidden = true;
  setFeedback(gapFeedback, "", "");
  setFeedback(resumeGenFeedback, "", "");
  setFeedback(coverGenFeedback, "", "");
  setFeedback(prepFeedback, "", "");
}

subtabButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    subtabButtons.forEach((b) => b.classList.toggle("active", b === btn));
    subtabPanels.forEach((panel) => {
      panel.hidden = panel.id !== `subtab-${btn.dataset.subtab}`;
    });
  });
});

// --- Skill Gap (M3.1) ---
async function loadExistingGap(jobId) {
  try {
    renderGap(await apiFetch(`/students/${studentId}/skill-gap/${jobId}`));
  } catch { /* none generated yet */ }
}

analyzeGapBtn.addEventListener("click", async () => {
  if (!toolkitJobId) return;
  analyzeGapBtn.disabled = true;
  setFeedback(gapFeedback, "Comparing your profile against this role — this can take a few seconds…", "");
  try {
    const analysis = await apiFetch(`/students/${studentId}/skill-gap`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_posting_id: toolkitJobId }),
    });
    renderGap(analysis);
    setFeedback(gapFeedback, "Done.", "success");
  } catch (err) {
    setFeedback(gapFeedback, err.message, "error");
  } finally {
    analyzeGapBtn.disabled = false;
  }
});

function renderGap(analysis) {
  gapOutput.hidden = false;
  renderList(gapCritical, analysis.critical_gaps, (g) => ({ title: g.item, desc: g.why_it_matters }), "No critical gaps identified.");
  renderList(gapPartial, analysis.partial_gaps, (g) => ({ title: g.item, desc: g.why_it_matters }), "Nothing partially demonstrated flagged.");
  renderList(gapPreferred, analysis.preferred_gaps, (g) => ({ title: g.item, desc: g.why_it_matters }), "No preferred-skill gaps identified.");
  renderTags(gapExperience, analysis.experience_gaps, "No experience gaps noted.");
  renderTags(gapQualification, analysis.qualification_gaps, "No qualification gaps noted.");
  renderList(gapRecommendations, analysis.recommendations, (r) => ({ title: r }), "No recommendations given.");
}

// --- Tailored Resume + Cover Letter (M3.2) — one generation call produces both ---
async function loadExistingMaterials(jobId) {
  try {
    renderMaterials(await apiFetch(`/students/${studentId}/materials/${jobId}`));
  } catch { /* none generated yet */ }
}

async function generateMaterials() {
  if (!toolkitJobId) return;
  setFeedback(resumeGenFeedback, "Writing a tailored resume and cover letter for this role — this can take a bit…", "");
  setFeedback(coverGenFeedback, "", "");
  try {
    const material = await apiFetch(`/students/${studentId}/materials`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_posting_id: toolkitJobId }),
    });
    renderMaterials(material);
    setFeedback(resumeGenFeedback, "Done — edit freely below, then save.", "success");
  } catch (err) {
    setFeedback(resumeGenFeedback, err.message, "error");
    setFeedback(coverGenFeedback, err.message, "error");
  }
}

function renderMaterials(material) {
  if (material.resume_content) {
    tailoredResumeText.value = material.resume_content;
    resumeOutput.hidden = false;
  }
  if (material.cover_letter_content) {
    coverLetterText.value = material.cover_letter_content;
    coverOutput.hidden = false;
  }
}

generateResumeBtn.addEventListener("click", async () => {
  generateResumeBtn.disabled = true;
  await generateMaterials();
  generateResumeBtn.disabled = false;
});

generateCoverBtn.addEventListener("click", async () => {
  generateCoverBtn.disabled = true;
  await generateMaterials();
  generateCoverBtn.disabled = false;
});

saveResumeBtn.addEventListener("click", async () => {
  if (!toolkitJobId) return;
  saveResumeBtn.disabled = true;
  try {
    await apiFetch(`/students/${studentId}/materials/${toolkitJobId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_content: tailoredResumeText.value }),
    });
    setFeedback(resumeGenFeedback, "Saved.", "success");
  } catch (err) {
    setFeedback(resumeGenFeedback, err.message, "error");
  } finally {
    saveResumeBtn.disabled = false;
  }
});

saveCoverBtn.addEventListener("click", async () => {
  if (!toolkitJobId) return;
  saveCoverBtn.disabled = true;
  try {
    await apiFetch(`/students/${studentId}/materials/${toolkitJobId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cover_letter_content: coverLetterText.value }),
    });
    setFeedback(coverGenFeedback, "Saved.", "success");
  } catch (err) {
    setFeedback(coverGenFeedback, err.message, "error");
  } finally {
    saveCoverBtn.disabled = false;
  }
});

downloadResumeBtn.addEventListener("click", () => downloadTextFile(tailoredResumeText.value, "tailored-resume.txt"));
downloadCoverBtn.addEventListener("click", () => downloadTextFile(coverLetterText.value, "cover-letter.txt"));

// --- Interview Prep, job-specific (M3.3) ---
async function loadExistingPrep(jobId) {
  try {
    renderPrep(await apiFetch(`/students/${studentId}/interview-prep/${jobId}`));
  } catch { /* none generated yet */ }
}

generatePrepBtn.addEventListener("click", async () => {
  if (!toolkitJobId) return;
  generatePrepBtn.disabled = true;
  setFeedback(prepFeedback, "Building a prep plan grounded in this role, your profile, and any skill gaps already found — this can take a bit…", "");
  try {
    const plan = await apiFetch(`/students/${studentId}/interview-prep`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_posting_id: toolkitJobId }),
    });
    renderPrep(plan);
    setFeedback(prepFeedback, "Done.", "success");
  } catch (err) {
    setFeedback(prepFeedback, err.message, "error");
  } finally {
    generatePrepBtn.disabled = false;
  }
});

function renderPrep(plan) {
  prepOutput.hidden = false;
  renderTags(prepRevisionTopics, plan.revision_topics, "No revision topics flagged.");
  renderList(prepTechnical, plan.technical_questions, (q) => ({ title: q.question, desc: q.guidance }), "No technical questions generated.");
  renderList(prepResumeBased, plan.resume_based_questions, (q) => ({ title: q.question, desc: q.guidance }), "No resume-based questions generated.");
  renderList(prepProjectBased, plan.project_based_questions, (q) => ({ title: q.question, desc: q.guidance }), "No project-based questions generated.");
  renderList(prepRoleSpecific, plan.role_specific_questions, (q) => ({ title: q.question, desc: q.guidance }), "No role-specific questions generated.");
  renderList(prepHR, plan.hr_questions, (q) => ({ title: q.question, desc: q.guidance }), "No HR questions generated.");
}

// ---------------------------------------------------------
// DASHBOARD 08 — Career Assistant (conversational, M3.4)
// ---------------------------------------------------------
const chatJobSelect = document.getElementById("chatJobSelect");
const assistantChatLog = document.getElementById("assistantChatLog");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const chatSendBtn = document.getElementById("chatSendBtn");
const chatFeedback = document.getElementById("chatFeedback");

async function loadChatView() {
  const jobs = await fetchJobOptionsForStudent().catch(() => []);
  populateJobSelect(chatJobSelect, jobs, "General question (no specific job)");

  try {
    const history = await apiFetch(`/students/${studentId}/chat`);
    if (history.length) {
      assistantChatLog.innerHTML = "";
      history.forEach((m) => appendChatBubble(m.role, m.content));
    }
  } catch { /* no history yet — leave the greeting bubble in place */ }
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  appendChatBubble("user", message);
  chatInput.value = "";
  chatSendBtn.disabled = true;
  setFeedback(chatFeedback, "Thinking…", "");

  try {
    const result = await apiFetch(`/students/${studentId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        job_posting_id: chatJobSelect.value ? Number(chatJobSelect.value) : null,
      }),
    });
    appendChatBubble("assistant", result.reply.content);
    setFeedback(chatFeedback, "", "");
  } catch (err) {
    setFeedback(chatFeedback, err.message, "error");
  } finally {
    chatSendBtn.disabled = false;
  }
});

function appendChatBubble(role, text) {
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${role === "user" ? "answer" : "question"}`;
  const label = role === "user" ? "You" : "Career Assistant";
  bubble.innerHTML = `<span class="chat-bubble-label">${escapeHtml(label)}</span>${escapeHtml(text)}`;
  assistantChatLog.appendChild(bubble);
  assistantChatLog.scrollTop = assistantChatLog.scrollHeight;
}

// ---------------------------------------------------------
// TOPBAR — Saved Jobs panel + Notifications panel (M4)
// ---------------------------------------------------------
const savedJobsBtn = document.getElementById("savedJobsBtn");
const savedJobsPanel = document.getElementById("savedJobsPanel");
const savedJobsBackdrop = document.getElementById("savedJobsBackdrop");
const closeSavedJobsBtn = document.getElementById("closeSavedJobsBtn");
const savedJobsFeedback = document.getElementById("savedJobsFeedback");
const savedJobsList = document.getElementById("savedJobsList");

const notificationsBtn = document.getElementById("notificationsBtn");
const notificationsPanel = document.getElementById("notificationsPanel");
const notificationsBackdrop = document.getElementById("notificationsBackdrop");
const closeNotificationsBtn = document.getElementById("closeNotificationsBtn");
const notificationsFeedback = document.getElementById("notificationsFeedback");
const notificationsList = document.getElementById("notificationsList");
const notifBadge = document.getElementById("notifBadge");

savedJobsBtn.addEventListener("click", async () => {
  savedJobsPanel.hidden = false;
  setFeedback(savedJobsFeedback, "Loading…", "");
  try {
    const saved = await apiFetch(`/students/${studentId}/saved-jobs`);
    savedJobIds = new Set(saved.map((s) => s.job.id));
    setFeedback(savedJobsFeedback, saved.length ? "" : "Nothing saved yet — tap 🔖 Save on any internship to bookmark it here.", "");
    savedJobsList.innerHTML = "";
    saved.forEach((s) => {
      const card = buildJobCard(s.job, { showApply: true, showSave: true });
      savedJobsList.appendChild(card);
    });
  } catch (err) {
    setFeedback(savedJobsFeedback, err.message, "error");
  }
});

function closeSavedJobsPanel() { savedJobsPanel.hidden = true; }
closeSavedJobsBtn.addEventListener("click", closeSavedJobsPanel);
savedJobsBackdrop.addEventListener("click", closeSavedJobsPanel);

notificationsBtn.addEventListener("click", async () => {
  notificationsPanel.hidden = false;
  await loadNotifications();
});

function closeNotificationsPanel() { notificationsPanel.hidden = true; }
closeNotificationsBtn.addEventListener("click", closeNotificationsPanel);
notificationsBackdrop.addEventListener("click", closeNotificationsPanel);

async function loadNotifications() {
  setFeedback(notificationsFeedback, "Loading…", "");
  try {
    const notifications = await apiFetch(`/students/${studentId}/notifications`);
    updateNotifBadge(notifications.length);

    if (!notifications.length) {
      setFeedback(notificationsFeedback, "No upcoming deadlines or interviews — reminders show up here once you set a deadline or interview date on an application (Dashboard 04).", "");
      notificationsList.innerHTML = "";
      return;
    }
    setFeedback(notificationsFeedback, "", "");
    notificationsList.innerHTML = notifications.map((n) => `
      <div class="notification-card urgency-${n.urgency}">
        <div class="notification-card-title">${n.kind === "interview" ? "🎤 " : "⏰ "}${escapeHtml(n.job_title)} — ${escapeHtml(n.company)}</div>
        <div class="notification-card-sub">${escapeHtml(n.message)}</div>
      </div>
    `).join("");
  } catch (err) {
    setFeedback(notificationsFeedback, err.message, "error");
  }
}

function updateNotifBadge(count) {
  if (count > 0) {
    notifBadge.textContent = count > 9 ? "9+" : String(count);
    notifBadge.hidden = false;
  } else {
    notifBadge.hidden = true;
  }
}

// Refresh the badge count once right after login/session-resume, so a
// student sees it without having to open the panel first.
(async () => {
  // Waits for the app shell to actually be visible (i.e. logged in) before
  // trying — enterApp() runs first on login/resume, this just polls briefly.
  for (let i = 0; i < 20; i++) {
    if (!appShell.hidden && studentId) {
      try {
        const notifications = await apiFetch(`/students/${studentId}/notifications`);
        updateNotifBadge(notifications.length);
      } catch {
        // non-fatal — badge just stays hidden until the panel is opened
      }
      break;
    }
    await new Promise((r) => setTimeout(r, 300));
  }
})();

// ---------------------------------------------------------
// Small utilities
// ---------------------------------------------------------
function renderEntryList(listEl, items, mapFn) {
  listEl.innerHTML = "";
  if (!items || items.length === 0) {
    listEl.innerHTML = `<li class="empty-note">Nothing here yet — parse a resume on Dashboard 02.</li>`;
    return;
  }
  items.forEach((item) => {
    const mapped = mapFn(item);
    const li = document.createElement("li");
    li.innerHTML = `
      <div class="entry-title">${escapeHtml(mapped.title)}</div>
      ${mapped.sub ? `<div class="entry-sub">${escapeHtml(mapped.sub)}</div>` : ""}
      ${mapped.desc ? `<p class="entry-desc">${escapeHtml(mapped.desc)}</p>` : ""}
    `;
    listEl.appendChild(li);
  });
}

function formatDateRange(start, end) {
  if (!start && !end) return "";
  return ` · ${start || "?"} – ${end || "present"}`;
}

function formatDate(isoString) {
  try {
    return new Date(isoString).toLocaleDateString();
  } catch {
    return isoString;
  }
}

// Builds the public URL for a stored profile photo. The backend saves the
// path using the server OS's separator (backslashes on Windows, e.g.
// "uploads\\photo_1_x.jpg"), which breaks a naive URL — so only the file
// name is used, under the /uploads static mount.
function photoUrl(photoPath) {
  const fileName = String(photoPath).split(/[\\/]/).pop();
  return `${API_BASE_URL}/uploads/${encodeURIComponent(fileName)}`;
}


function setFeedback(el, message, kind) {
  el.textContent = message;
  el.className = "feedback" + (kind ? ` ${kind}` : "");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
