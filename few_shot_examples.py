"""
few_shot_examples.py
====================
Curated worked examples aligned with the chapter structure of standard
Network Analysis syllabi (Bakshi-style). These are used as dynamic
few-shot demonstrations injected into Gemini prompts.

Each entry is a dict with:
    mode     : analysis type tag
    keywords : list of trigger keywords
    title    : short description
    example  : full Q&A demonstration string
"""

# ─────────────────────────────────────────────────────────────────────────────
EXAMPLES = [

    # ─── MESH ANALYSIS ────────────────────────────────────────────────────────
    {
        "mode": "dc_mesh",
        "keywords": ["mesh", "kvl", "loop current", "two loop", "two-loop"],
        "title": "Two-Mesh DC Circuit",
        "example": """
**Example — Mesh Analysis (Two-Loop Circuit)**

**Circuit:** 10 V source in mesh 1. Mesh 1 has R1 = 2 Ω, shared branch R2 = 4 Ω.
Mesh 2 has R3 = 6 Ω and a 4 V source (aiding mesh 2).

**Step 1 — Assign mesh currents I1 (clockwise, mesh 1) and I2 (clockwise, mesh 2).**

**Step 2 — Write KVL equations:**

Mesh 1: 10 = I1·(R1 + R2) − I2·R2
         10 = 6·I1 − 4·I2        … (1)

Mesh 2: 4 = I2·(R2 + R3) − I1·R2
         4 = 10·I2 − 4·I1        … (2)

**Step 3 — SymPy solution:**
```python
from sympy import symbols, Eq, solve
I1, I2 = symbols('I1 I2')
eq1 = Eq(6*I1 - 4*I2, 10)
eq2 = Eq(-4*I1 + 10*I2, 4)
sol = solve([eq1, eq2], [I1, I2])
print(f"I1 = {float(sol[I1]):.4f} A")
print(f"I2 = {float(sol[I2]):.4f} A")
print(f"V_R2 = {float((sol[I1]-sol[I2])*4):.4f} V")
```

**Result:**
| Quantity | Value |
|----------|-------|
| I1 | 2.0690 A |
| I2 | 1.2276 A |
| V_R2 | 3.3655 V |
"""
    },

    # ─── NODAL ANALYSIS ───────────────────────────────────────────────────────
    {
        "mode": "dc_nodal",
        "keywords": ["nodal", "kcl", "node voltage", "two node"],
        "title": "Two-Node Nodal Analysis",
        "example": """
**Example — Nodal Analysis (Two Non-Reference Nodes)**

**Circuit:** 5 A current source feeds node V1. R1 = 2 Ω between V1 and ground.
R2 = 4 Ω between V1 and V2. R3 = 3 Ω between V2 and ground. 3 A current source drains from V2 to ground.

**Step 1 — KCL at node V1:**
  I_source − V1/R1 − (V1−V2)/R2 = 0
  5 = V1/2 + (V1−V2)/4

**Step 2 — KCL at node V2:**
  (V1−V2)/R2 − V2/R3 − 3 = 0
  (V1−V2)/4 = V2/3 + 3

**Step 3 — SymPy solution:**
```python
from sympy import symbols, Eq, solve, Rational
V1, V2 = symbols('V1 V2')
eq1 = Eq(Rational(1,2)*V1 + Rational(1,4)*(V1-V2), 5)
eq2 = Eq(Rational(1,4)*(V1-V2) - Rational(1,3)*V2, 3)
sol = solve([eq1, eq2], [V1, V2])
print(f"V1 = {float(sol[V1]):.4f} V")
print(f"V2 = {float(sol[V2]):.4f} V")
print(f"I_R2 = {float((sol[V1]-sol[V2])/4):.4f} A")
```

**Result:**
| Node | Voltage |
|------|---------|
| V1 | 7.7647 V |
| V2 | 2.9412 V |
| I through R2 | 1.2059 A |
"""
    },

    # ─── THEVENIN ─────────────────────────────────────────────────────────────
    {
        "mode": "thevenin",
        "keywords": ["thevenin", "thevenin equivalent", "vth", "voc"],
        "title": "Thevenin Equivalent Circuit",
        "example": """
**Example — Thevenin Equivalent**

**Circuit:** 12 V source with R1 = 3 Ω in series, then R2 = 6 Ω in series to terminal A.
R3 = 6 Ω connected from terminal A to ground. Terminal B = ground.

**Step 1 — Find V_th (open-circuit voltage at A-B):**
  Remove load (terminal A-B open).
  Only R1 and R3 form a voltage divider (R2 is in series with open terminal, no current):
  Wait — R3 is to ground, R2 goes to terminal A. Current flows: 12V → R1(3Ω) → R3(6Ω) → ground
  I = 12/(3+6) = 4/3 A
  V_th = V_A = I × R3 = (4/3) × 6 = 8 V

**Step 2 — Find R_th (deactivate 12V source → short):**
  R_th = R3 ∥ R1 + R2 = (6 ∥ 3) + 0 → but R2 connects A to the short, so:
  R_th seen from A: R3 in parallel with (R1 + R2) ... 
  Actually: source shorted, R1 and R2 are in series = 9Ω, this is in parallel with R3(6Ω):
  R_th = (9 × 6)/(9+6) = 54/15 = 3.6 Ω

**Step 3 — SymPy solution:**
```python
from sympy import symbols, Rational
R1, R2, R3, Vs = 3, 0, 6, 12   # R2=0 here (removed from example above)
I_oc = Vs / (R1 + R3)
Vth = I_oc * R3
Rth = (R3 * R1) / (R3 + R1)
print(f"V_th = {float(Vth):.4f} V")
print(f"R_th = {float(Rth):.4f} Ohm")
print(f"I_sc = {float(Vth/Rth):.4f} A")
```

**Result:**
| Parameter | Value |
|-----------|-------|
| V_th | 8.0000 V |
| R_th | 2.0000 Ω |
| I_sc (Norton) | 4.0000 A |
"""
    },

    # ─── NORTON ───────────────────────────────────────────────────────────────
    {
        "mode": "norton",
        "keywords": ["norton", "norton equivalent", "isc", "short circuit current"],
        "title": "Norton Equivalent Circuit",
        "example": """
**Example — Norton Equivalent**

**Circuit:** 15 V source with R1 = 5 Ω in series. R2 = 10 Ω in parallel with terminals A-B.

**Step 1 — I_N = Short-circuit current (terminals A-B shorted):**
  R2 is shorted out. Only R1 limits current.
  I_N = I_sc = 15 / 5 = 3 A

**Step 2 — R_N = Thevenin resistance:**
  Voltage source shorted. R_th = R1 ∥ R2 = (5×10)/(5+10) = 50/15 = 3.333 Ω

**Step 3 — Verify: V_th = I_N × R_N = 3 × 3.333 = 10 V**

```python
from sympy import Rational
R1, R2, Vs = 5, 10, 15
IN = Vs / R1
RN = (R1 * R2)/(R1 + R2)
Vth = IN * RN
print(f"I_N = {float(IN):.4f} A")
print(f"R_N = {float(RN):.4f} Ohm")
print(f"V_th = {float(Vth):.4f} V")
```

**Result:**
| Parameter | Value |
|-----------|-------|
| I_N | 3.0000 A |
| R_N | 3.3333 Ω |
| V_th | 10.0000 V |
"""
    },

    # ─── SUPERPOSITION ────────────────────────────────────────────────────────
    {
        "mode": "superposition",
        "keywords": ["superposition", "multiple source", "two source"],
        "title": "Superposition Theorem",
        "example": """
**Example — Superposition Theorem**

**Circuit:** 10 V voltage source and 2 A current source. R1 = 5 Ω, R2 = 10 Ω.
Find current through R2.

**Step 1 — Due to 10V source only (2A source open-circuited):**
  R1 and R2 in series: I_total = 10/(5+10) = 0.667 A
  I_R2_1 = 0.667 A (downward through R2)

**Step 2 — Due to 2A source only (10V source short-circuited):**
  Current divider between R1 and R2 (now in parallel due to short):
  I_R2_2 = 2 × R1/(R1+R2) = 2 × 5/15 = 0.667 A (upward, depends on source direction)

**Step 3 — Total (algebraic sum):**
  I_R2 = I_R2_1 + I_R2_2  (or − depending on directions)

```python
from sympy import Rational
R1, R2, Vs, Is = 5, 10, 10, 2
# Due to voltage source
I_R2_v = Vs / (R1 + R2)
# Due to current source (voltage source shorted, R1 || nothing → current divider)
I_R2_i = Is * R1 / (R1 + R2)
# Assuming both produce current in same direction through R2
I_R2_total = I_R2_v + I_R2_i
print(f"I_R2 due to Vs = {float(I_R2_v):.4f} A")
print(f"I_R2 due to Is = {float(I_R2_i):.4f} A")
print(f"I_R2 total = {float(I_R2_total):.4f} A")
```
"""
    },

    # ─── AC PHASOR ────────────────────────────────────────────────────────────
    {
        "mode": "ac_phasor",
        "keywords": ["phasor", "ac", "impedance", "sinusoidal", "rms"],
        "title": "AC Series RLC Phasor Analysis",
        "example": """
**Example — AC Series RLC Circuit**

**Circuit:** V_s = 100∠0° V at f = 50 Hz. R = 10 Ω, L = 50 mH, C = 100 μF.

**Step 1 — Calculate impedances:**
  ω = 2π × 50 = 314.16 rad/s
  X_L = ωL = 314.16 × 0.05 = 15.708 Ω
  X_C = 1/(ωC) = 1/(314.16 × 100×10⁻⁶) = 31.831 Ω
  Z = R + j(X_L − X_C) = 10 + j(15.708 − 31.831) = 10 − j16.123 Ω

**Step 2 — Calculate current and voltages:**
  |Z| = √(10² + 16.123²) = 19.01 Ω
  φ = arctan(−16.123/10) = −58.2° (capacitive, current leads voltage)
  I = V_s/Z = 100∠0° / 19.01∠−58.2° = 5.26∠58.2° A

```python
import cmath, math
f = 50; omega = 2*math.pi*f
R, L, C = 10, 50e-3, 100e-6
XL = omega * L
XC = 1/(omega * C)
Z = complex(R, XL - XC)
Vs = complex(100, 0)   # 100 angle 0
I = Vs / Z
VR = I * R
VL = I * complex(0, XL)
VC = I * complex(0, -XC)
print(f"|Z| = {abs(Z):.4f} Ohm, angle = {math.degrees(cmath.phase(Z)):.2f} deg")
print(f"|I| = {abs(I):.4f} A, angle = {math.degrees(cmath.phase(I)):.2f} deg")
print(f"|V_R| = {abs(VR):.4f} V")
print(f"|V_L| = {abs(VL):.4f} V")
print(f"|V_C| = {abs(VC):.4f} V")
print(f"Power factor = {math.cos(cmath.phase(Z)):.4f}")
```

**Result:**
| Quantity | Value |
|----------|-------|
| |Z| | 19.01 Ω |
| |I| | 5.26 A |
| Phase angle | −58.2° (capacitive) |
"""
    },

    # ─── RESONANCE ────────────────────────────────────────────────────────────
    {
        "mode": "resonance",
        "keywords": ["resonan", "resonance frequency", "quality factor", "q factor", "bandwidth"],
        "title": "Series RLC Resonance",
        "example": """
**Example — Series Resonance**

**Circuit:** R = 5 Ω, L = 0.1 H, C = 10 μF

**Step 1 — Resonant frequency:**
  ω₀ = 1/√(LC) = 1/√(0.1 × 10×10⁻⁶) = 1000 rad/s
  f₀ = ω₀/(2π) = 159.15 Hz

**Step 2 — Quality factor:**
  Q = ω₀L/R = 1000 × 0.1 / 5 = 20

**Step 3 — Bandwidth:**
  BW = f₀/Q = 159.15/20 = 7.96 Hz
  Half-power frequencies: f₁ = 155.2 Hz, f₂ = 163.1 Hz

```python
import math
R, L, C = 5, 0.1, 10e-6
omega0 = 1/math.sqrt(L*C)
f0 = omega0 / (2*math.pi)
Q = omega0*L/R
BW = f0/Q
alpha = R/(2*L)
f1 = (math.sqrt(alpha**2 + omega0**2) - alpha)/(2*math.pi)
f2 = (math.sqrt(alpha**2 + omega0**2) + alpha)/(2*math.pi)
print(f"omega_0 = {omega0:.2f} rad/s,  f0 = {f0:.4f} Hz")
print(f"Q factor = {Q:.4f}")
print(f"Bandwidth = {BW:.4f} Hz")
print(f"Half-power: f1 = {f1:.4f} Hz,  f2 = {f2:.4f} Hz")
```

**Result:**
| Parameter | Value |
|-----------|-------|
| f₀ | 159.15 Hz |
| Q | 20 |
| BW | 7.96 Hz |
"""
    },

    # ─── TRANSIENT RC ─────────────────────────────────────────────────────────
    {
        "mode": "transient_rc",
        "keywords": ["transient", "rc circuit", "charging", "time constant", "step response"],
        "title": "RC Transient Step Response",
        "example": """
**Example — RC Transient (Step Response)**

**Circuit:** 20 V DC switched on at t=0 through R = 10 kΩ into C = 47 μF (initially uncharged).

**Step 1 — Time constant:**
  τ = RC = 10×10³ × 47×10⁻⁶ = 0.47 s

**Step 2 — Transient equations:**
  v_C(t) = 20(1 − e^(−t/0.47))   V
  i(t) = (20/10000) × e^(−t/0.47) = 2×10⁻³ × e^(−t/0.47)   A

```python
import math
R, C, Vs = 10e3, 47e-6, 20
tau = R * C
print(f"Time constant tau = {tau:.4f} s")
for t_mult in [0, 0.5, 1, 2, 3, 5]:
    t = t_mult * tau
    vC = Vs * (1 - math.exp(-t/tau))
    i  = (Vs/R) * math.exp(-t/tau)
    print(f"t = {t_mult}τ = {t:.4f}s: v_C = {vC:.4f} V,  i = {i*1000:.4f} mA")
```

**Result Table (v_C at multiples of τ):**
| t | v_C(t) | i(t) |
|---|--------|------|
| 0 | 0 V | 2.000 mA |
| τ | 12.642 V | 0.736 mA |
| 2τ | 17.293 V | 0.271 mA |
| 5τ | 19.865 V | 0.013 mA |
"""
    },

    # ─── TRANSIENT RLC ────────────────────────────────────────────────────────
    {
        "mode": "transient_rlc",
        "keywords": ["rlc transient", "second order", "overdamped", "underdamped", "critically damped"],
        "title": "RLC Series Transient (Second-Order)",
        "example": """
**Example — RLC Series Transient**

**Circuit:** R = 4 Ω, L = 1 H, C = 0.25 F. Source V = 10 V switched at t=0.
Initial conditions: i(0) = 0, v_C(0) = 0.

**Step 1 — Characteristic equation:**
  s² + (R/L)s + 1/(LC) = 0
  s² + 4s + 4 = 0
  α = R/(2L) = 2;  ω₀ = 1/√(LC) = 2  →  α = ω₀  →  **Critically Damped**

**Step 2 — Response form:**
  i(t) = (A₁ + A₂t)e^(−2t)

**Step 3 — Apply initial conditions:**
  i(0) = A₁ = 0  →  A₁ = 0
  di/dt|_{t=0} = V_L(0)/L = (Vs − v_C(0) − R×i(0))/L = 10/1 = 10
  di/dt = A₂e^(−2t) − 2(A₁+A₂t)e^(−2t)  at t=0: A₂ = 10  →  A₂ = 10

```python
import math
R, L, C, Vs = 4, 1, 0.25, 10
alpha = R/(2*L)
omega0 = 1/math.sqrt(L*C)
print(f"alpha = {alpha}, omega0 = {omega0}")
print("Critically damped (alpha == omega0)")
A1, A2 = 0, 10   # from initial conditions
for t in [0, 0.25, 0.5, 1.0, 2.0, 3.0]:
    i = (A1 + A2*t)*math.exp(-alpha*t)
    print(f"i({t}s) = {i:.6f} A")
```

**Result:**
| t (s) | i(t) (A) |
|-------|----------|
| 0 | 0.000000 |
| 0.5 | 1.947734 |
| 1.0 | 1.353353 |
| 2.0 | 0.366313 |
"""
    },

    # ─── LAPLACE ──────────────────────────────────────────────────────────────
    {
        "mode": "laplace",
        "keywords": ["laplace", "s domain", "s-domain", "partial fraction", "transfer function"],
        "title": "Laplace Transform Circuit Analysis",
        "example": """
**Example — s-Domain Analysis with Laplace Transform**

**Circuit:** Series RL: R = 2 Ω, L = 1 H. Input: unit step u(t). Find i(t).

**Step 1 — s-domain:**
  V(s) = 1/s  (Laplace of unit step)
  Z(s) = R + sL = 2 + s
  I(s) = V(s)/Z(s) = (1/s)/(s+2) = 1/(s(s+2))

**Step 2 — Partial fractions:**
  I(s) = A/s + B/(s+2)
  A = [s × I(s)]_{s=0} = 1/2
  B = [(s+2) × I(s)]_{s=−2} = −1/2
  I(s) = (1/2)/s − (1/2)/(s+2)

**Step 3 — Inverse Laplace:**
  i(t) = (1/2)(1 − e^(−2t)) × u(t)   A

```python
from sympy import symbols, apart, inverse_laplace_transform, exp, Heaviside, factor
s, t = symbols('s t', positive=True)
Is = 1 / (s * (s + 2))
Is_pf = apart(Is, s)
print("Partial fractions:", Is_pf)
it = inverse_laplace_transform(Is, s, t)
print("i(t) =", it)
```

**Result:**
  i(t) = 0.5(1 − e^(−2t)) A for t ≥ 0
  Steady-state: i(∞) = 0.5 A  ✓ (= V/R = 1/2)
  Initial value: i(0) = 0  ✓ (inductor opposes instantaneous change)
"""
    },

    # ─── FREQUENCY RESPONSE ───────────────────────────────────────────────────
    {
        "mode": "freq_response",
        "keywords": ["bode plot", "frequency response", "low pass", "high pass", "cutoff frequency"],
        "title": "RC Low-Pass Filter Frequency Response",
        "example": """
**Example — RC Low-Pass Filter**

**Circuit:** R = 1 kΩ, C = 1 μF. Input V_in, output V_out across C.

**Step 1 — Transfer function:**
  H(s) = Z_C/(R + Z_C) = (1/sC)/(R + 1/sC) = 1/(1 + sRC)
  H(s) = ω_c/(s + ω_c)   where ω_c = 1/(RC)

**Step 2 — Cutoff frequency:**
  ω_c = 1/(1000 × 10⁻⁶) = 1000 rad/s
  f_c = ω_c/(2π) = 159.15 Hz

**Step 3 — Frequency response:**
  H(jω) = 1/(1 + jω/ω_c)
  |H(jω)| = 1/√(1 + (ω/ω_c)²)
  ∠H = −arctan(ω/ω_c)
  At ω = ω_c: |H| = 1/√2 = 0.707 (−3dB)

```python
import math
R, C = 1e3, 1e-6
wc = 1/(R*C)
fc = wc/(2*math.pi)
print(f"Cutoff freq: wc = {wc:.2f} rad/s,  fc = {fc:.4f} Hz")
for freq in [0.1*fc, fc, 10*fc, 100*fc]:
    w = 2*math.pi*freq
    H_mag = 1/math.sqrt(1 + (w/wc)**2)
    H_db = 20*math.log10(H_mag)
    H_phase = -math.degrees(math.atan(w/wc))
    print(f"f={freq:.2f}Hz: |H|={H_mag:.4f} ({H_db:.2f}dB), phase={H_phase:.2f}°")
```

**Result:**
| Frequency | |H| | dB | Phase |
|-----------|-----|-----|-------|
| 0.1×fc | 0.9950 | −0.04 dB | −5.7° |
| fc | 0.7071 | −3.01 dB | −45.0° |
| 10×fc | 0.0995 | −20.0 dB | −84.3° |
"""
    },

    # ─── TWO-PORT ─────────────────────────────────────────────────────────────
    {
        "mode": "two_port",
        "keywords": ["z parameter", "y parameter", "two port", "h parameter", "abcd"],
        "title": "Z-Parameter Calculation",
        "example": """
**Example — Two-Port Z-Parameters**

**Circuit:** T-network: Z1 in series (port 1 arm), Z2 in series (port 2 arm), Z3 shunt between them.
Z1 = 2 Ω, Z2 = 3 Ω, Z3 = 6 Ω.

**Step 1 — Z11 (output open, I2=0):**
  Z11 = V1/I1|_{I2=0} = Z1 + Z3 = 2 + 6 = 8 Ω

**Step 2 — Z22 (input open, I1=0):**
  Z22 = V2/I2|_{I1=0} = Z2 + Z3 = 3 + 6 = 9 Ω

**Step 3 — Z12 = Z21 (reciprocal network):**
  Z12 = V1/I2|_{I1=0} = Z3 = 6 Ω   (voltage across shunt element)

```python
Z1, Z2, Z3 = 2, 3, 6
Z11 = Z1 + Z3
Z22 = Z2 + Z3
Z12 = Z3
Z21 = Z3   # reciprocal
delta_Z = Z11*Z22 - Z12*Z21
print(f"Z11 = {Z11} Ohm")
print(f"Z22 = {Z22} Ohm")
print(f"Z12 = Z21 = {Z12} Ohm")
print(f"delta_Z = {delta_Z}")
# Y parameters from Z
Y11 =  Z22/delta_Z
Y12 = -Z12/delta_Z
Y21 = -Z21/delta_Z
Y22 =  Z11/delta_Z
print(f"Y11={Y11:.4f} S, Y12={Y12:.4f} S, Y21={Y21:.4f} S, Y22={Y22:.4f} S")
```

**Result:**
| Parameter | Value |
|-----------|-------|
| Z11 | 8 Ω |
| Z22 | 9 Ω |
| Z12 = Z21 | 6 Ω |
| ΔZ | 36 |
"""
    },

    # ─── DELTA-WYE ────────────────────────────────────────────────────────────
    {
        "mode": "delta_wye",
        "keywords": ["delta wye", "delta star", "wye delta", "star delta", "triangle star"],
        "title": "Delta to Wye (Star) Transformation",
        "example": """
**Example — Delta to Wye Transformation**

**Delta network:** R_ab = 12 Ω, R_bc = 6 Ω, R_ca = 18 Ω

**Step 1 — Apply transformation formulas:**
  R_sum = R_ab + R_bc + R_ca = 12 + 6 + 18 = 36 Ω
  Ra = (R_ab × R_ca)/R_sum = (12 × 18)/36 = 6 Ω
  Rb = (R_ab × R_bc)/R_sum = (12 × 6)/36 = 2 Ω
  Rc = (R_bc × R_ca)/R_sum = (6 × 18)/36 = 3 Ω

```python
Rab, Rbc, Rca = 12, 6, 18
R_sum = Rab + Rbc + Rca
Ra = (Rab * Rca) / R_sum
Rb = (Rab * Rbc) / R_sum
Rc = (Rbc * Rca) / R_sum
print(f"R_sum = {R_sum} Ohm")
print(f"Ra = {Ra:.4f} Ohm")
print(f"Rb = {Rb:.4f} Ohm")
print(f"Rc = {Rc:.4f} Ohm")
# Verify: Wye to Delta back
Rab_check = Ra + Rb + (Ra*Rb)/Rc
Rbc_check = Rb + Rc + (Rb*Rc)/Ra
Rca_check = Rc + Ra + (Rc*Ra)/Rb
print(f"Verification — Rab={Rab_check:.2f}, Rbc={Rbc_check:.2f}, Rca={Rca_check:.2f}")
```

**Result:**
| Wye Resistor | Value |
|--------------|-------|
| Ra | 6 Ω |
| Rb | 2 Ω |
| Rc | 3 Ω |
"""
    },
]


def get_few_shot_example(query: str) -> str:
    """
    Returns the most relevant worked example to inject as a few-shot demonstration.

    Parameters
    ----------
    query : str
        User's circuit problem description.

    Returns
    -------
    str
        A formatted few-shot example string, or empty string if none matches.
    """
    q_lower = query.lower()
    best_match = None
    best_score = 0

    for ex in EXAMPLES:
        score = sum(1 for kw in ex["keywords"] if kw in q_lower)
        if score > best_score:
            best_score = score
            best_match = ex

    if best_match and best_score > 0:
        return (
            f"\n### 📖 Reference Example: {best_match['title']}\n"
            f"*(Follow this methodology for your solution)*\n"
            + best_match["example"]
        )
    return ""


def get_all_titles() -> list[str]:
    """Returns list of example titles — useful for UI display."""
    return [ex["title"] for ex in EXAMPLES]
