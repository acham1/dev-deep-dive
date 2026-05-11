const API_BASE = window.DEEP_DIVE_API_BASE || "";

// --- Signup ---

const signupForm = document.getElementById("signup-form");
if (signupForm) {
  signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = signupForm.querySelector('input[type="email"]');
    const msg = document.getElementById("signup-message");
    const email = input.value.trim();
    if (!email) return;

    msg.textContent = "Subscribing...";
    msg.className = "signup-message";

    try {
      const res = await fetch(`${API_BASE}/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (res.ok) {
        msg.textContent =
          data.status === "already_subscribed"
            ? "You're already subscribed!"
            : "You're in! Watch your inbox.";
        msg.className = "signup-message success";
        input.value = "";
      } else {
        msg.textContent = data.error || "Something went wrong.";
        msg.className = "signup-message error";
      }
    } catch {
      msg.textContent = "Network error. Please try again.";
      msg.className = "signup-message error";
    }
  });
}

// --- Archive ---

const archiveGrid = document.getElementById("archive-grid");
const loadMoreBtn = document.getElementById("load-more-btn");
let lastReportId = null;

async function loadArchive(append = false) {
  if (!archiveGrid) return;

  let url = `${API_BASE}/reports?limit=20`;
  if (append && lastReportId) {
    url += `&start_after=${lastReportId}`;
  }

  try {
    const res = await fetch(url);
    const data = await res.json();
    const reports = data.reports || [];

    if (!append) archiveGrid.innerHTML = "";

    for (const r of reports) {
      const a = document.createElement("a");
      a.href = `report.html?id=${r.id}`;
      a.className = "card";

      const date = r.created_at
        ? new Date(r.created_at).toLocaleDateString()
        : "";

      a.innerHTML = `
        <span class="category">${r.category || "misc"}</span>
        <h3>${r.title || r.project_name}</h3>
        <p class="tagline">${r.tagline || ""}</p>
        <span class="date">${date}</span>
      `;
      archiveGrid.appendChild(a);
    }

    if (reports.length > 0) {
      lastReportId = reports[reports.length - 1].id;
    }

    if (loadMoreBtn) {
      loadMoreBtn.style.display = reports.length < 20 ? "none" : "block";
    }
  } catch {
    archiveGrid.innerHTML = "<p>Failed to load reports.</p>";
  }
}

if (loadMoreBtn) {
  loadMoreBtn.addEventListener("click", () => loadArchive(true));
}

if (archiveGrid) {
  loadArchive();
}

// --- Single Report ---

const reportContainer = document.getElementById("report-container");

async function loadReport() {
  if (!reportContainer) return;

  const id = new URLSearchParams(location.search).get("id");
  if (!id) {
    reportContainer.innerHTML = "<p>No report ID specified.</p>";
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/reports/${id}`);
    if (!res.ok) {
      reportContainer.innerHTML = "<p>Report not found.</p>";
      return;
    }
    const r = await res.json();

    const date = r.created_at
      ? new Date(r.created_at).toLocaleDateString()
      : "";

    document.title = `${r.title || r.project_name} — Weekly Deep Dive`;

    reportContainer.innerHTML = `
      <div class="report-header">
        <div class="container">
          <h2>${r.title || r.project_name}</h2>
          <p class="tagline">${r.tagline || ""}</p>
          <p class="report-meta">
            ${date}
            ${r.repo_url ? ` · <a href="${r.repo_url}" target="_blank">GitHub</a>` : ""}
          </p>
        </div>
      </div>

      <div class="section">
        <div class="container">
          <div class="why-section">
            <h3>Why It Matters</h3>
            <div>${marked.parse(r.why_it_matters || "")}</div>
          </div>

          <div class="tabs">
            <button class="tab active" data-level="beginner" onclick="switchTab('beginner')">Beginner</button>
            <button class="tab" data-level="intermediate" onclick="switchTab('intermediate')">Intermediate</button>
            <button class="tab" data-level="advanced" onclick="switchTab('advanced')">Advanced</button>
          </div>

          <div class="tab-content active" id="tab-beginner">
            <div class="level-content beginner">${marked.parse(r.beginner || "")}</div>
          </div>
          <div class="tab-content" id="tab-intermediate">
            <div class="level-content intermediate">${marked.parse(r.intermediate || "")}</div>
          </div>
          <div class="tab-content" id="tab-advanced">
            <div class="level-content advanced">${marked.parse(r.advanced || "")}</div>
          </div>

          <div class="takeaways-section">
            <h3>Key Takeaways</h3>
            <div>${marked.parse(r.key_takeaways || "")}</div>
          </div>
        </div>
      </div>
    `;
  } catch {
    reportContainer.innerHTML = "<p>Failed to load report.</p>";
  }
}

// Expose globally for inline onclick
window.switchTab = function (level) {
  document.querySelectorAll(".tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.level === level);
  });
  document.querySelectorAll(".tab-content").forEach((c) => {
    c.classList.toggle("active", c.id === `tab-${level}`);
  });
};

if (reportContainer) {
  loadReport();
}

// --- Latest report on index page ---

const latestPreview = document.getElementById("latest-preview");

async function loadLatest() {
  if (!latestPreview) return;

  try {
    const res = await fetch(`${API_BASE}/reports?limit=1`);
    const data = await res.json();
    const reports = data.reports || [];

    if (reports.length === 0) {
      latestPreview.innerHTML =
        "<p>No deep dives yet. The first one is coming soon!</p>";
      return;
    }

    const r = reports[0];
    const date = r.created_at
      ? new Date(r.created_at).toLocaleDateString()
      : "";

    latestPreview.innerHTML = `
      <a href="report.html?id=${r.id}" class="card">
        <span class="category">${r.category || "misc"}</span>
        <h3>${r.title || r.project_name}</h3>
        <p class="tagline">${r.tagline || ""}</p>
        <span class="date">${date}</span>
      </a>
    `;
  } catch {
    latestPreview.innerHTML = "";
  }
}

if (latestPreview) {
  loadLatest();
}

// --- Unsubscribe ---

const unsubMessage = document.getElementById("unsub-result");

async function handleUnsubscribe() {
  if (!unsubMessage) return;

  const token = new URLSearchParams(location.search).get("token");
  if (!token) {
    unsubMessage.textContent = "Invalid unsubscribe link.";
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/unsubscribe?token=${token}`);
    if (res.ok) {
      unsubMessage.textContent =
        "You've been unsubscribed. Sorry to see you go!";
    } else {
      unsubMessage.textContent = "Unsubscribe link not found or already used.";
    }
  } catch {
    unsubMessage.textContent = "Something went wrong. Please try again.";
  }
}

if (unsubMessage) {
  handleUnsubscribe();
}
