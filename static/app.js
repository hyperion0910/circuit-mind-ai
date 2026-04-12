// ============================
//  CIRCUIT MIND AI — app.js
// ============================

const API_BASE = 'http://localhost:5000';

// Example queries
const EXAMPLES = {
  mesh: `A circuit has two meshes. Mesh 1 contains a 12V voltage source and resistors R1=4Ω and R2=6Ω. Mesh 2 contains a 6V voltage source and resistors R2=6Ω (shared) and R3=3Ω. Find all mesh currents using Mesh Analysis (KVL).`,
  thevenin: `Find the Thevenin equivalent circuit (Vth and Rth) across terminals A and B. The circuit consists of a 24V source in series with R1=8Ω. R2=12Ω is connected between the junction of R1 and the source's return, and terminal A. Terminal B is the negative terminal of the source.`,
  superposition: `Use the Superposition Theorem to find the current through a 10Ω resistor R3. The circuit has two sources: V1=20V and V2=10V. R1=5Ω is in series with V1. R2=5Ω is in series with V2. R3=10Ω connects the midpoints. Show the independent solutions for each source then combine.`,
  nodal: `Apply Nodal Analysis (KCL) to find all node voltages. A 5A current source supplies current into node V1. R1=10Ω connects V1 to ground. R2=5Ω connects V1 to V2. A 2A current source connects to V2. R3=8Ω connects V2 to ground.`
};

// DOM elements
let imageFile = null;
const uploadZone    = document.getElementById('uploadZone');
const uploadContent = document.getElementById('uploadContent');
const uploadPreview = document.getElementById('uploadPreview');
const previewImg    = document.getElementById('previewImg');
const imageInput    = document.getElementById('imageInput');
const removeImageBtn= document.getElementById('removeImage');
const queryInput    = document.getElementById('queryInput');
const solveBtn      = document.getElementById('solveBtn');
const resultsSection= document.getElementById('resultsSection');
const resultsBody   = document.getElementById('resultsBody');
const loadingOverlay= document.getElementById('loadingOverlay');
const loadingStep   = document.getElementById('loadingStep');
const copyBtn       = document.getElementById('copyBtn');
const clearBtn      = document.getElementById('clearBtn');
const statusDot     = document.querySelector('.status-dot');
const statusText    = document.querySelector('.status-text');
const exampleBtn    = document.getElementById('exampleBtn');

// ============================
//  API Health Check
// ============================
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    const data = await res.json();
    if (data.api_key_set) {
      statusDot.className = 'status-dot online';
      statusText.textContent = 'Connected to Gemini';
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

// ============================
//  Image Upload Handling
// ============================
uploadTrigger.addEventListener('click', () => imageInput.click());
uploadZone.addEventListener('click', (e) => {
  if (!imageFile && e.target !== document.getElementById('uploadTrigger')) {
    imageInput.click();
  }
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
  const url = URL.createObjectURL(file);
  previewImg.src = url;
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

// ============================
//  Example Buttons
// ============================
document.querySelectorAll('.example-card').forEach(card => {
  card.addEventListener('click', () => {
    const key = card.dataset.example;
    if (EXAMPLES[key]) {
      queryInput.value = EXAMPLES[key];
      queryInput.focus();
      queryInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  });
});

let exampleIndex = 0;
const exampleKeys = Object.keys(EXAMPLES);
exampleBtn.addEventListener('click', () => {
  queryInput.value = EXAMPLES[exampleKeys[exampleIndex % exampleKeys.length]];
  exampleIndex++;
});

// ============================
//  Main Solve Logic
// ============================
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
  setLoadingStep('Sending to Gemini AI...');

  const formData = new FormData();
  if (query)     formData.append('query', query);
  if (imageFile) formData.append('image', imageFile);

  try {
    setLoadingStep('Analyzing circuit topology...');
    const response = await fetch(`${API_BASE}/analyze`, { method: 'POST', body: formData });
    
    setLoadingStep('Running symbolic solver...');
    const data = await response.json();

    if (!response.ok || data.error) {
      throw new Error(data.error || 'Server error');
    }

    setLoadingStep('Rendering results...');
    await new Promise(r => setTimeout(r, 300));

    renderResults(data.analysis, data.model_used);
  } catch (err) {
    showError(err.message || 'Unknown error occurred.');
  } finally {
    showLoading(false);
  }
}

// ============================
//  Render Results
// ============================
function renderResults(markdownText, modelUsed) {
  resultsSection.style.display = 'block';
  if (modelUsed) {
    document.querySelector('.results-title').innerHTML =
      `<span class="results-icon">🧠</span> Analysis Results <span style="font-size:0.7rem;font-weight:500;background:rgba(108,99,255,0.2);border:1px solid rgba(108,99,255,0.3);padding:2px 9px;border-radius:20px;color:#9090b8;margin-left:8px;">${modelUsed}</span>`;
  }
  resultsBody.innerHTML = markdownToHtml(markdownText);
  
  // Trigger MathJax typesetting
  if (window.MathJax) {
    MathJax.typesetPromise([resultsBody]).catch(console.error);
  }

  resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ============================
//  Markdown → HTML
// ============================
function markdownToHtml(md) {
  // Protect math blocks before processing
  const mathBlocks = [];
  md = md.replace(/\$\$([\s\S]+?)\$\$/g, (_, m) => {
    mathBlocks.push(`$$${m}$$`);
    return `%%MATH_BLOCK_${mathBlocks.length - 1}%%`;
  });
  md = md.replace(/\$([^$\n]+?)\$/g, (_, m) => {
    mathBlocks.push(`$${m}$`);
    return `%%MATH_INLINE_${mathBlocks.length - 1}%%`;
  });

  // Code blocks (fenced)
  md = md.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    const escaped = code.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return `<pre class="code-block"><code class="lang-${lang || 'text'}">${escaped}</code></pre>`;
  });

  // Inline code
  md = md.replace(/`([^`\n]+)`/g, '<code>$1</code>');

  // Headings
  md = md.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
  md = md.replace(/^### (.+)$/gm,  '<h3>$1</h3>');
  md = md.replace(/^## (.+)$/gm,   '<h2>$1</h2>');
  md = md.replace(/^# (.+)$/gm,    '<h1>$1</h1>');

  // HR
  md = md.replace(/^---+$/gm, '<hr />');

  // Bold and italic
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

// ============================
//  Loading & Error States
// ============================
function showLoading(show) {
  loadingOverlay.style.display = show ? 'flex' : 'none';
  solveBtn.disabled = show;
}

function setLoadingStep(msg) {
  loadingStep.textContent = msg;
}

function showError(msg) {
  resultsSection.style.display = 'block';
  resultsBody.innerHTML = `
    <div style="padding:1.5rem; background: rgba(255, 77, 109, 0.08); border: 1px solid rgba(255,77,109,0.3); border-radius: 12px; color: #ff4d6d;">
      <strong>⚠️ Error:</strong> ${msg}
      <br/><br/>
      <small>If using the API for the first time, make sure your <code>GEMINI_API_KEY</code> is set in the <code>.env</code> file and the Flask server is running.</small>
    </div>`;
  showLoading(false);
}

// ============================
//  Copy & Clear
// ============================
copyBtn.addEventListener('click', () => {
  const text = resultsBody.innerText;
  navigator.clipboard.writeText(text).then(() => {
    copyBtn.textContent = '✅ Copied!';
    setTimeout(() => copyBtn.textContent = '📋 Copy', 2000);
  });
});

clearBtn.addEventListener('click', () => {
  resultsSection.style.display = 'none';
  resultsBody.innerHTML = '';
});
