/* ─────────────────────────────────────────────────────────────
   RUST DETECTION — app.js  v2
   Handles: drag-drop, instant upload, Flask API call, results render
   Backend expected at http://localhost:5000
   ───────────────────────────────────────────────────────────── */

const API_BASE = 'http://localhost:5000';

// ── DOM refs ──────────────────────────────────────────────────
const dropzone          = document.getElementById('dropzone');
const dropzoneWrapper   = document.getElementById('dropzoneWrapper');
const fileInput         = document.getElementById('fileInput');
const browseBtn         = document.getElementById('browseBtn');
const loadingPanel      = document.getElementById('loadingPanel');
const resultsPanel      = document.getElementById('resultsPanel');
const errorPanel        = document.getElementById('errorPanel');
const errorMsg          = document.getElementById('errorMsg');
const errorHint         = document.getElementById('errorHint');
const retryBtn          = document.getElementById('retryBtn');
const analyzeAnotherBtn = document.getElementById('analyzeAnotherBtn');

const backendStatus = document.getElementById('backendStatus');
const bsDot         = document.getElementById('bsDot');
const bsText        = document.getElementById('bsText');

const lstep1 = document.getElementById('lstep1');
const lstep2 = document.getElementById('lstep2');
const lstep3 = document.getElementById('lstep3');

const gradeBadge    = document.getElementById('gradeBadge');
const gradeIcon     = document.getElementById('gradeIcon');
const gradeLabel    = document.getElementById('gradeLabel');
const gradeDesc     = document.getElementById('gradeDesc');
const numDetections = document.getElementById('numDetections');
const coveragePct   = document.getElementById('coveragePct');
const gradeNum      = document.getElementById('gradeNum');
const originalImg   = document.getElementById('originalImg');
const annotatedImg  = document.getElementById('annotatedImg');

const severityFill     = document.getElementById('severityFill');
const severityMarker   = document.getElementById('severityMarker');
const severityPctLabel = document.getElementById('severityPctLabel');

const confValue   = document.getElementById('confValue');
const confAvg     = document.getElementById('confAvg');
const confMax     = document.getElementById('confMax');
const confMin     = document.getElementById('confMin');
const confDesc    = document.getElementById('confDesc');
const confArc     = document.getElementById('confArc');

const detectionsList    = document.getElementById('detectionsList');
const detectionsSection = document.getElementById('detectionsSection');

// ── BACKGROUND PARTICLES ──────────────────────────────────────
(function createParticles() {
  const container = document.getElementById('bgParticles');
  if (!container) return;
  for (let i = 0; i < 18; i++) {
    const p    = document.createElement('div');
    p.className = 'particle';
    const size  = Math.random() * 120 + 40;
    const left  = Math.random() * 100;
    const dur   = Math.random() * 20 + 15;
    const delay = Math.random() * -30;
    p.style.cssText = `width:${size}px;height:${size}px;left:${left}%;animation-duration:${dur}s;animation-delay:${delay}s;`;
    container.appendChild(p);
  }
})();

// ── BACKEND HEALTH CHECK ──────────────────────────────────────
async function checkBackend() {
  try {
    const res = await fetch(`${API_BASE}/api/health`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      backendStatus.className = 'backend-status connected';
      bsText.textContent = '✓ Backend connected — Ready to analyze';
    } else {
      throw new Error('Non-OK response');
    }
  } catch {
    backendStatus.className = 'backend-status disconnected';
    bsText.textContent = '✗ Backend offline — Run: python app.py';
  }
}

// Poll every 5 seconds
checkBackend();
setInterval(checkBackend, 5000);

// ── DRAG & DROP ───────────────────────────────────────────────
dropzone.addEventListener('dragover', e => {
  e.preventDefault();
  dropzone.classList.add('dragging');
});
['dragleave', 'dragend'].forEach(ev =>
  dropzone.addEventListener(ev, () => dropzone.classList.remove('dragging'))
);
dropzone.addEventListener('drop', e => {
  e.preventDefault();
  dropzone.classList.remove('dragging');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) runAnalysis(file);
});

browseBtn.addEventListener('click', e => { e.stopPropagation(); fileInput.click(); });
dropzone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) runAnalysis(fileInput.files[0]);
});

retryBtn.addEventListener('click', resetToDropzone);
analyzeAnotherBtn.addEventListener('click', resetToDropzone);

// ── MAIN FLOW ─────────────────────────────────────────────────
async function runAnalysis(file) {
  showPanel('loading');
  animateLoadingSteps();

  // Preview original immediately
  originalImg.src = URL.createObjectURL(file);

  const formData = new FormData();
  formData.append('image', file);

  try {
    const res = await fetch(`${API_BASE}/api/analyze`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
      throw new Error(err.error || `HTTP ${res.status}`);
    }

    const data = await res.json();
    renderResults(data);
    showPanel('results');

  } catch (err) {
    console.error('[RustGuard]', err);

    if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError') || err.name === 'TypeError') {
      errorMsg.textContent = 'Cannot reach the local backend server.';
      errorHint.innerHTML  = `
        <strong>Make sure the Flask backend is running:</strong><br/>
        <code style="color:#ff6b35">python app.py</code>
        &nbsp;in the project directory, then try again.
      `;
    } else {
      errorMsg.textContent = err.message;
      errorHint.innerHTML  = '';
    }
    showPanel('error');
  }
}

// ── LOADING STEP ANIMATION ────────────────────────────────────
let stepTimer1, stepTimer2;
function animateLoadingSteps() {
  clearTimeout(stepTimer1);
  clearTimeout(stepTimer2);
  [lstep1, lstep2, lstep3].forEach(s => s.className = 'lstep');
  lstep1.classList.add('active');

  stepTimer1 = setTimeout(() => {
    lstep1.classList.replace('active', 'done');
    lstep2.classList.add('active');
    stepTimer2 = setTimeout(() => {
      lstep2.classList.replace('active', 'done');
      lstep3.classList.add('active');
    }, 1400);
  }, 900);
}

// ── RENDER RESULTS ────────────────────────────────────────────
function renderResults(data) {
  const { overall, detections = [], avg_confidence = 0, original_image, annotated_image } = data;

  // Images
  originalImg.src  = `data:image/jpeg;base64,${original_image}`;
  annotatedImg.src = `data:image/jpeg;base64,${annotated_image}`;

  // Grade badge
  const key = overall.label.toLowerCase();  // 'none' | 'mild' | 'moderate' | 'critical'
  gradeBadge.className = `grade-badge grade-${key}`;

  const icons = { none: '✓', mild: '⚠', moderate: '⚡', critical: '🔴' };
  gradeIcon.textContent = icons[key] ?? '●';
  gradeLabel.textContent = overall.label;
  gradeDesc.textContent  = overall.description;
  numDetections.textContent = overall.num_detections ?? 0;
  coveragePct.textContent   = overall.coverage_pct != null ? `${overall.coverage_pct}%` : '—';
  gradeNum.textContent      = `${overall.grade} / 3`;

  // Severity bar
  const sevPct = overall.severity_pct ?? 0;
  severityPctLabel.textContent = `${sevPct.toFixed(1)}%`;
  setTimeout(() => {
    // Fill covers the unused right portion of the bar
    severityFill.style.width  = `${100 - sevPct}%`;
    severityFill.style.left   = `${sevPct}%`;
    severityMarker.style.left = `${Math.min(98, Math.max(2, sevPct))}%`;
  }, 120);

  // Highlight active zone
  document.querySelectorAll('.zone').forEach(z => z.classList.remove('active'));
  const zoneMap = { mild: 'zoneMild', moderate: 'zoneModerate', critical: 'zoneCritical' };
  if (zoneMap[key]) document.getElementById(zoneMap[key])?.classList.add('active');

  // Confidence ring
  const conf = avg_confidence ?? 0;
  confValue.textContent = conf.toFixed(1);
  confAvg.textContent   = `${conf.toFixed(1)}%`;

  if (detections.length) {
    const maxC = Math.max(...detections.map(d => d.confidence));
    const minC = Math.min(...detections.map(d => d.confidence));
    confMax.textContent = `${(maxC * 100).toFixed(1)}%`;
    confMin.textContent = `${(minC * 100).toFixed(1)}%`;
  } else {
    confMax.textContent = '—';
    confMin.textContent = '—';
  }

  confDesc.textContent = conf >= 75
    ? 'High confidence — results are highly reliable.'
    : conf >= 50
      ? 'Moderate confidence — consider visual verification.'
      : conf > 0
        ? 'Lower confidence — manual inspection recommended.'
        : 'No detections — the image appears corrosion-free.';

  // Animate arc  (circumference of r=50 circle = 314.159)
  const circ   = 314.159;
  const filled = (conf / 100) * circ;
  setTimeout(() => {
    confArc.style.strokeDasharray = `${filled} ${circ - filled}`;
  }, 200);

  // Detection cards
  detectionsList.innerHTML = '';
  if (detections.length === 0) {
    detectionsSection.style.display = 'none';
  } else {
    detectionsSection.style.display = '';
    detections.forEach((det, i) => {
      const card = document.createElement('div');
      card.className = 'detection-card';
      card.innerHTML = `
        <div class="det-num">${i + 1}</div>
        <div class="det-class">${capitalize(det.class_name)}</div>
        <div class="det-sev-badge sev-${det.severity_label}">${det.severity_label}</div>
        <div class="det-conf">${(det.confidence * 100).toFixed(1)}%</div>
      `;
      detectionsList.appendChild(card);
    });
  }

  // Scroll to top of upload section
  setTimeout(() => {
    document.getElementById('upload-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 150);
}

// ── PANEL VISIBILITY ──────────────────────────────────────────
function showPanel(which) {
  dropzoneWrapper.style.display = which === 'dropzone' ? 'flex' : 'none';
  loadingPanel.style.display    = which === 'loading'  ? 'flex' : 'none';
  resultsPanel.style.display    = which === 'results'  ? 'flex' : 'none';
  errorPanel.style.display      = which === 'error'    ? 'block' : 'none';
}

function resetToDropzone() {
  fileInput.value = '';
  // Reset severity bar
  severityFill.style.width  = '100%';
  severityFill.style.left   = '0%';
  severityMarker.style.left = '2%';
  // Reset confidence arc
  confArc.style.strokeDasharray = '0 314';
  showPanel('dropzone');
}

function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// ── INIT ──────────────────────────────────────────────────────
showPanel('dropzone');

// Smooth nav active state on scroll
const sections = document.querySelectorAll('section[id]');
const navLinks  = document.querySelectorAll('.nav-pill');
const observer  = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      navLinks.forEach(l => l.classList.remove('active'));
      const link = document.querySelector(`.nav-pill[href="#${entry.target.id}"]`);
      link?.classList.add('active');
    }
  });
}, { threshold: 0.3 });
sections.forEach(s => observer.observe(s));
