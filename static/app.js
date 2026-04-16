// ============================
//  CIRCUIT MIND AI — app.js
//  Full feature upgrade: mode tabs, history sidebar,
//  char counter, print/export, streaming steps
// ============================

const API_BASE = window.location.origin;

// ── Example queries mapped by key ─────────────────────────────────────────────
const EXAMPLES = {
  mesh: `A circuit has two meshes. Mesh 1 contains a 12V voltage source and resistors R1=4Ω and R2=6Ω. Mesh 2 contains a 6V voltage source and resistors R2=6Ω (shared) and R3=3Ω. Find all mesh currents using Mesh Analysis (KVL).`,
  nodal: `Apply Nodal Analysis (KCL) to find all node voltages. A 5A current source supplies current into node V1. R1=10Ω connects V1 to ground. R2=5Ω connects V1 to V2. A 2A current source connects to V2. R3=8Ω connects V2 to ground.`,
  thevenin: `Find the Thevenin equivalent circuit (Vth and Rth) across terminals A and B. The circuit consists of a 24V source in series with R1=8Ω. R2=12Ω is connected between the junction of R1 and the source's return, and terminal A. Terminal B is the negative terminal of the source.`,
  superposition: `Use the Superposition Theorem to find the current through a 10Ω resistor R3. The circuit has two sources: V1=20V and V2=10V. R1=5Ω is in series with V1. R2=5Ω is in series with V2. R3=10Ω connects the midpoints. Show the independent solutions for each source then combine.`,
  ac: `An AC series RLC circuit has R=50Ω, L=0.1H, C=100µF, and a sinusoidal source Vs=100∠0° V at 50 Hz. Find: (a) impedance Z, (b) current I (phasor), (c) voltages across each element, (d) real power P, reactive power Q, apparent power S, and power factor.`,
  resonance: `A series RLC circuit has R=10Ω, L=0.1H, C=1µF. Find: (a) resonant frequency ω₀ and f₀, (b) quality factor Q, (c) bandwidth BW, (d) half-power frequencies ω₁ and ω₂. Also verify that BW = R/L.`,
  transient: `An RC circuit has R=10kΩ and C=100µF. The capacitor is initially uncharged and a 9V step voltage is applied at t=0. Find: (a) the time constant τ, (b) the capacitor voltage equation vc(t), (c) the voltage at t=1τ, 2τ, and 5τ.`,
  laplace: `An RC circuit in the s-domain: R=1kΩ, C=1µF, initial capacitor voltage V₀=0. Find the transfer function H(s)=Vout(s)/Vin(s) for a voltage divider where Vout is across the capacitor. Then determine the inverse Laplace transform to find the step response.`,
};

// Loading step messages for animated progress
const LOADING_STEPS = [
  'Injecting Bakshi EEE knowledge base…',
  'Detecting analysis mode…',
  'Calling Gemini AI…',
  'Formulating governing equations…',
  'Running SymPy symbolic solver…',
  'Verifying with energy/power balance…',
  'Rendering LaTeX and results…',
];

// ── DOM Refs ──────────────────────────────────────────────────────────────────
const uploadZone      = document.getElementById('uploadZone');
const uploadContent   = document.getElementById('uploadContent');
const uploadPreview   = document.getElementById('uploadPreview');
const previewImg      = document.getElementById('previewImg');
const imageInput      = document.getElementById('imageInput');
const removeImageBtn  = document.getElementById('removeImage');
const queryInput      = document.getElementById('queryInput');
const charCount       = document.getElementById('charCount');
const solveBtn        = document.getElementById('solveBtn');
const resultsSection  = document.getElementById('resultsSection');
const resultsBody     = document.getElementById('resultsBody');
const resultsBadges   = document.getElementById('resultsBadges');
const loadingOverlay  = document.getElementById('loadingOverlay');
const loadingStep     = document.getElementById('loadingStep');
const loadingBar      = document.getElementById('loadingBar');
const copyBtn         = document.getElementById('copyBtn');
const printBtn        = document.getElementById('printBtn');
const clearBtn        = document.getElementById('clearBtn');
const statusDot       = document.querySelector('.status-dot');
const statusText      = document.querySelector('.status-text');
const exampleBtn      = document.getElementById('exampleBtn');
const clearQueryBtn   = document.getElementById('clearQueryBtn');
const modeTabs        = document.getElementById('modeTabs');
const sidebarToggle   = document.getElementById('sidebarToggle');
const sidebar         = document.getElementById('sidebar');
const historyList     = document.getElementById('historyList');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');

let imageFile = null;
let selectedMode = 'auto';
let exampleIndex = 0;
const exampleKeys = Object.keys(EXAMPLES);

// ── Health Check ─────────────────────────────────────────────────────────────
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    const data = await res.json();
    if (data.api_key_set) {
      statusDot.className = 'status-dot online';
      statusText.textContent = 'Gemini Connected';
    } else {
      statusDot.className = 'status-dot offline';
      statusText.textContent = 'API Key Missing';
    }
  } catch {
    statusDot.className = 'status-dot offline';
    statusText.textContent = 'Server Offline';
  }
}

checkHealth();

// ── Mode Tabs ─────────────────────────────────────────────────────────────────
if (modeTabs) {
  modeTabs.addEventListener('click', (e) => {
    const tab = e.target.closest('.mode-tab');
    if (!tab) return;
    document.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    selectedMode = tab.dataset.mode;
  });
}

// Auto-detect mode hint from textarea content
queryInput.addEventListener('input', () => {
  const q = queryInput.value.toLowerCase();
  let hint = 'auto';
  if (/bode|frequency response|low.?pass|high.?pass|filter|cutoff/.test(q)) hint = 'frequency';
  else if (/laplace|s-domain|transfer function|partial fraction/.test(q)) hint = 'laplace';
  else if (/transient|step response|time constant|charging|discharging|overdamped|underdamped/.test(q)) hint = 'transient';
  else if (/phasor|ac circuit|sinusoidal|impedance|power factor|resonan|rms|reactive/.test(q)) hint = 'ac';
  else if (/two.?port|z-param|y-param|h-param|abcd/.test(q)) hint = 'two_port';
  else if (/mesh|nodal|thevenin|norton|superposition|kvl|kcl|dc/.test(q)) hint = 'dc';

  // Only auto-update if user hasn't manually locked a mode
  if (selectedMode === 'auto' && hint !== 'auto') {
    document.querySelectorAll('.mode-tab').forEach(t => {
      t.classList.toggle('hint', t.dataset.mode === hint);
    });
  } else {
    document.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('hint'));
  }

  // Char counter
  const len = queryInput.value.length;
  if (charCount) {
    charCount.textContent = `${len} / 2000`;
    charCount.style.color = len > 1800 ? 'var(--error)' : len > 1500 ? '#f59e0b' : '';
  }
});

// ── Image Upload ─────────────────────────────────────────────────────────────
document.getElementById('uploadTrigger')?.addEventListener('click', () => imageInput.click());
uploadZone.addEventListener('click', (e) => {
  if (!imageFile && e.target !== document.getElementById('uploadTrigger')) imageInput.click();
});
imageInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) handleImageFile(file);
});
uploadZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadZone.classList.add('dragover');
});
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) handleImageFile(file);
});

function handleImageFile(file) {
  imageFile = file;
  previewImg.src = URL.createObjectURL(file);
  uploadContent.style.display = 'none';
  uploadPreview.style.display = 'block';
}

removeImageBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  imageFile = null;
  imageInput.value = '';
  previewImg.src = '';
  uploadContent.style.display = 'flex';
  uploadPreview.style.display = 'none';
});

// ── Example Cards & Load Button ───────────────────────────────────────────────
document.querySelectorAll('.example-card').forEach(card => {
  card.addEventListener('click', () => {
    const key = card.dataset.example;
    const mode = card.dataset.mode;
    if (EXAMPLES[key]) {
      queryInput.value = EXAMPLES[key];
      queryInput.dispatchEvent(new Event('input'));
      // Switch mode tab to match
      if (mode) {
        document.querySelectorAll('.mode-tab').forEach(t => {
          t.classList.toggle('active', t.dataset.mode === mode);
        });
        selectedMode = mode;
      }
      queryInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
      queryInput.focus();
    }
  });
});

exampleBtn?.addEventListener('click', () => {
  queryInput.value = EXAMPLES[exampleKeys[exampleIndex % exampleKeys.length]];
  queryInput.dispatchEvent(new Event('input'));
  exampleIndex++;
});

clearQueryBtn?.addEventListener('click', () => {
  queryInput.value = '';
  queryInput.dispatchEvent(new Event('input'));
  queryInput.focus();
});

// ── Solve ─────────────────────────────────────────────────────────────────────
solveBtn.addEventListener('click', analyze);
queryInput.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.key === 'Enter') analyze();
});

async function analyze() {
  const query = queryInput.value.trim();
  if (!query && !imageFile) {
    showError('Please provide a circuit description or upload an image.');
    return;
  }

  showLoading(true);
  startLoadingAnimation();

  const formData = new FormData();
  if (query)     formData.append('query', query);
  if (imageFile) formData.append('image', imageFile);
  formData.append('mode', selectedMode);

  try {
    const response = await fetch(`${API_BASE}/analyze`, { method: 'POST', body: formData });
    const data = await response.json();

    if (!response.ok || data.error) throw new Error(data.error || 'Server error');

    renderResults(data);
    await refreshHistory();
  } catch (err) {
    showError(err.message || 'Unknown error occurred.');
  } finally {
    showLoading(false);
    stopLoadingAnimation();
  }
}

// ── Loading Animation ─────────────────────────────────────────────────────────
let _loadingTimer = null;
let _stepIndex = 0;
let _progressVal = 0;

function startLoadingAnimation() {
  _stepIndex = 0;
  _progressVal = 5;
  _updateLoadingUI();
  _loadingTimer = setInterval(() => {
    _stepIndex = (_stepIndex + 1) % LOADING_STEPS.length;
    _progressVal = Math.min(95, _progressVal + Math.random() * 14 + 6);
    _updateLoadingUI();
  }, 1800);
}

function _updateLoadingUI() {
  if (loadingStep) loadingStep.textContent = LOADING_STEPS[_stepIndex];
  if (loadingBar)  loadingBar.style.width = `${_progressVal}%`;
}

function stopLoadingAnimation() {
  clearInterval(_loadingTimer);
  if (loadingBar) {
    loadingBar.style.width = '100%';
    setTimeout(() => { if (loadingBar) loadingBar.style.width = '0%'; }, 500);
  }
}

function showLoading(show) {
  if (loadingOverlay) loadingOverlay.style.display = show ? 'flex' : 'none';
  solveBtn.disabled = show;
  if (show) {
    solveBtn.querySelector('.solve-btn-text').textContent = 'Analyzing…';
  } else {
    solveBtn.querySelector('.solve-btn-text').textContent = 'Analyze Circuit';
  }
}

// ── Render Results ────────────────────────────────────────────────────────────
function renderResults(data) {
  resultsSection.style.display = 'block';

  // Build badges
  if (resultsBadges) {
    const modeLabel = {
      dc: '⚡ DC', ac: '〰️ AC', transient: '📈 Transient',
      laplace: '🔁 Laplace', frequency: '📊 Frequency', two_port: '🔲 Two-Port'
    };
    const mode = data.mode_detected || 'dc';
    const model = data.model_used || '';
    resultsBadges.innerHTML = `
      <span class="badge badge-mode">${modeLabel[mode] || mode.toUpperCase()}</span>
      ${model ? `<span class="badge badge-model">${model}</span>` : ''}
      ${data.code_executed ? `<span class="badge badge-sym">✓ SymPy Verified</span>` : ''}
    `;
  }

  // Update results title
  const titleEl = document.querySelector('.results-title');
  if (titleEl) titleEl.innerHTML = `<span class="results-icon">🧠</span> Analysis Results`;

  // Render markdown+math
  resultsBody.innerHTML = markdownToHtml(data.analysis || '');

  // MathJax re-render
  if (window.MathJax) {
    MathJax.typesetPromise([resultsBody]).catch(console.error);
  }

  resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── History Sidebar ───────────────────────────────────────────────────────────
sidebarToggle?.addEventListener('click', () => {
  sidebar.classList.toggle('open');
});

clearHistoryBtn?.addEventListener('click', async () => {
  await fetch(`${API_BASE}/history`, { method: 'DELETE' });
  await refreshHistory();
});

async function refreshHistory() {
  try {
    const res = await fetch(`${API_BASE}/history`);
    const data = await res.json();
    renderHistory(data.history || []);
  } catch { /* server may not be up yet */ }
}

function renderHistory(items) {
  if (!historyList) return;
  if (!items.length) {
    historyList.innerHTML = `<div class="sidebar-empty">No queries yet.<br>Solve a circuit to see history.</div>`;
    return;
  }

  const modeIcons = {
    dc: '⚡', ac: '〰️', transient: '📈', laplace: '🔁', frequency: '📊', two_port: '🔲', auto: '🤖'
  };

  historyList.innerHTML = [...items].reverse().map(item => `
    <div class="history-item" data-id="${item.id}">
      <div class="history-item-icon">${modeIcons[item.mode] || '⚡'}</div>
      <div class="history-item-body">
        <div class="history-item-query">${escapeHtml(item.query)}</div>
        <div class="history-item-meta">
          <span class="history-mode">${item.mode?.toUpperCase()}</span>
          <span class="history-time">${item.timestamp}</span>
        </div>
      </div>
    </div>
  `).join('');
}

// Load history on page open
refreshHistory();

// ── Print / Export PDF ────────────────────────────────────────────────────────
printBtn?.addEventListener('click', () => {
  window.print();
});

// ── Copy ──────────────────────────────────────────────────────────────────────
copyBtn?.addEventListener('click', () => {
  const text = resultsBody.innerText;
  navigator.clipboard.writeText(text).then(() => {
    copyBtn.textContent = '✅ Copied!';
    setTimeout(() => copyBtn.textContent = '📋 Copy', 2000);
  });
});

// ── Clear Results ─────────────────────────────────────────────────────────────
clearBtn?.addEventListener('click', () => {
  resultsSection.style.display = 'none';
  resultsBody.innerHTML = '';
  if (resultsBadges) resultsBadges.innerHTML = '';
});

// ── Error Display ─────────────────────────────────────────────────────────────
function showError(msg) {
  resultsSection.style.display = 'block';
  resultsBody.innerHTML = `
    <div style="padding:1.5rem; background:rgba(255,77,109,0.08); border:1px solid rgba(255,77,109,0.3); border-radius:12px; color:#ff4d6d;">
      <strong>⚠️ Error:</strong> ${escapeHtml(msg)}
      <br/><br/>
      <small>Make sure your <code>GEMINI_API_KEY</code> is set in the <code>.env</code> file and the Flask server is running on port 5000.</small>
    </div>`;
  showLoading(false);
  stopLoadingAnimation();
}

// ── Markdown → HTML ───────────────────────────────────────────────────────────
function markdownToHtml(md) {
  // Protect math blocks first
  const mathBlocks = [];
  md = md.replace(/\$\$([\s\S]+?)\$\$/g, (_, m) => {
    mathBlocks.push(`$$${m}$$`);
    return `%%MATH_BLOCK_${mathBlocks.length - 1}%%`;
  });
  md = md.replace(/\$([^$\n]+?)\$/g, (_, m) => {
    mathBlocks.push(`$${m}$`);
    return `%%MATH_INLINE_${mathBlocks.length - 1}%%`;
  });

  // Fenced code blocks
  md = md.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    const escaped = code.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return `<pre class="code-block"><button class="copy-code-btn" onclick="copyCode(this)">Copy</button><code class="lang-${lang || 'text'}">${escaped}</code></pre>`;
  });

  // Inline code
  md = md.replace(/`([^`\n]+)`/g, '<code>$1</code>');

  // Headings
  md = md.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
  md = md.replace(/^### (.+)$/gm,  '<h3>$1</h3>');
  md = md.replace(/^## (.+)$/gm,   '<h2>$1</h2>');
  md = md.replace(/^# (.+)$/gm,    '<h1>$1</h1>');

  // Horizontal rule
  md = md.replace(/^---+$/gm, '<hr />');

  // Bold & italic
  md = md.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  md = md.replace(/\*\*(.+?)\*\*/g,     '<strong>$1</strong>');
  md = md.replace(/\*(.+?)\*/g,         '<em>$1</em>');

  // Tables
  md = md.replace(/((^\|.+\|\n)+)/gm, (tableStr) => {
    const rows = tableStr.trim().split('\n').filter(r => !r.match(/^\|[-:| ]+\|$/));
    if (rows.length < 1) return tableStr;
    let html = '<table>';
    rows.forEach((row, i) => {
      const cells = row.split('|').filter((_, idx, arr) => idx > 0 && idx < arr.length - 1);
      const tag = i === 0 ? 'th' : 'td';
      html += '<tr>' + cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('') + '</tr>';
    });
    html += '</table>';
    return html;
  });

  // Unordered lists
  md = md.replace(/(^- .+(\n|$))+/gm, (block) => {
    const items = block.trim().split('\n').map(l => `<li>${l.replace(/^- /, '')}</li>`).join('');
    return `<ul>${items}</ul>`;
  });

  // Ordered lists
  md = md.replace(/(^\d+\. .+(\n|$))+/gm, (block) => {
    const items = block.trim().split('\n').map(l => `<li>${l.replace(/^\d+\. /, '')}</li>`).join('');
    return `<ol>${items}</ol>`;
  });

  // Paragraphs
  md = md.split('\n\n').map(para => {
    para = para.trim();
    if (!para) return '';
    if (/^(<h|<ul|<ol|<pre|<table|<hr)/.test(para)) return para;
    return `<p>${para.replace(/\n/g, ' ')}</p>`;
  }).join('\n');

  // Restore math
  md = md.replace(/%%MATH_BLOCK_(\d+)%%/g, (_, i) => mathBlocks[parseInt(i)]);
  md = md.replace(/%%MATH_INLINE_(\d+)%%/g, (_, i) => mathBlocks[parseInt(i)]);

  return md;
}

// ── Copy Code Helper ──────────────────────────────────────────────────────────
window.copyCode = function(btn) {
  const code = btn.nextElementSibling?.innerText || '';
  navigator.clipboard.writeText(code).then(() => {
    btn.textContent = '✓ Copied';
    setTimeout(() => btn.textContent = 'Copy', 2000);
  });
};

// ── Utility ───────────────────────────────────────────────────────────────────
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
