import os
import base64
import json
import traceback
import re
import sys
import socket
import subprocess
import threading
import time
from io import StringIO
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google import genai
from google.genai import types
from dotenv import load_dotenv
import sympy

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)
else:
    print("WARNING: GEMINI_API_KEY not set. Please create a .env file with GEMINI_API_KEY=your_key")

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Model fallback chain -- tries in order when quota is exceeded
MODELS = [
    "gemini-2.0-flash",           # Primary: fast, cheap, vision-capable
    "gemini-2.0-flash-lite",      # Fallback 1: even cheaper
    "gemini-2.5-flash",           # Fallback 2: more capable
    "gemini-2.5-pro",             # Fallback 3: most capable
    "gemini-flash-latest",        # Fallback 4: alias
]

def call_gemini(contents, system_instruction=None, temperature=0.2, max_tokens=8192):
    """Call Gemini with automatic model fallback on quota errors."""
    config_kwargs = {"temperature": temperature, "max_output_tokens": max_tokens}
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction

    last_error = None
    for model in MODELS:
        try:
            resp = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(**config_kwargs)
            )
            return resp, model
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                last_error = e
                continue
            raise
    raise last_error

# ===== SYSTEM PROMPT =====
SYSTEM_PROMPT = """You are an expert electrical engineering AI assistant specializing in network analysis. 
Your capabilities include solving circuits using:
- Mesh Analysis (Kirchhoff's Voltage Law)
- Nodal Analysis (Kirchhoff's Current Law)
- Superposition Theorem
- Thevenin's Theorem
- Norton's Theorem
- Maximum Power Transfer Theorem
- Source Transformation
- Delta-Wye (Delta-Star) Transformation

When given a circuit (as an image or text description), you must:

1. **IDENTIFY** all components: resistors, voltage sources, current sources, capacitors, inductors, dependent/independent sources.
2. **DESCRIBE** the circuit topology clearly (node labeling, mesh definition if applicable).
3. **CHOOSE** the most appropriate analysis method.
4. **SHOW** all steps mathematically using LaTeX notation (wrap inline math in $...$ and block equations in $$...$$).
5. **SOLVE** by generating exact Python/SymPy code wrapped in ```python\n...\n``` code blocks. The code MUST:
   - Use `sympy` to define symbols and solve ALL equations algebraically
   - Print ALL final results with labels (e.g., `print(f"I1 = {float(I1_val):.4f} A")`)
   - Be complete and runnable without any edits
6. **SUMMARIZE** the final answers in a neat markdown table at the end.

**CRITICAL RULES:**
- ALWAYS generate SymPy solving code. Never just state the answer without computing it via sympy.
- Wrap LaTeX equations in $...$ for inline or $$...$$ for block equations.
- For image inputs: first carefully describe every component and connection you see, then proceed to analysis.
- For Superposition: solve for each independent source individually, then superimpose (add) the results.
- For Thevenin/Norton: clearly identify V_oc (open circuit voltage), then find R_th (deactivate independent sources).
- Be extremely precise and methodical. Show all KVL/KCL equations before solving.
"""

# ============================
#  SymPy Code Execution Sandbox
# ============================
def run_sympy_code(code: str) -> dict:
    """Safely execute SymPy code and return results."""
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
    }
    exec_globals = {"__builtins__": safe_builtins}

    try:
        full_code = "from sympy import *\nimport sympy\n" + code
        exec(full_code, exec_globals)
        result["success"] = True
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}"
    finally:
        sys.stdout = old_stdout
        result["output"] = buffer.getvalue()

    return result


# ============================
#  Routes
# ============================
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "api_key_set": bool(api_key)})


@app.route('/analyze', methods=['POST'])
def analyze():
    """Main endpoint: accepts text query and/or an image."""
    if not client:
        return jsonify({"error": "GEMINI_API_KEY not configured. Add it to the .env file."}), 500

    query = request.form.get('query', '').strip()
    image_file = request.files.get('image')

    if not query and not image_file:
        return jsonify({"error": "Please provide either a text query or an image."}), 400

    try:
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
                    "Generate the SymPy solving code."
                )

        content_parts.append(query)

        response, model_used = call_gemini(
            contents=content_parts,
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=8192,
        )
        initial_analysis = response.text

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

        final_response = initial_analysis
        computed_block = ""

        if computed_outputs:
            computed_block = "## Computed Results\n\n"
            for i, res in enumerate(execution_results):
                computed_block += f"**Code Block {i+1} Output:**\n"
                if res["success"] and res["output"]:
                    computed_block += f"```\n{res['output'].strip()}\n```\n\n"
                elif res["error"]:
                    computed_block += f"```\nError: {res['error']}\n```\n\n"

            summary_prompt = (
                f"Original question: {query}\n\n"
                f"The SymPy solver computed these exact values:\n"
                + "\n".join(computed_outputs) +
                "\n\nNow provide a **clean final summary** with:\n"
                "1. A brief circuit description.\n"
                "2. The key equations used (LaTeX $...$ and $$...$$).\n"
                "3. A final answers table (markdown table).\n"
                "Do NOT include Python code blocks. Be concise."
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
                + "\n## Final Summary\n\n"
                + summary_resp.text
            )

        return jsonify({
            "success": True,
            "analysis": final_response,
            "model_used": model_used,
            "code_executed": len(execution_results) > 0,
            "execution_results": [
                {"success": r["success"], "output": r["output"], "error": r["error"]}
                for r in execution_results
            ]
        })

    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


# ============================
#  Public Tunnel (localhost.run via SSH)
# ============================
public_url_global = None

def start_localhost_run_tunnel(port):
    """Start a free public tunnel via localhost.run (no account needed)."""
    global public_url_global
    try:
        proc = subprocess.Popen(
            ["ssh", "-o", "StrictHostKeyChecking=no",
             "-o", "ServerAliveInterval=60",
             "-R", f"80:localhost:{port}",
             "nokey@localhost.run"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for line in proc.stdout:
            line = line.strip()
            if "https://" in line:
                for token in line.split():
                    t = token.rstrip(",.")
                    if t.startswith("https://"):
                        public_url_global = t
                        print(f"\n  [PUBLIC URL] Anyone can access: {public_url_global}\n")
                        break
                if public_url_global:
                    break
    except FileNotFoundError:
        print("  [tunnel] OpenSSH not found. Install it or use ngrok manually.")
    except Exception as e:
        print(f"  [tunnel] Error: {e}")


if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
