/**
 * Predictive Healthcare Assistant - Clinical Frontend Controller
 * Handles Multi-Page Navigation, Patient Registration, Real-Time Prediction & Lifetime History Retrieval
 */

// Automatically use relative path when hosted (e.g. Render/Cloud/port 8000), fallback to 8000 for local standalone frontend
const API_BASE = (window.location.hostname === "127.0.0.1" && window.location.port === "5500") 
  ? "http://127.0.0.1:8000" 
  : "";

// State Management
const state = {
  patients: [],
  history: [],
  selectedPatient: null,
  activeTab: "assessment-page"
};

// DOM Utility
const $ = id => document.getElementById(id);
const $$ = selector => document.querySelectorAll(selector);

// Toast notification helper
function showToast(message, type = "success") {
  const toast = $("toast");
  toast.textContent = message;
  toast.className = `toast-msg show ${type === "error" ? "toast-error" : "toast-success"}`;
  setTimeout(() => {
    toast.className = "toast-msg";
  }, 4500);
}

function handleFetchError(err) {
  if (err.message === "Failed to fetch" || err.name === "TypeError") {
    showToast("⚠️ Cannot connect to backend server. Make sure the FastAPI server is running on http://127.0.0.1:8000", "error");
  } else {
    showToast(`Error: ${err.message}`, "error");
  }
}

// ----------------------------------------------------
// Navigation / Page Router
// ----------------------------------------------------
function navigateTo(targetPageId) {
  // Update nav tabs styling
  $$(".nav-tab-btn").forEach(btn => {
    if (btn.dataset.target === targetPageId) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  // Switch active page
  $$(".page-view").forEach(page => {
    if (page.id === targetPageId) {
      page.classList.add("active");
    } else {
      page.classList.remove("active");
    }
  });

  state.activeTab = targetPageId;

  // Refresh page-specific data on visit
  if (targetPageId === "patients-page") {
    loadPatients();
  } else if (targetPageId === "history-page") {
    loadHistory();
  } else if (targetPageId === "analytics-page") {
    loadAnalytics();
  }
}

// ----------------------------------------------------
// Server Health Check & Status Pill
// ----------------------------------------------------
async function checkServerHealth() {
  const pill = $("serverStatusBadge");
  const text = $("serverStatusText");
  try {
    const res = await fetch(`${API_BASE}/api/health`, { method: "GET" });
    if (res.ok) {
      pill.className = "server-status-pill online";
      text.textContent = "Backend Online";
      pill.title = "Connected to FastAPI Server at http://127.0.0.1:8000";
    } else {
      throw new Error();
    }
  } catch {
    pill.className = "server-status-pill offline";
    text.textContent = "Backend Offline";
    pill.title = "FastAPI server is not responding. Run: uvicorn main:app --reload";
  }
}

// Attach Tab Navigation Click Handlers
$$(".nav-tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const target = btn.dataset.target;
    navigateTo(target);
  });
});

// ----------------------------------------------------
// Modal Controller (Top-Bar Add Patient)
// ----------------------------------------------------
function openAddPatientModal() {
  $("addPatientModal").classList.add("show");
  $("newPatientName").focus();
}

function closeAddPatientModal() {
  $("addPatientModal").classList.remove("show");
  $("addPatientForm").reset();
}

$("openAddPatientModalBtn").addEventListener("click", openAddPatientModal);
$("closeAddPatientModalBtn").addEventListener("click", closeAddPatientModal);
$("cancelPatientModalBtn").addEventListener("click", closeAddPatientModal);
$("addPatientPageBtn").addEventListener("click", openAddPatientModal);

// Close modal on click outside content
$("addPatientModal").addEventListener("click", (e) => {
  if (e.target === $("addPatientModal")) {
    closeAddPatientModal();
  }
});

// ----------------------------------------------------
// Patient Registration Form Submission
// ----------------------------------------------------
$("addPatientForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    name: $("newPatientName").value.trim(),
    age: parseInt($("newPatientAge").value, 10),
    gender: $("newPatientGender").value,
    blood_group: $("newPatientBlood").value,
    contact: $("newPatientContact").value.trim(),
    medical_history: $("newPatientHistory").value.trim()
  };

  try {
    const res = await fetch(`${API_BASE}/api/patients`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to register patient.");
    }

    const savedPatient = await res.json();
    showToast(`✓ Patient "${savedPatient.name}" (${savedPatient.patient_code}) successfully registered!`);
    closeAddPatientModal();

    // Reload patients & link as current active patient for immediate screening
    await loadPatients();
    selectActivePatient(savedPatient.id);
    navigateTo("assessment-page");

  } catch (err) {
    handleFetchError(err);
  }
});

// ----------------------------------------------------
// Patient Data Loading & Rendering
// ----------------------------------------------------
async function loadPatients() {
  try {
    const res = await fetch(`${API_BASE}/api/patients`);
    if (!res.ok) throw new Error("Could not fetch patients from database");
    const data = await res.json();
    state.patients = data;

    // Update Top-Nav Counter Badge
    $("patientBadge").textContent = data.length;

    // Populate dropdown in Assessment view
    populatePatientSelect(data);

    // Populate Patients Table
    renderPatientsTable(data);
  } catch (err) {
    console.error(err);
  }
}

function populatePatientSelect(patients) {
  const select = $("quickPatientSelect");
  const currentVal = select.value;
  select.innerHTML = `<option value="">-- Link Registered Patient --</option>`;

  patients.forEach(p => {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = `${p.name} (${p.patient_code || 'ID: ' + p.id}) - ${p.age}y, ${p.gender}`;
    select.appendChild(opt);
  });

  if (state.selectedPatient) {
    select.value = state.selectedPatient.id;
  } else {
    select.value = currentVal;
  }
}

function renderPatientsTable(patients) {
  const tbody = $("patientsTableBody");
  const emptyState = $("patientsEmptyState");

  if (!patients.length) {
    tbody.innerHTML = "";
    emptyState.classList.remove("hidden");
    return;
  }

  emptyState.classList.add("hidden");
  tbody.innerHTML = patients.map(p => {
    const riskBadge = p.latest_risk 
      ? `<span class="badge-risk risk-${p.latest_risk}">${p.latest_risk}</span>`
      : `<span class="helper-text">Not Assessed</span>`;

    return `
      <tr>
        <td><strong>${p.patient_code || 'PAT-' + p.id}</strong></td>
        <td><strong>${p.name}</strong></td>
        <td>${p.age} yrs / ${p.gender}</td>
        <td>${p.contact || '-'}</td>
        <td>${p.blood_group || 'Unknown'}</td>
        <td><span class="patient-pill" style="font-size: 11px;">${p.assessment_count || 0} screenings</span></td>
        <td>${riskBadge}</td>
        <td style="font-size: 12px; color: var(--text-muted);">${p.created_at || '-'}</td>
        <td>
          <div style="display:flex; gap:6px;">
            <button class="btn btn-outline btn-sm" onclick="viewPatientDetail(${p.id})">👤 View Profile</button>
            <button class="btn btn-primary btn-sm" onclick="startAssessmentForPatient(${p.id})">📋 Screen</button>
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

// Patient search filter
$("patientSearchInput").addEventListener("input", (e) => {
  const q = e.target.value.toLowerCase();
  const filtered = state.patients.filter(p => 
    p.name.toLowerCase().includes(q) || 
    (p.patient_code && p.patient_code.toLowerCase().includes(q))
  );
  renderPatientsTable(filtered);
});

// ----------------------------------------------------
// Active Patient Context Selection
// ----------------------------------------------------
function selectActivePatient(patientId) {
  if (!patientId) {
    state.selectedPatient = null;
    $("selectedPatientDisplay").textContent = "No registered patient linked (Guest assessment)";
    $("clearPatientLinkBtn").style.display = "none";
    $("quickPatientSelect").value = "";
    return;
  }

  const patient = state.patients.find(p => p.id == patientId);
  if (patient) {
    state.selectedPatient = patient;
    $("selectedPatientDisplay").innerHTML = `Linked to: <strong>${patient.name}</strong> (${patient.patient_code || 'ID:' + patient.id}) • Age: ${patient.age} • ${patient.gender}`;
    $("clearPatientLinkBtn").style.display = "inline-block";
    $("quickPatientSelect").value = patient.id;

    // Pre-fill form fields with patient demographic data
    $("name").value = patient.name;
    $("age").value = patient.age;
    $("gender").value = patient.gender;
  }
}

$("quickPatientSelect").addEventListener("change", (e) => {
  selectActivePatient(e.target.value);
});

$("clearPatientLinkBtn").addEventListener("click", () => {
  selectActivePatient(null);
});

// ----------------------------------------------------
// Patient Profile / Lifetime Detail View
// ----------------------------------------------------
window.viewPatientDetail = async function(patientId) {
  try {
    const res = await fetch(`${API_BASE}/api/patients/${patientId}`);
    if (!res.ok) throw new Error("Could not load patient details");
    const data = await res.json();

    // Populate Profile Tab
    $("detailPatientCode").textContent = data.patient_code || `PAT-${data.id}`;
    $("detailPatientName").textContent = data.name;
    $("detailPatientAge").textContent = `${data.age} years`;
    $("detailPatientGender").textContent = data.gender;
    $("detailPatientBlood").textContent = data.blood_group || "Unknown";
    $("detailPatientContact").textContent = data.contact || "None";
    $("detailPatientCreated").textContent = data.created_at || "N/A";
    $("detailPatientHistory").textContent = data.medical_history || "No pre-existing conditions reported.";

    // Render Lifetime Assessments for this patient
    const tbody = $("patientAssessmentsBody");
    const emptyState = $("patientAssessmentsEmpty");

    if (!data.assessments || !data.assessments.length) {
      tbody.innerHTML = "";
      emptyState.classList.remove("hidden");
    } else {
      emptyState.classList.add("hidden");
      tbody.innerHTML = data.assessments.map(a => `
        <tr>
          <td style="font-size:12px; color:var(--text-muted);">${a.created_at}</td>
          <td>${a.bmi}</td>
          <td>${a.systolic_bp} mmHg</td>
          <td>${a.glucose} mg/dL</td>
          <td>${a.cholesterol} mg/dL</td>
          <td>${a.heart_rate} bpm</td>
          <td><strong>${a.diabetes_risk}%</strong></td>
          <td><strong>${a.heart_risk}%</strong></td>
          <td><strong>${a.hypertension_risk}%</strong></td>
          <td><span class="badge-risk risk-${a.overall_risk}">${a.overall_risk}</span></td>
        </tr>
      `).join("");
    }

    // Set button actions for this patient
    $("newAssessmentForPatientBtn").onclick = () => {
      selectActivePatient(data.id);
      navigateTo("assessment-page");
    };

    // Show tab & navigate
    $("patientDetailTab").style.display = "inline-flex";
    navigateTo("patient-detail-page");

  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
  }
};

window.startAssessmentForPatient = function(patientId) {
  selectActivePatient(patientId);
  navigateTo("assessment-page");
};

$("backToPatientsBtn").addEventListener("click", () => {
  navigateTo("patients-page");
});

// ----------------------------------------------------
// Health Assessment Submission & Real-Time Prediction
// ----------------------------------------------------
$("healthForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("submitAssessmentBtn").disabled = true;
  $("submitAssessmentBtn").textContent = "Calculating Risk...";

  const payload = {
    patient_id: state.selectedPatient ? state.selectedPatient.id : null,
    patient_code: state.selectedPatient ? state.selectedPatient.patient_code : null,
    name: $("name").value.trim(),
    age: parseInt($("age").value, 10),
    gender: $("gender").value,
    bmi: parseFloat($("bmi").value),
    systolic_bp: parseFloat($("bp").value),
    glucose: parseFloat($("glucose").value),
    cholesterol: parseFloat($("cholesterol").value),
    heart_rate: parseFloat($("heartRate").value),
    smoking: $("smoking").value,
    activity: $("activity").value
  };

  try {
    const res = await fetch(`${API_BASE}/api/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error("Assessment processing failed. Please check inputs.");
    const result = await res.json();

    // Render results in UI
    renderAssessmentResult(result);
    showToast(`✓ Clinical Assessment complete for ${result.name}! Stored in database.`);

    // Refresh database records in background
    loadPatients();
    loadHistory();

    // Scroll to results
    $("resultCard").scrollIntoView({ behavior: "smooth" });

  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
  } finally {
    $("submitAssessmentBtn").disabled = false;
    $("submitAssessmentBtn").textContent = "⚡ Calculate & Store Assessment";
  }
});

function renderAssessmentResult(data) {
  const resultCard = $("resultCard");
  resultCard.classList.remove("hidden");

  $("assessmentTimestamp").textContent = `Assessed on ${data.created_at || new Date().toLocaleString()}`;

  // Composite Risk Banner
  const overallBanner = $("overallBanner");
  overallBanner.className = `result-banner ${data.overall_risk.toLowerCase()}`;
  $("overallRiskValue").textContent = `${data.overall_risk} OVERALL RISK`;
  $("overallBadgeHolder").innerHTML = `<span class="badge-risk risk-${data.overall_risk}">${data.overall_risk} RISK</span>`;

  // Risk Probability Numbers
  $("diabetesRiskValue").textContent = `${data.diabetes_risk}%`;
  $("heartRiskValue").textContent = `${data.heart_risk}%`;
  $("hypertensionRiskValue").textContent = `${data.hypertension_risk}%`;

  // Progress Bar Animations & Colors
  updateProgressBar($("diabetesProgress"), data.diabetes_risk);
  updateProgressBar($("heartProgress"), data.heart_risk);
  updateProgressBar($("hypertensionProgress"), data.hypertension_risk);

  // Lists
  $("factorsList").innerHTML = data.risk_factors.map(f => `<li>${f}</li>`).join("");
  $("recommendationsList").innerHTML = data.recommendations.map(r => `<li>${r}</li>`).join("");

  // Link to full patient history if applicable
  $("viewPatientHistoryBtn").onclick = () => {
    if (data.patient_id) {
      viewPatientDetail(data.patient_id);
    } else {
      navigateTo("history-page");
    }
  };
}

function updateProgressBar(element, value) {
  element.style.width = `${value}%`;
  element.className = "progress-bar-fill";
  if (value < 30) {
    element.classList.add("fill-low");
  } else if (value < 60) {
    element.classList.add("fill-medium");
  } else {
    element.classList.add("fill-high");
  }
}

// ----------------------------------------------------
// Lifetime History Data Fetching & Table Rendering
// ----------------------------------------------------
async function loadHistory() {
  try {
    const res = await fetch(`${API_BASE}/api/history`);
    if (!res.ok) throw new Error("Could not retrieve assessment history");
    const data = await res.json();
    state.history = data;

    // Update History Badge
    $("historyBadge").textContent = data.length;

    renderHistoryTable(data);
  } catch (err) {
    console.error(err);
  }
}

function renderHistoryTable(records) {
  const tbody = $("historyTableBody");
  const emptyState = $("historyEmptyState");

  if (!records.length) {
    tbody.innerHTML = "";
    emptyState.classList.remove("hidden");
    return;
  }

  emptyState.classList.add("hidden");
  tbody.innerHTML = records.map(r => `
    <tr>
      <td><strong>#${r.id}</strong></td>
      <td>
        <strong>${r.name}</strong>
        ${r.patient_code ? `<span class="patient-pill" style="margin-left:6px; font-size:10px;">${r.patient_code}</span>` : ''}
      </td>
      <td style="font-size:12px; color:var(--text-muted);">
        BMI: ${r.bmi} | BP: ${r.systolic_bp} | Gluc: ${r.glucose} | Chol: ${r.cholesterol} | HR: ${r.heart_rate}
      </td>
      <td><strong>${r.diabetes_risk}%</strong></td>
      <td><strong>${r.heart_risk}%</strong></td>
      <td><strong>${r.hypertension_risk}%</strong></td>
      <td><span class="badge-risk risk-${r.overall_risk}">${r.overall_risk}</span></td>
      <td style="font-size:12px; color:var(--text-muted);">${r.created_at}</td>
    </tr>
  `).join("");
}

// History search filter
$("historySearchInput").addEventListener("input", (e) => {
  const q = e.target.value.toLowerCase();
  const filtered = state.history.filter(r => 
    r.name.toLowerCase().includes(q) ||
    (r.patient_code && r.patient_code.toLowerCase().includes(q))
  );
  renderHistoryTable(filtered);
});

$("refreshHistoryBtn").addEventListener("click", loadHistory);
$("refreshDataBtn").addEventListener("click", async () => {
  await loadPatients();
  await loadHistory();
  showToast("✓ Database synchronized successfully!");
});

// ----------------------------------------------------
// Analytics Loader & Export Handler
// ----------------------------------------------------
async function loadAnalytics() {
  try {
    const res = await fetch(`${API_BASE}/api/analytics/summary`);
    if (!res.ok) throw new Error("Could not fetch analytics data");
    const data = await res.json();

    $("analyticTotalPatients").textContent = data.total_patients || 0;
    $("analyticTotalAssessments").textContent = data.total_assessments || 0;
    $("analyticHighRiskCount").textContent = data.high_risk_patients_count || 0;

    const lowPct = data.risk_percentages["LOW"] || 0;
    const medPct = data.risk_percentages["MEDIUM"] || 0;
    const highPct = data.risk_percentages["HIGH"] || 0;

    const lowCount = data.risk_distribution["LOW"] || 0;
    const medCount = data.risk_distribution["MEDIUM"] || 0;
    const highCount = data.risk_distribution["HIGH"] || 0;

    $("pctLowRisk").textContent = `${lowPct}% (${lowCount})`;
    $("pctMedRisk").textContent = `${medPct}% (${medCount})`;
    $("pctHighRisk").textContent = `${highPct}% (${highCount})`;

    $("barLowRisk").style.width = `${lowPct}%`;
    $("barMedRisk").style.width = `${medPct}%`;
    $("barHighRisk").style.width = `${highPct}%`;

    // Biomarkers
    $("avgBmi").textContent = data.average_vitals.bmi ? `${data.average_vitals.bmi} kg/m²` : "-";
    $("avgBp").textContent = data.average_vitals.systolic_bp ? `${data.average_vitals.systolic_bp} mmHg` : "-";
    $("avgGlucose").textContent = data.average_vitals.glucose ? `${data.average_vitals.glucose} mg/dL` : "-";
    $("avgCholesterol").textContent = data.average_vitals.cholesterol ? `${data.average_vitals.cholesterol} mg/dL` : "-";
    $("avgHr").textContent = data.average_vitals.heart_rate ? `${data.average_vitals.heart_rate} bpm` : "-";
    $("avgDiabetes").textContent = data.average_vitals.diabetes_risk ? `${data.average_vitals.diabetes_risk}%` : "-";

  } catch (err) {
    handleFetchError(err);
  }
}

if ($("exportCsvBtn")) {
  $("exportCsvBtn").addEventListener("click", () => {
    window.open(`${API_BASE}/api/export/assessments/csv`, "_blank");
  });
}

if ($("refreshAnalyticsBtn")) {
  $("refreshAnalyticsBtn").addEventListener("click", () => {
    loadAnalytics();
    showToast("✓ Analytics refreshed");
  });
}

// ----------------------------------------------------
// Initialization
// ----------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  checkServerHealth();
  loadPatients();
  loadHistory();
  // Poll server health every 8 seconds
  setInterval(checkServerHealth, 8000);
});
