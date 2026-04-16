"""
knowledge_base.py
=================
Distilled EEE knowledge base aligned with the standard topics covered in
Network Analysis textbooks (Bakshi-style syllabus: DC circuits, network
theorems, AC phasors, resonance, transient analysis, two-port networks,
Laplace / frequency domain).

All content represents standard, publicly-known electrical engineering
laws, formulas, and principles (not copyrighted). Used for RAG injection
into Gemini prompts to make the solver domain-specialist.

Functions:
    get_relevant_context(query: str) -> str
        Returns a relevant KB excerpt to prepend to Gemini calls.
"""

import re
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
#  CHAPTER 1 — Basic Concepts & Circuit Elements (Bakshi Ch. 1 alignment)
# ─────────────────────────────────────────────────────────────────────────────
DC_BASICS = """
## Reference: Basic Circuit Concepts & Laws

### Ohm's Law
V = IR   (voltage = current × resistance)
I = V/R  (current = voltage / resistance)
P = VI = I²R = V²/R   (power dissipation)

### Kirchhoff's Current Law (KCL)
The algebraic sum of currents entering a node = 0
  ΣI_in = ΣI_out   (at every node)

### Kirchhoff's Voltage Law (KVL)
The algebraic sum of voltages around any closed loop = 0
  ΣV_rises = ΣV_drops   (around every mesh)

### Sign Convention
- Current enters (+) terminal of passive element → voltage drop
- Assumed mesh current direction (clockwise positive is standard)
- Voltage source: + to − is a rise; − to + is a drop along current path

### Series Circuits
R_eq = R1 + R2 + … + Rn
Voltage divider: V_k = V_s × Rk / R_total

### Parallel Circuits
1/R_eq = 1/R1 + 1/R2 + … + 1/Rn
For two resistors: R_eq = (R1 × R2)/(R1 + R2)
Current divider: I_k = I_total × (R_other / R_total)

### Source Transformations
Voltage source V_s in series with R_s  ↔  Current source I_s = V_s/R_s in parallel with R_s
(Sources are equivalent at external terminals)

### Power Balance
ΣP_delivered = ΣP_absorbed   (conservation of energy)
Independent sources deliver power; passive elements absorb power.
"""

# ─────────────────────────────────────────────────────────────────────────────
#  CHAPTER 2 — Mesh Analysis (Bakshi Ch. 2 alignment)
# ─────────────────────────────────────────────────────────────────────────────
MESH_ANALYSIS = """
## Reference: Mesh Analysis (KVL Method)

### Procedure
1. Identify all independent meshes (loops that share no other loops).
2. Assign mesh currents I1, I2, … In (clockwise is convention).
3. Write KVL for each mesh:
     For mesh k: ΣR × I_k − ΣR_shared × I_adj = ΣV_sources in mesh k
4. Form the matrix equation [R][I] = [V] and solve using Cramer's rule or SymPy.

### Matrix Form (N meshes)
  | R11  -R12  -R13 | | I1 |   | V1 |
  | -R21  R22  -R23 | | I2 | = | V2 |
  | -R31 -R32   R33 | | I3 |   | V3 |

  R_kk = sum of ALL resistances in mesh k
  R_kj = sum of resistances SHARED between mesh k and mesh j (negative off-diagonal)
  V_k  = algebraic sum of voltage sources in mesh k (+ if source aids mesh current)

### Supermesh
When a current source is shared between two meshes:
  - Do NOT write KVL through the current source
  - Write a supermesh KVL (combine the two mesh KVLs, excluding the current source branch)
  - Write constraint: I_k − I_j = I_source (or I_j − I_k depending on direction)
  - Net unknowns remain the same

### Dependent Sources in Mesh Analysis
  - Include the dependent source expression in the KVL equations
  - Express the controlling variable in terms of the mesh currents, then substitute
"""

# ─────────────────────────────────────────────────────────────────────────────
#  CHAPTER 3 — Nodal Analysis (Bakshi Ch. 3 alignment)
# ─────────────────────────────────────────────────────────────────────────────
NODAL_ANALYSIS = """
## Reference: Nodal Analysis (KCL Method)

### Procedure
1. Choose a reference node (ground, V = 0).
2. Label remaining nodes V1, V2, … Vn.
3. Write KCL at each non-reference node:
     ΣI_leaving_node = ΣI_entering_node
     Or: (V_k − V_j)/R_kj + … = I_source_entering_at_k
4. Solve the system of equations.

### Matrix Form (N nodes, conductance form)
  | G11  -G12  -G13 | | V1 |   | I1 |
  | -G21  G22  -G23 | | V2 | = | I2 |
  | -G31 -G32   G33 | | V3 |   | I3 |

  G_kk = sum of ALL conductances connected to node k
  G_kj = conductance BETWEEN node k and node j (negative off-diagonal)
  I_k  = algebraic sum of current sources injecting into node k

### Supernode
When a voltage source is connected between two non-reference nodes:
  - Combine those two nodes into a supernode
  - Write KCL for the combined supernode (net currents entering = 0)
  - Write constraint: V_k − V_j = V_source
  - This preserves the number of independent equations

### Dependent Sources
  - Include dependent source in KCL: express the controlling variable in terms of node voltages, substitute
"""

# ─────────────────────────────────────────────────────────────────────────────
#  CHAPTER 4 — Network Theorems (Bakshi Ch. 4-5 alignment)
# ─────────────────────────────────────────────────────────────────────────────
NETWORK_THEOREMS = """
## Reference: Network Theorems

### Superposition Theorem
For linear circuits with multiple independent sources:
  1. Keep ONE independent source active at a time; deactivate others
       (Voltage source → short circuit; Current source → open circuit)
  2. Find the response (voltage or current) due to that source alone
  3. Total response = algebraic sum of individual responses
  NOTE: Cannot be applied to power (non-linear); only valid for voltage/current.

### Thevenin's Theorem
Any linear two-terminal network = V_th in series with R_th
  V_th  = Open-circuit voltage at the terminals (remove load, measure V_oc)
  R_th  = Equivalent resistance seen from terminals with all independent sources deactivated
          (or V_oc / I_sc where I_sc = short-circuit current)
  If dependent sources present: use V_oc / I_sc method ONLY (don't deactivate dep. sources)

### Norton's Theorem
Any linear two-terminal network = I_N in parallel with R_N
  I_N = Short-circuit current at the terminals (I_sc)
  R_N = R_th (same value as Thevenin resistance)
  Relation: V_th = I_N × R_N

### Maximum Power Transfer Theorem
Maximum power is transferred to load R_L when:
  R_L = R_th  (load equals Thevenin resistance)
  P_max = V_th² / (4 × R_th)
  Efficiency at max power transfer = 50%

### Millman's Theorem
For N voltage sources V1…Vn with series resistors R1…Rn in parallel:
  V_common = (V1/R1 + V2/R2 + … + Vn/Rn) / (1/R1 + 1/R2 + … + 1/Rn)

### Reciprocity Theorem
In a linear passive bilateral network:
  V / I_x = V_x / I  (the ratio of excitation to response is the same when source and response are interchanged)

### Delta ↔ Wye (Star) Transformation
Delta to Wye:
  Ra = (Rab × Rca) / (Rab + Rbc + Rca)
  Rb = (Rab × Rbc) / (Rab + Rbc + Rca)
  Rc = (Rbc × Rca) / (Rab + Rbc + Rca)

Wye to Delta:
  Rab = Ra + Rb + (Ra×Rb)/Rc
  Rbc = Rb + Rc + (Rb×Rc)/Ra
  Rca = Rc + Ra + (Rc×Ra)/Rb
  (Or: R_delta = sum of Wye products taken two at a time / opposite Wye resistor)
"""

# ─────────────────────────────────────────────────────────────────────────────
#  CHAPTER 5 — AC Circuits & Phasor Analysis (Bakshi Ch. 6-7 alignment)
# ─────────────────────────────────────────────────────────────────────────────
AC_PHASORS = """
## Reference: AC Circuits and Phasor Analysis

### Phasor Representation
Sinusoidal signal: v(t) = Vm sin(ωt + φ)   or   Vm cos(ωt + φ)
Phasor: V = Vm∠φ  =  Vm(cosφ + j sinφ)
ω = 2πf  (angular frequency, rad/s)

### Impedances (at angular frequency ω)
  Resistor:   Z_R = R       (real, no phase shift)
  Inductor:   Z_L = jωL     (phase: voltage leads current by 90°)
  Capacitor:  Z_C = 1/(jωC) = -j/(ωC)   (phase: current leads voltage by 90°)

### Series RLC Impedance
  Z = R + j(ωL − 1/(ωC))
  |Z| = √(R² + (ωL − 1/(ωC))²)
  φ = arctan((ωL − 1/(ωC)) / R)

### KVL and KCL in Phasor Domain
  Identical to DC analysis but using complex impedances Z instead of R
  V = I × Z  (Ohm's law in phasor domain)

### Admittance
  Y = 1/Z = G + jB   (G = conductance, B = susceptance)
  Y_R = 1/R;   Y_L = 1/(jωL) = -j/(ωL);   Y_C = jωC

### Power in AC Circuits
  Apparent Power:  S = V × I*   [VA]   (V, I are phasors; I* = complex conjugate)
  Real Power:      P = |V||I|cosφ = I²R   [W]
  Reactive Power:  Q = |V||I|sinφ        [VAR]
  Power Factor:    PF = cosφ = P/|S|
  |S|² = P² + Q²

### Voltage / Current Divider (Phasor Form)
  Voltage divider: V_2 = V_s × Z2/(Z1+Z2)
  Current divider: I_2 = I_s × Z1/(Z1+Z2)

### Mesh and Nodal Analysis in AC
  Replace all R with Z (impedances). System of equations becomes complex-valued.
  Solve using SymPy with complex symbols or numpy for numerical results.
"""

# ─────────────────────────────────────────────────────────────────────────────
#  CHAPTER 6 — Resonance (Bakshi Ch. 8 alignment)
# ─────────────────────────────────────────────────────────────────────────────
RESONANCE = """
## Reference: Resonance in RLC Circuits

### Series Resonance
At resonance: ωL = 1/(ωC)  →  ω₀ = 1/√(LC)   (rad/s),   f₀ = 1/(2π√(LC)) Hz
At ω₀:
  Z = R  (purely resistive, minimum impedance)
  I = V/R  (maximum current)
  V_L = V_C = Q × V_s  (voltage magnification)
  Q = ω₀L/R = 1/(ω₀CR) = (1/R)√(L/C)   (Quality factor)
  Bandwidth: BW = f₀/Q  (Hz);   or  BW = R/L  (rad/s)
  Half-power frequencies: f₁, f₂ = f₀ ± BW/2

### Parallel Resonance (Ideal tank circuit)
At resonance: ω₀ = 1/√(LC)  (same formula)
At ω₀:
  Z = R_p  (maximum impedance)
  I_source is minimum; circulating current in L and C = Q × I_source
  Q = R_p/(ω₀L) = R_p × ω₀C

### Bandwidth and Selectivity
  Q factor determines selectivity (higher Q = narrower bandwidth = more selective)
  BW = f₀/Q;   f₁ = f₀/√(1 + 1/(4Q²)) − f₀/(2Q) ≈ f₀ − BW/2  (for high Q)
"""

# ─────────────────────────────────────────────────────────────────────────────
#  CHAPTER 7 — Transient Analysis (Bakshi Ch. 9-10 alignment)
# ─────────────────────────────────────────────────────────────────────────────
TRANSIENT_ANALYSIS = """
## Reference: Transient Analysis (Time‐Domain)

### General Approach (Classical Method)
  Total Response = Natural Response + Forced (Steady-State) Response
  x(t) = x_natural(t) + x_steady(t)

### RC Circuit — Step Input (V_s applied at t=0)
  Charging: v_C(t) = V_s(1 − e^(−t/τ))   where τ = RC
  Current:  i(t) = (V_s/R) × e^(−t/τ)
  τ is the time constant; v_C reaches ~63.2% of V_s in one τ, ~99.3% in 5τ

  Discharging (initial V₀): v_C(t) = V₀ × e^(−t/τ)

### RL Circuit — Step Input
  i_L(t) = (V_s/R)(1 − e^(−t/τ))   where τ = L/R
  v_L(t) = V_s × e^(−t/τ)
  Energy stored in inductor: E = ½LI²

### Initial Conditions
  - Capacitor voltage cannot change instantaneously: v_C(0⁺) = v_C(0⁻)
  - Inductor current cannot change instantaneously: i_L(0⁺) = i_L(0⁻)
  - At DC steady state: capacitor → open circuit; inductor → short circuit

### RLC Series Circuit — Step Input
  Characteristic equation: s² + (R/L)s + 1/(LC) = 0
  Roots: s₁,₂ = −α ± √(α² − ω₀²)
  where α = R/(2L)  (damping coefficient),  ω₀ = 1/√(LC)  (natural frequency)

  Case 1 — Overdamped (α > ω₀):  two distinct real roots → exponential decay (no oscillation)
    i(t) = A₁e^(s₁t) + A₂e^(s₂t)

  Case 2 — Critically Damped (α = ω₀):  repeated real root s = −α
    i(t) = (A₁ + A₂t)e^(−αt)

  Case 3 — Underdamped (α < ω₀):  complex conjugate roots → damped sinusoid
    ωd = √(ω₀² − α²)   (damped natural frequency)
    i(t) = e^(−αt)(A₁cos(ωd t) + A₂sin(ωd t))

### RLC Parallel Circuit
  Characteristic equation: s² + s/(RC) + 1/(LC) = 0
  α = 1/(2RC);  ω₀ = 1/√(LC);  same three cases apply.

### Finding A₁, A₂ (Constants of Integration)
  Use initial conditions: i(0), v(0), and di/dt(0) = [V_L(0)]/L or dv/dt(0) = [I_C(0)]/C
"""

# ─────────────────────────────────────────────────────────────────────────────
#  CHAPTER 8 — Laplace Transform & s-Domain (Bakshi Ch. 11 alignment)
# ─────────────────────────────────────────────────────────────────────────────
LAPLACE_DOMAIN = """
## Reference: Laplace Transform & s-Domain Circuit Analysis

### Common Laplace Pairs
  δ(t)          ↔  1
  u(t)          ↔  1/s
  t             ↔  1/s²
  e^(−at)       ↔  1/(s+a)
  sin(ωt)       ↔  ω/(s²+ω²)
  cos(ωt)       ↔  s/(s²+ω²)
  e^(−at)sin(ωt) ↔  ω/((s+a)²+ω²)
  e^(−at)cos(ωt) ↔  (s+a)/((s+a)²+ω²)

### s-Domain Element Models (with initial conditions)
  Resistor R:   V(s) = R × I(s)
  Inductor L:   V(s) = sL × I(s) − L×i_L(0⁻)   [Series model]
                     Z_L(s) = sL
  Capacitor C:  V(s) = I(s)/(sC) + v_C(0⁻)/s    [Series model]
                     Z_C(s) = 1/(sC)

### Network Function (Transfer Function)
  H(s) = Y(s)/X(s) = Output/Input (in s-domain, zero initial conditions)
  Zeros: values of s where H(s)=0
  Poles: values of s where H(s)→∞

### Partial Fraction Expansion
  F(s) = N(s)/D(s)
  Distinct real poles: F(s) = K1/(s+p1) + K2/(s+p2) + …
  Repeated pole (s+p)^n: terms are K1/(s+p) + K2/(s+p)² + … + Kn/(s+p)^n
  Complex pair s = −α ± jωd: combine to (As+B)/((s+α)²+ωd²), match to Laplace pairs table

### Final & Initial Value Theorems
  Initial value: x(0⁺) = lim[s→∞] s×X(s)
  Final value:   x(∞)  = lim[s→0] s×X(s)   (only valid if X(s) has all poles in LHP)
"""

# ─────────────────────────────────────────────────────────────────────────────
#  CHAPTER 9 — Frequency Response & Bode Plots (Bakshi Ch. 12 alignment)
# ─────────────────────────────────────────────────────────────────────────────
FREQUENCY_RESPONSE = """
## Reference: Frequency Response & Bode Plots

### Frequency Response
  H(jω) = H(s)|_{s=jω}   (substitute s = jω in the transfer function)
  |H(jω)| = magnitude response (gain)
  ∠H(jω) = phase response

### Common Filter Transfer Functions
  Low-pass  RC: H(s) = (1/RC)/(s + 1/RC)   →   ωc = 1/RC,  -3dB at ωc
  High-pass RC: H(s) = s/(s + 1/RC)         →   ωc = 1/RC,  -3dB at ωc
  Band-pass RLC series: H(s) = (R/L)s / (s² + (R/L)s + 1/(LC))   →   peaks at ω₀

### Bode Plot Rules
  Magnitude in dB: |H|_dB = 20 log₁₀|H(jω)|
  Each zero at s = 0: +20 dB/dec slope
  Each pole at s = 0: −20 dB/dec slope
  Real zero at s = −z: gain increases +20dB/dec after ω = z
  Real pole at s = −p: gain decreases −20dB/dec after ω = p
  Complex pair: affects plot near natural frequency ω₀

### Key Cutoff Frequencies
  -3dB frequency: |H(jωc)| = 1/√2 × |H(0)|
  For RC low-pass: ωc = 1/(RC);  fc = 1/(2πRC)
  For series RLC:  ωc1,2 = −(R/2L) ± √((R/2L)² + 1/(LC))
"""

# ─────────────────────────────────────────────────────────────────────────────
#  CHAPTER 10 — Two-Port Networks (Bakshi Ch. 13 alignment)
# ─────────────────────────────────────────────────────────────────────────────
TWO_PORT_NETWORKS = """
## Reference: Two-Port Network Parameters

### Z-parameters (Open-circuit impedance)
  V1 = Z11×I1 + Z12×I2
  V2 = Z21×I1 + Z22×I2
  Z11 = V1/I1|_{I2=0} (input impedance, output open)
  Z22 = V2/I2|_{I1=0} (output impedance, input open)
  Z12 = V1/I2|_{I1=0};   Z21 = V2/I1|_{I2=0}

### Y-parameters (Short-circuit admittance)
  I1 = Y11×V1 + Y12×V2
  I2 = Y21×V1 + Y22×V2
  Y11 = I1/V1|_{V2=0};  Y12 = I1/V2|_{V1=0}

### h-parameters (Hybrid)
  V1 = h11×I1 + h12×V2
  I2 = h21×I1 + h22×V2
  (Used widely for transistor models)

### ABCD (Transmission) Parameters
  | V1 |   | A  B | | V2  |
  | I1 | = | C  D | |-I2  |
  A = V1/V2|_{I2=0};  B = V1/(-I2)|_{V2=0}
  C = I1/V2|_{I2=0};  D = I1/(-I2)|_{V2=0}
  For reciprocal network: AD − BC = 1

### Parameter Conversions (Z ↔ Y)
  [Y] = [Z]⁻¹   (inverse of Z matrix)
  ΔZ = Z11×Z22 − Z12×Z21

### Series / Parallel / Cascade Combinations
  Series connection:  [Z_total] = [Z_a] + [Z_b]
  Parallel connection: [Y_total] = [Y_a] + [Y_b]
  Cascade connection: [ABCD_total] = [ABCD_a] × [ABCD_b]
"""

# ─────────────────────────────────────────────────────────────────────────────
#  CHAPTER 11 — Coupled Circuits & Mutual Inductance
# ─────────────────────────────────────────────────────────────────────────────
COUPLED_CIRCUITS = """
## Reference: Coupled Circuits & Mutual Inductance

### Mutual Inductance
  v1 = L1 × di1/dt ± M × di2/dt
  v2 = L2 × di2/dt ± M × di1/dt
  (+) when both currents enter dotted terminals; (−) otherwise
  M = k√(L1×L2)  where k = coefficient of coupling (0 ≤ k ≤ 1)

### s-Domain (or jω-domain) for Coupled Circuits
  V1 = jωL1×I1 ± jωM×I2
  V2 = jωL2×I2 ± jωM×I1

### Series-Aiding vs. Series-Opposing Inductors
  Aiding (same dot): L_total = L1 + L2 + 2M
  Opposing:          L_total = L1 + L2 − 2M

### Reflected Impedance (Transformer)
  For an ideal transformer (coupling k=1):
    V2/V1 = N2/N1 = n  (turns ratio)
    I1/I2 = n
    Z_reflected = Z_L / n²  (load impedance seen at primary)
"""

# ─────────────────────────────────────────────────────────────────────────────
#  LOOKUP TABLE — Maps keywords to KB sections
# ─────────────────────────────────────────────────────────────────────────────
_KEYWORD_MAP = {
    "mesh": ("MESH", MESH_ANALYSIS),
    "kvl": ("MESH", MESH_ANALYSIS),
    "loop": ("MESH", MESH_ANALYSIS),
    "supermesh": ("MESH", MESH_ANALYSIS),
    "nodal": ("NODAL", NODAL_ANALYSIS),
    "kcl": ("NODAL", NODAL_ANALYSIS),
    "node voltage": ("NODAL", NODAL_ANALYSIS),
    "supernode": ("NODAL", NODAL_ANALYSIS),
    "thevenin": ("THEOREMS", NETWORK_THEOREMS),
    "norton": ("THEOREMS", NETWORK_THEOREMS),
    "superposition": ("THEOREMS", NETWORK_THEOREMS),
    "maximum power": ("THEOREMS", NETWORK_THEOREMS),
    "millman": ("THEOREMS", NETWORK_THEOREMS),
    "delta": ("THEOREMS", NETWORK_THEOREMS),
    "wye": ("THEOREMS", NETWORK_THEOREMS),
    "star": ("THEOREMS", NETWORK_THEOREMS),
    "source transformation": ("BASICS", DC_BASICS),
    "ohm": ("BASICS", DC_BASICS),
    "series": ("BASICS", DC_BASICS),
    "parallel": ("BASICS", DC_BASICS),
    "phasor": ("AC", AC_PHASORS),
    "impedance": ("AC", AC_PHASORS),
    "ac circuit": ("AC", AC_PHASORS),
    "admittance": ("AC", AC_PHASORS),
    "power factor": ("AC", AC_PHASORS),
    "reactive power": ("AC", AC_PHASORS),
    "apparent power": ("AC", AC_PHASORS),
    "resonan": ("RESONANCE", RESONANCE),
    "quality factor": ("RESONANCE", RESONANCE),
    "bandwidth": ("RESONANCE", RESONANCE),
    "tank circuit": ("RESONANCE", RESONANCE),
    "transient": ("TRANSIENT", TRANSIENT_ANALYSIS),
    "time constant": ("TRANSIENT", TRANSIENT_ANALYSIS),
    "step response": ("TRANSIENT", TRANSIENT_ANALYSIS),
    "overdamp": ("TRANSIENT", TRANSIENT_ANALYSIS),
    "underdamp": ("TRANSIENT", TRANSIENT_ANALYSIS),
    "critically damp": ("TRANSIENT", TRANSIENT_ANALYSIS),
    "initial condition": ("TRANSIENT", TRANSIENT_ANALYSIS),
    "capacitor voltage": ("TRANSIENT", TRANSIENT_ANALYSIS),
    "inductor current": ("TRANSIENT", TRANSIENT_ANALYSIS),
    "laplace": ("LAPLACE", LAPLACE_DOMAIN),
    "s-domain": ("LAPLACE", LAPLACE_DOMAIN),
    "transfer function": ("LAPLACE", LAPLACE_DOMAIN),
    "partial fraction": ("LAPLACE", LAPLACE_DOMAIN),
    "final value": ("LAPLACE", LAPLACE_DOMAIN),
    "initial value theorem": ("LAPLACE", LAPLACE_DOMAIN),
    "bode": ("FREQ", FREQUENCY_RESPONSE),
    "frequency response": ("FREQ", FREQUENCY_RESPONSE),
    "low-pass": ("FREQ", FREQUENCY_RESPONSE),
    "high-pass": ("FREQ", FREQUENCY_RESPONSE),
    "cutoff": ("FREQ", FREQUENCY_RESPONSE),
    "filter": ("FREQ", FREQUENCY_RESPONSE),
    "two-port": ("TWOPORT", TWO_PORT_NETWORKS),
    "z-parameter": ("TWOPORT", TWO_PORT_NETWORKS),
    "y-parameter": ("TWOPORT", TWO_PORT_NETWORKS),
    "h-parameter": ("TWOPORT", TWO_PORT_NETWORKS),
    "abcd": ("TWOPORT", TWO_PORT_NETWORKS),
    "transmission parameter": ("TWOPORT", TWO_PORT_NETWORKS),
    "mutual inductance": ("COUPLED", COUPLED_CIRCUITS),
    "coupled": ("COUPLED", COUPLED_CIRCUITS),
    "transformer": ("COUPLED", COUPLED_CIRCUITS),
    "dot convention": ("COUPLED", COUPLED_CIRCUITS),
}

# All sections in order (used as fallback context)
_ALL_SECTIONS = [
    DC_BASICS, MESH_ANALYSIS, NODAL_ANALYSIS, NETWORK_THEOREMS,
    AC_PHASORS, RESONANCE, TRANSIENT_ANALYSIS, LAPLACE_DOMAIN,
    FREQUENCY_RESPONSE, TWO_PORT_NETWORKS, COUPLED_CIRCUITS
]


def get_relevant_context(query: str, max_sections: int = 3) -> str:
    """
    Returns a relevant subset of the knowledge base based on keywords in the query.
    Falls back to DC basics + mesh/nodal if no keywords match.

    Parameters
    ----------
    query : str
        The user's circuit problem description.
    max_sections : int
        Maximum number of KB sections to include (to keep prompt size manageable).

    Returns
    -------
    str
        A formatted string block to prepend to the Gemini system call.
    """
    q_lower = query.lower()

    seen_ids: set = set()
    matched: list[str] = []

    for keyword, (section_id, content) in _KEYWORD_MAP.items():
        if keyword in q_lower and section_id not in seen_ids:
            seen_ids.add(section_id)
            matched.append(content)
            if len(matched) >= max_sections:
                break

    # Fallback: always include DC basics if no match or query is very short
    if not matched:
        matched = [DC_BASICS, MESH_ANALYSIS, NODAL_ANALYSIS]

    header = (
        "### 📚 Network Analysis Knowledge Base (Bakshi-aligned EEE Reference)\n"
        "The following domain knowledge is injected to guide your solution:\n\n"
    )
    return header + "\n".join(matched)


def get_full_compendium() -> str:
    """Returns the complete knowledge base (for debugging or system prompt priming)."""
    return "\n\n".join(_ALL_SECTIONS)
