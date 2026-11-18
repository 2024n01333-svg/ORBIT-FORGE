# OrbitForge — CubeSat Mission Configuration Advisor
An Academic Rule-Based Expert System for Small Satellite Systems Engineering.

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.67.0-red.svg)](https://streamlit.io)
[![Test Suite](https://img.shields.io/badge/pytest-18%20passed-brightgreen.svg)](https://pytest.org)
[![Knowledge Base](https://img.shields.io/badge/Production%20Rules-112-success.svg)]()
[![Domain Facts](https://img.shields.io/badge/Domain%20Facts-386-success.svg)]()

---

## 1. Executive Summary & Purpose
OrbitForge is a complete, genuine rule-based Expert System developed according to rigorous academic Expert Systems methodologies. It advises aerospace mission planners, academic research groups, and commercial satellite developers on the optimal sizing, component selection, regulatory compliance, and cross-subsystem configuration of CubeSats (ranging from 1U to 16U+).

The decision-making mechanism is **purely deterministic and auditable**, driven by explicit production rules with formal forward and backward chaining inference engines, rather than a probabilistic LLM chatbot.

---

## 2. Key Architecture & System Components

### 2.1 Structured Knowledge Base
- **Explicit Production Rules (`knowledge_base/rules.json`)**: Contains **112 explicit IF-THEN production rules** across 11 functional domains:
  - `orbit`: Orbital decay, altitude lifetime, SSO LTAN selection, radiation belts, atmospheric density.
  - `structure`: Form factor volume/mass limits (1U, 2U, 3U, 6U, 12U), deployer rail specifications, center-of-gravity offsets.
  - `power`: Triple-junction solar cell generation, MPPT vs DET, Li-ion battery capacity, depth-of-discharge (DoD), bus voltages (3.3V, 5V, 12V, 28V).
  - `comm`: Frequency band selection (UHF, S-band, X-band, Ka-band, Optical Laser), RF power, link margins, atmospheric rain fade, DSN compatibility.
  - `adcs`: Pointing tolerances, sensor suites (fine sun sensors, magnetometers, star trackers), actuators (passive magnetic, magnetorquers, reaction wheel clusters), desaturation methods.
  - `payload`: Earth Observation optical cameras, SAR radars, hyperspectral spectrometers, thermal infrared (TIR), maritime AIS, IoT LoRa store-and-forward, microfluidics biology labs.
  - `thermal`: Surface emissivity/absorptivity finishes, MLI blankets, battery thermal enclosures, heat pipes, micro-cryocoolers.
  - `propulsion`: Cold gas, green chemical monopropellant, electrospray, gridded ion thrusters, deployable drag sails.
  - `launch`: GEVS vibration levels, separation kill-switches, post-deploy RF silence timers, non-toxic propellant mandates.
  - `regulations`: FCC 5-year post-mission disposal rule, ITU spectrum coordination, battery passivation.
  - `system_validation`: Cross-subsystem consistency checks (e.g. power-area mismatch, payload data rate vs UHF bottleneck).

- **Domain Assertions & Facts (`knowledge_base/facts.json`)**: Contains **386 verified domain assertions and component specifications** stored separately in an inspectable JSON format.

### 2.2 Genuine Inference Engine (`expert_system/engine.py`)
- **Working Memory (`WorkingMemory`)**: Dynamic state database storing active assertions, values, physical units, and provenance (`user`, `scenario`, `deduced`, `rule:<ID>`).
- **Forward Chaining**: Classic Match-Resolve-Act cycle running to quiescence.
- **Conflict Resolution Strategy**:
  1. **Salience (Priority)**: Rules with higher salience (1-100) are activated first.
  2. **Specificity**: Rules with a greater number of antecedent condition clauses take precedence over general fallback rules.
  3. **Definition Order**: Tie-breaker based on stable rule order.
- **Backward Chaining**: Goal-directed recursive reasoning algorithm that checks whether a user hypothesis (e.g., `"Is 6U required?"` or `"Will this violate FCC deorbit rules?"`) can be proven. Generates hierarchical proof trees and identifies missing prerequisite facts.
- **Explanation Facility & Reasoning Tracer**: Logs every fired rule, matched condition values, conflict set evaluations, timestamps, and domain rationales for full transparency.

### 2.3 Natural Language Interface (`expert_system/nlp_interface.py`)
- Enables users to state their mission requirements in plain English.
- Extracts entities (payload instruments, orbital altitudes, inclinations, lifetimes, form factors, organization types).
- Evaluates missing mission-critical parameters and generates targeted follow-up questions.
- Transmits validated facts into the working memory of the inference engine.

---

## 3. Web Application Features (`app.py`)
The Streamlit interface provides 6 dedicated views:
1. **Mission Advisor (NLP)**: Interactive conversational interface alongside real-time subsystem configuration dashboards and reasoning cards.
2. **Interactive Configuration**: Parameter configuration form allowing engineers to adjust altitudes, payloads, and pointing requirements directly.
3. **Goal Verification (Backward Chaining)**: Interactive hypothesis evaluation tool producing backward proof trees and missing fact diagnostics.
4. **Rule Explorer**: Filterable and searchable catalog of all 112 production rules displaying condition clauses, salience, and explanations.
5. **Knowledge Base Explorer**: Searchable table of all 386 domain assertions and physical specifications.
6. **Pre-Built Scenarios**:
   - *Earth Observation 6U (SSO High-Res RGB)*
   - *IoT Store-and-Forward 1U (Academic Low-Cost)*
   - *Synthetic Aperture Radar (SAR) 12U High-Power*
   - *Deep Space Lunar Orbiter 12U*
   - *Maritime AIS Tracking 3U*

---

## 4. Installation & Running

```bash
# Clone and enter the repository
git clone <repo-url>
cd orbitforge

# Install dependencies
pip install streamlit pytest pytest-cov pandas

# Run the test suite (100% passing)
PYTHONPATH=. pytest tests/ -v

# Launch the OrbitForge web application
streamlit run app.py
```

Access the web UI at `http://localhost:8501`.

---

## 5. Verification & Testing Summary
- **Knowledge Base Validation (`verify_kb.py`)**: Confirms 112 rules and 386 facts, valid schemas, and unique IDs.
- **Unit & Integration Tests (`tests/`)**:
  - `test_engine.py`: Tests working memory CRUD, forward chaining, backward chaining, conflict resolution (salience & specificity), and explanation facility.
  - `test_nlp.py`: Tests entity extraction, missing information analysis, and dialogue turn responses.
  - `test_integration.py`: Tests all 5 pre-built scenarios and end-to-end subsystem synthesis.
- **Frontend Verification**: Fully verified with Playwright headless browser automation, capturing and validating UI rendering and user interactions.
