import os
import base64
import json
import traceback
import re
import sys
import cmath
import math
import socket
import threading
import time
import functools
from io import StringIO
from flask import Flask, request, jsonify, send_from_directory, Response, session, redirect, url_for
from flask_cors import CORS
from google import genai
from google.genai import types
from dotenv import load_dotenv
import sympy

from knowledge_base import get_relevant_context, get_full_compendium
from few_shot_examples import get_few_shot_example, get_all_titles

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'circuitmind-dev-secret-2024')
CORS(app, supports_credentials=True)

# ─── Gemini Client ───────────────────────────────────────────────────────────
api_key = os.environ.get("GEMINI_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)
else:
    print("WARNING: GEMINI_API_KEY not set.")

# ─── Auth Config ─────────────────────────────────────────────────────────────
APP_PIN = os.environ.get("APP_PIN", "")

def login_required(f):
    """Decorator: redirect to /login if not authenticated (when PIN is set)."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if APP_PIN and not session.get('authenticated'):
            # API calls: return 401 JSON
            if request.path.startswith('/analyze') or request.is_json or \
               request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"error": "Unauthorized. Please log in.", "auth_required": True}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory session history (last 20 queries)
_history: list[dict] = []

# ─── Model Fallback Chain ─────────────────────────────────────────────────────
MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
]

# Transient error signals that should trigger a model fallback
_RETRYABLE = (
    "429", "500", "503",
    "RESOURCE_EXHAUSTED", "UNAVAILABLE", "INTERNAL",
    "quota", "overloaded", "capacity", "high demand",
    "try again", "server error",
)

def call_gemini(contents, system_instruction=None, temperature=0.2, max_tokens=8192):
    """Call Gemini with automatic model fallback on quota/server errors."""
    config_kwargs = {"temperature": temperature, "max_output_tokens": max_tokens}
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction

    last_error = None
    for i, model in enumerate(MODELS):
        try:
            resp = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(**config_kwargs)
            )
            return resp, model
        except Exception as e:
            err_str = str(e).lower()
            if any(signal.lower() in err_str for signal in _RETRYABLE):
                last_error = e
                print(f"[fallback] {model} failed ({type(e).__name__}), trying next model...")
                if i < len(MODELS) - 1:
                    time.sleep(1.5)  # brief pause before next attempt
                continue
            raise
    raise last_error


# ─── Master System Prompt ─────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are **CircuitMind AI** — an expert Electrical & Electronics Engineering (EEE) assistant specializing in Network Analysis, modeled after the rigorous problem-solving approach of standard Indian university EEE syllabi (Bakshi-style curriculum).

## Your Domain Expertise

You can fully solve problems across ALL these areas:

### DC Circuit Analysis
- Ohm's Law, KVL, KCL, series/parallel reductions
- **Mesh Analysis** (including supermesh for current source branches)
- **Nodal Analysis** (including supernode for voltage source branches)
- Source Transformation (voltage↔current source equivalents)
- **Network Theorems**: Thevenin, Norton, Superposition, Maximum Power Transfer, Millman's, Reciprocity
- **Delta ↔ Wye (Star)** transformations

### AC Circuit Analysis
- Phasor representation, impedance (Z_R, Z_L=jωL, Z_C=1/jωC)
- Series and parallel RLC circuits
- Power: real (P), reactive (Q), apparent (S), power factor (cosφ)
- AC mesh/nodal analysis with complex arithmetic

### Resonance
- Series resonance: ω₀ = 1/√(LC), Q factor, bandwidth
- Parallel resonance, selectivity, half-power frequencies

### Transient Analysis (Time Domain)
- **First-order**: RC (τ=RC) and RL (τ=L/R) step responses
- **Second-order RLC**: overdamped / critically damped / underdamped classification
- Initial conditions (inductor current continuity, capacitor voltage continuity)
- Natural + forced response decomposition

### Laplace Transform & s-Domain
- Circuit element models in s-domain: Z_L=sL, Z_C=1/(sC)
- Transfer functions H(s) = Output/Input
- Partial fraction expansion and inverse Laplace transform
- Initial/Final Value Theorems
- Poles, zeros, stability

### Frequency Response & Bode Plots
- H(jω) evaluation, magnitude (dB) and phase plots
- RC/RL/RLC filter responses; cutoff frequencies
- Asymptotic Bode approximations

### Two-Port Networks
- Z, Y, h, ABCD parameters — definition and calculation
- Parameter conversions (Z↔Y via matrix inversion)
- Interconnections: series (Z-add), parallel (Y-add), cascade (ABCD-multiply)

### Coupled Circuits
- Mutual inductance M = k√(L1·L2), dot convention
- Series-aiding vs. series-opposing
- Reflected impedance in transformers

---

## Mandatory Solution Format

For EVERY problem you must follow this exact structure:

### 1. IDENTIFY
List all components and their values. For image inputs: describe every component and connection you can see before analysis.

### 2. TOPOLOGY
Describe the circuit structure: number of nodes, meshes, topology type. Label all nodes (V1, V2, …) and/or meshes (I1, I2, …).

### 3. METHOD
State the analysis method chosen and WHY it is optimal for this circuit.

### 4. EQUATIONS
Write ALL governing equations using proper LaTeX:
- Inline math: $...$ 
- Block equations: $$...$$
Show KVL/KCL equations, impedance formulas, system of equations.

### 5. SYMPY CODE
Generate a COMPLETE, RUNNABLE Python/SymPy code block:
```python
# Complete runnable code here
from sympy import *
# ... solve and print ALL results with labels
print(f"I1 = {float(I1_val):.4f} A")
```
Rules for code:
- Always import sympy at top
- For AC/phasor problems: use Python `complex` type or SymPy `I`
- For transient/Laplace: use `sympy.laplace_transform` or explicit IVP solving
- Print ALL intermediate and final results clearly labeled
- Never leave variables unsolved — always call `solve()` or `dsolve()`

### 6. RESULTS TABLE
Present all final answers in a clean markdown table:
| Quantity | Symbol | Value | Unit |
|----------|--------|-------|------|

### 7. VERIFICATION
Always verify using at least one of:
- Power balance (ΣP_delivered = ΣP_absorbed)
- KVL check around a loop
- KCL check at a node
- Initial/final value theorem check

---

## Critical Rules
- NEVER give an answer without SymPy code to compute it
- NEVER approximate when exact symbolic solutions exist
- For image inputs: describe FIRST, then solve
- If the query references a specific textbook method (Bakshi, etc.), follow that exact pedagogy
- Always classify second-order transient responses (overdamped/underdamped/critically damped) before solving
"""


# ─── SymPy Sandbox ────────────────────────────────────────────────────────────
def run_sympy_code(code: str) -> dict:
    """Safely execute SymPy/Python code and return results."""
    code = re.sub(r'```python\s*', '', code)
    code = re.sub(r'```\s*$', '', code, flags=re.MULTILINE)

    old_stdout = sys.stdout
    sys.stdout = buffer = StringIO()

    result = {"success": False, "output": "", "error": ""}

    safe_builtins = {
        "print": print, "float": float, "abs": abs, "round": round,
        "range": range, "len": len, "str": str, "int": int, "list": list,
        "dict": dict, "type": type, "enumerate": enumerate, "zip": zip,
        "map": map, "min": min, "max": max, "sum": sum, "sorted": sorted,
        "True": True, "False": False, "None": None,
        "__import__": __import__,
        "complex": complex, "pow": pow, "tuple": tuple, "set": set,
        "bool": bool, "vars": vars, "getattr": getattr,
    }

    # Try importing numpy and scipy for numerical support
    try:
        import numpy as np_mod
        import scipy.signal as sig_mod
    except ImportError:
        np_mod = None
        sig_mod = None

    exec_globals = {
        "__builtins__": safe_builtins,
        "math": math,
        "cmath": cmath,
    }
    if np_mod:
        exec_globals["np"] = np_mod
        exec_globals["numpy"] = np_mod
    if sig_mod:
        exec_globals["signal"] = sig_mod

    try:
        full_code = (
            "from sympy import *\n"
            "from sympy import symbols, solve, Eq, simplify, factor, expand, "
            "Matrix, laplace_transform, inverse_laplace_transform, "
            "dsolve, Function, Derivative, exp, cos, sin, tan, sqrt, pi, I, "
            "re, im, Abs, arg, conjugate, oo, zoo, nan, diff, integrate, "
            "apart, together, cancel, limit, series\n"
            "import sympy\n"
            "import math\n"
            "import cmath\n"
            + code
        )
        exec(full_code, exec_globals)
        result["success"] = True
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}"
    finally:
        sys.stdout = old_stdout
        result["output"] = buffer.getvalue()

    return result



# ─── Analysis Mode Detector ───────────────────────────────────────────────────
def detect_mode(query: str) -> str:
    """Auto-detect the primary analysis mode from the query text."""
    q = query.lower()
    if any(w in q for w in ["bode", "frequency response", "low-pass", "high-pass", "filter", "cutoff"]):
        return "frequency"
    if any(w in q for w in ["laplace", "s-domain", "s domain", "transfer function", "partial fraction"]):
        return "laplace"
    if any(w in q for w in ["transient", "step response", "time constant", "charging", "discharging",
                             "overdamped", "underdamped", "critically", "rlc transient", "second order"]):
        return "transient"
    if any(w in q for w in ["phasor", "ac circuit", "sinusoidal", "impedance", "admittance",
                             "power factor", "reactive", "resonan", "rms"]):
        return "ac"
    if any(w in q for w in ["two-port", "z-param", "y-param", "h-param", "abcd"]):
        return "two_port"
    if any(w in q for w in ["coupled", "mutual inductance", "transformer", "dot convention"]):
        return "coupled"
    return "dc"


# ─── RAG Context Builder ──────────────────────────────────────────────────────
def build_rag_context(query: str, include_example: bool = True) -> str:
    """Build the RAG context block for the given query."""
    kb_context = get_relevant_context(query)
    if include_example:
        example = get_few_shot_example(query)
        if example:
            return kb_context + "\n\n" + example
    return kb_context


# ─────────────────────────────────────────────────────────────────────────────
#  Auth Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET'])
def login_page():
    if not APP_PIN or session.get('authenticated'):
        return redirect('/')
    return send_from_directory('static', 'login.html')

@app.route('/login', methods=['POST'])
def do_login():
    data = request.get_json(silent=True) or {}
    pin = data.get('pin', '').strip()
    if APP_PIN and pin == APP_PIN:
        session['authenticated'] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Incorrect PIN."}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route('/check-auth', methods=['GET'])
def check_auth():
    if not APP_PIN:
        return jsonify({"authenticated": True, "pin_required": False})
    return jsonify({"authenticated": bool(session.get('authenticated')), "pin_required": True})


# ─────────────────────────────────────────────────────────────────────────────
#  App Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/')
@login_required
def index():
    return send_from_directory('static', 'index.html')


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "api_key_set": bool(api_key),
        "knowledge_base": "bakshi_aligned_v2",
        "examples_loaded": len(get_all_titles()),
        "auth_enabled": bool(APP_PIN),
    })


@app.route('/modes', methods=['GET'])
@login_required
def get_modes():
    """Return available analysis modes for the frontend."""
    return jsonify({
        "modes": [
            {"id": "auto",      "label": "🤖 Auto-Detect",     "desc": "AI picks the best method"},
            {"id": "dc",        "label": "⚡ DC Analysis",      "desc": "KVL, KCL, mesh, nodal, theorems"},
            {"id": "ac",        "label": "〰️ AC / Phasor",     "desc": "Impedance, power, sinusoidal steady-state"},
            {"id": "transient", "label": "📈 Transient",       "desc": "RC, RL, RLC step/impulse response"},
            {"id": "laplace",   "label": "🔁 Laplace / s-Domain","desc": "Transfer functions, s-domain circuit analysis"},
            {"id": "frequency", "label": "📊 Frequency Domain","desc": "Bode plots, filters, cutoff frequencies"},
            {"id": "two_port",  "label": "🔲 Two-Port",        "desc": "Z, Y, h, ABCD parameters"},
        ],
        "examples": get_all_titles(),
    })


@app.route('/history', methods=['GET'])
@login_required
def get_history():
    """Return the last 20 queries from this session."""
    return jsonify({"history": _history[-20:]})


@app.route('/history', methods=['DELETE'])
@login_required
def clear_history():
    """Clear session history."""
    _history.clear()
    return jsonify({"status": "cleared"})


@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    """Main endpoint: accepts text query and/or an image, returns full analysis."""
    if not client:
        return jsonify({"error": "GEMINI_API_KEY not configured. Add it to the .env file."}), 500

    query = request.form.get('query', '').strip()
    mode_override = request.form.get('mode', 'auto').strip()
    image_file = request.files.get('image')

    if not query and not image_file:
        return jsonify({"error": "Please provide either a text query or an image."}), 400

    try:
        # ── Detect analysis mode ──────────────────────────────────────────────
        effective_mode = mode_override if mode_override != 'auto' else detect_mode(query)

        # ── Build RAG context from knowledge base ─────────────────────────────
        rag_context = build_rag_context(query, include_example=True)

        # ── Assemble content parts ────────────────────────────────────────────
        content_parts = []

        if image_file:
            image_bytes = image_file.read()
            mime_type = image_file.mimetype or "image/jpeg"
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            content_parts.append(image_part)
            if not query:
                query = (
                    "Analyze this circuit diagram completely. Identify all components, "
                    "describe the topology, choose the most appropriate analysis method, "
                    "and solve for all node voltages, mesh currents, and any other relevant quantities. "
                    "Generate the SymPy solving code and verify your answer."
                )

        # Inject RAG context before the user query
        augmented_query = (
            f"{rag_context}\n\n"
            f"---\n\n"
            f"**Analysis Mode:** {effective_mode.upper()}\n\n"
            f"**Problem to Solve:**\n{query}"
        )
        content_parts.append(augmented_query)

        # ── Call Gemini ───────────────────────────────────────────────────────
        response, model_used = call_gemini(
            contents=content_parts,
            system_instruction=SYSTEM_PROMPT,
            temperature=0.15,
            max_tokens=8192,
        )
        initial_analysis = response.text

        # ── Execute SymPy code blocks ─────────────────────────────────────────
        code_blocks = re.findall(r'```python(.*?)```', initial_analysis, re.DOTALL)
        execution_results = []
        computed_outputs = []

        for i, code in enumerate(code_blocks):
            exec_result = run_sympy_code(code)
            execution_results.append(exec_result)
            if exec_result["success"] and exec_result["output"]:
                computed_outputs.append(exec_result["output"].strip())
            elif exec_result["error"]:
                computed_outputs.append(f"[Error in block {i+1}]: {exec_result['error']}")

        # ── Build final response ──────────────────────────────────────────────
        final_response = initial_analysis
        computed_block = ""

        if computed_outputs:
            computed_block = "## ✅ Computed Results\n\n"
            for i, res in enumerate(execution_results):
                computed_block += f"**Code Block {i+1} Output:**\n"
                if res["success"] and res["output"]:
                    computed_block += f"```\n{res['output'].strip()}\n```\n\n"
                elif res["error"]:
                    computed_block += f"```\nError: {res['error']}\n```\n\n"

            # Summary pass
            summary_prompt = (
                f"Original problem: {query}\n\n"
                f"Analysis mode: {effective_mode}\n\n"
                f"The SymPy solver computed these exact values:\n"
                + "\n".join(computed_outputs) +
                "\n\nProvide a **clean final summary** with:\n"
                "1. One-sentence circuit description.\n"
                "2. The key equation(s) used (LaTeX $...$ and $$...$$).\n"
                "3. Final answers table (markdown).\n"
                "4. One verification check.\n"
                "Do NOT include Python code. Be concise and precise."
            )
            summary_resp, _ = call_gemini(
                contents=[summary_prompt],
                temperature=0.1,
                max_tokens=2048,
            )
            final_response = (
                initial_analysis
                + "\n\n---\n\n"
                + computed_block
                + "\n## 🎯 Final Summary\n\n"
                + summary_resp.text
            )

        # ── Save to history ───────────────────────────────────────────────────
        _history.append({
            "id": len(_history) + 1,
            "query": query[:120] + ("…" if len(query) > 120 else ""),
            "mode": effective_mode,
            "model": model_used,
            "timestamp": time.strftime("%H:%M:%S"),
            "success": True,
        })

        return jsonify({
            "success": True,
            "analysis": final_response,
            "model_used": model_used,
            "mode_detected": effective_mode,
            "code_executed": len(execution_results) > 0,
            "execution_results": [
                {"success": r["success"], "output": r["output"], "error": r["error"]}
                for r in execution_results
            ],
        })

    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
