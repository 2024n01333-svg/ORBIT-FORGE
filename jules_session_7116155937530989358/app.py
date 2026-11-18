"""
OrbitForge — CubeSat Mission Configuration Advisor
Academic Rule-Based Expert System Web Application.
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path

from expert_system.knowledge import KnowledgeBase
from expert_system.engine import InferenceEngine
from expert_system.nlp_interface import NaturalLanguageInterface
from expert_system.scenarios import SCENARIOS

# Page configuration
st.set_page_config(
    page_title="OrbitForge — CubeSat Mission Advisor",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #3B82F6;
        margin-bottom: 10px;
    }
    .rule-card {
        background-color: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
    }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 4px;
        margin-right: 6px;
    }
    .badge-primary { background-color: #DBEAFE; color: #1E40AF; }
    .badge-success { background-color: #D1FAE5; color: #065F46; }
    .badge-warning { background-color: #FEF3C7; color: #92400E; }
    .badge-danger { background-color: #FEE2E2; color: #991B1B; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_expert_system():
    kb = KnowledgeBase("knowledge_base/facts.json", "knowledge_base/rules.json")
    nlp = NaturalLanguageInterface()
    return kb, nlp

kb, nlp = load_expert_system()

# Initialize session state
if "working_facts" not in st.session_state:
    st.session_state.working_facts = {}

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Welcome to **OrbitForge — CubeSat Mission Configuration Advisor**!\n\nDescribe your CubeSat mission in plain English (e.g. *\"We are building a 6U optical Earth observation satellite for a university mission at 500 km SSO orbit\"*), or pick a preset scenario from the sidebar."}
    ]

if "engine_run_results" not in st.session_state:
    st.session_state.engine_run_results = None

# Sidebar Navigation
st.sidebar.image("https://images.unsplash.com/photo-1516849841032-87cbac4d88f7?w=400&q=80", use_container_width=True)
st.sidebar.title("🛰️ OrbitForge Navigation")

mode = st.sidebar.radio(
    "Choose View:",
    ["Mission Advisor (NLP)", "Interactive Configuration", "Goal Verification (Backward Chaining)", "Rule Explorer", "Knowledge Base Explorer", "System Documentation"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Presets & Scenarios")
selected_scenario = st.sidebar.selectbox("Load Predefined Mission:", ["-- Select --"] + list(SCENARIOS.keys()))

if st.sidebar.button("Load Scenario") and selected_scenario != "-- Select --":
    sc = SCENARIOS[selected_scenario]
    st.session_state.working_facts = dict(sc["facts"])
    st.session_state.messages.append({"role": "user", "content": sc["input_text"]})
    
    # Run inference engine
    eng = InferenceEngine(kb)
    for k, v in sc["facts"].items():
        eng.working_memory.set(k, v, source="scenario")
    run_res = eng.forward_chain()
    st.session_state.engine_run_results = {
        "engine": eng,
        "summary": run_res
    }
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"Loaded scenario: **{selected_scenario}**.\n\nFired **{run_res['fired_count']} production rules** across subsystems."
    })
    st.rerun()

if st.sidebar.button("Reset Working Memory"):
    st.session_state.working_facts = {}
    st.session_state.engine_run_results = None
    st.session_state.messages = [
        {"role": "assistant", "content": "Working memory reset. Enter a new CubeSat mission description to begin."}
    ]
    st.rerun()

# Knowledge Base Stats in Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Knowledge Base Stats:**\n- Production Rules: `{kb.rule_count}` (Requirement: >=100)\n- Asserted Facts: `{kb.fact_count}` (Requirement: >=300)")


# =============================================================================
# VIEW 1: MISSION ADVISOR (NLP CHAT + INFERENCE DASHBOARD)
# =============================================================================
if mode == "Mission Advisor (NLP)":
    st.markdown('<div class="main-header">OrbitForge — CubeSat Mission Configuration Advisor</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Conversational Natural Language Interface coupled to a Deterministic Production Rule Inference Engine</div>', unsafe_allow_html=True)

    col_chat, col_results = st.columns([1.1, 1.3])

    with col_chat:
        st.subheader("💬 Mission Dialogue")
        
        # Display chat conversation
        chat_container = st.container(height=480)
        with chat_container:
            for m in st.session_state.messages:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

        # Chat input
        user_prompt = st.chat_input("Describe your CubeSat payload, orbit, lifetime, or form factor...")
        if user_prompt:
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            
            # Natural Language Processing
            nlp_res = nlp.generate_response(user_prompt, st.session_state.working_facts)
            st.session_state.working_facts = nlp_res["all_facts"]

            # Run deterministic inference engine
            eng = InferenceEngine(kb)
            for k, v in st.session_state.working_facts.items():
                eng.working_memory.set(k, v, source="user_input")
            
            summary = eng.forward_chain()
            st.session_state.engine_run_results = {
                "engine": eng,
                "summary": summary
            }

            reply_text = nlp_res["reply"]
            if summary["fired_count"] > 0:
                reply_text += f"\n\n⚙️ **Inference Engine Update**: {summary['fired_count']} rules activated and fired."

            st.session_state.messages.append({"role": "assistant", "content": reply_text})
            st.rerun()

    with col_results:
        st.subheader("⚙️ Mission Synthesis & Engineering Architecture")

        if st.session_state.engine_run_results:
            eng = st.session_state.engine_run_results["engine"]
            summary = st.session_state.engine_run_results["summary"]
            wm = eng.working_memory

            # Metrics Row
            m1, m2, m3, m4 = st.columns(4)
            configured_ff = wm.get_value("form_factor")
            min_ff = wm.get_value("min_form_factor")
            display_ff = f"{configured_ff} (Min: {min_ff})" if configured_ff and min_ff and configured_ff != min_ff else (configured_ff or min_ff or "TBD")
            m1.metric("Form Factor", display_ff)
            m2.metric("RF Band", wm.get_value("recommended_comm_downlink_band", "TBD"))
            m3.metric("Peak Power", f"{wm.get_value('peak_power_requirement_w', 0.0):.1f} W")
            m4.metric("Rules Fired", summary["fired_count"])

            tabs = st.tabs(["Subsystem Configuration", "Reasoning Trace", "Active Working Memory"])

            with tabs[0]:
                st.markdown("#### Subsystem Recommendations")
                
                # Orbit & Structure
                with st.expander("🛰️ Orbit, Structure & Launch", expanded=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Target Altitude:** `{wm.get_value('orbit_altitude_km', 'N/A')} km`")
                        st.markdown(f"**Orbit Regime:** `{wm.get_value('orbit_type', 'LEO').upper()}`")
                        st.markdown(f"**Max Mass Limit:** `{wm.get_value('max_satellite_mass_kg', 'N/A')} kg`")
                    with c2:
                        deorbit_ok = wm.get_value("deorbit_regulation_compliant")
                        if deorbit_ok is False:
                            st.error("⚠️ **FCC Deorbit Rule:** Non-compliant without active deorbit mechanism!")
                            st.info(f"Recommended Deorbit: `{wm.get_value('recommended_deorbit_device', 'Drag Sail / Propulsion')}`")
                        else:
                            st.success("✅ **FCC Deorbit Rule:** Compliant (< 5 year decay)")
                        st.markdown(f"**Structural Rail Finish:** `{wm.get_value('deployer_rail_finish', 'Hard Anodize')}`")

                # Power & Thermal
                with st.expander("⚡ Electrical Power & Thermal Systems", expanded=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Solar Panel Type:** `{wm.get_value('solar_panel_type', 'Body-Mounted')}`")
                        st.markdown(f"**Bus Rail Regulation:** `{wm.get_value('eps_regulated_bus_voltage', '5V/3.3V Standard')}`")
                        st.markdown(f"**Battery Cell Tech:** `{wm.get_value('battery_chemistry', 'Li-ion 18650 Space Grade')}`")
                    with c2:
                        st.markdown(f"**Thermal Control:** `{wm.get_value('thermal_control_architecture', 'Passive Surface Coatings')}`")
                        st.markdown(f"**Battery Heater:** `{wm.get_value('battery_thermal_mounting', 'Delrin Standoffs & Thermostat')}`")

                # Comm & ADCS
                with st.expander("📡 Communications & ADCS Pointing", expanded=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Downlink Frequency:** `{wm.get_value('recommended_comm_downlink_band', 'UHF')}`")
                        st.markdown(f"**Antenna Type:** `{wm.get_value('recommended_antenna_comm', wm.get_value('ais_antenna_type', 'Patch / Dipole'))}`")
                        st.markdown(f"**Post-Deploy Silence:** `{wm.get_value('mandatory_post_eject_radio_silence_min', 30)} minutes`")
                    with c2:
                        st.markdown(f"**ADCS Actuators:** `{wm.get_value('adcs_actuator_type', 'Coarse / Passive')}`")
                        st.markdown(f"**Sensor Suite:** `{wm.get_value('adcs_sensor_suite', 'Coarse Sun Sensors')}`")
                        st.markdown(f"**Detumble Algorithm:** `{wm.get_value('detumble_mode_algorithm', 'B-Dot Magnetic')}`")

            with tabs[1]:
                st.markdown("#### Rule Execution Trace (Explainability Facility)")
                st.markdown("Inspect which rules fired in what order, their priority (salience), antecedent conditions, and deducted assertions:")
                
                for step in eng.trace:
                    with st.expander(f"Step {step.step_number}: [{step.category.upper()}] {step.rule_id} — {step.rule_name} (Salience: {step.salience})"):
                        st.markdown(f"**Rationale:** {step.rationale}")
                        st.markdown("**Matched Antecedent Conditions:**")
                        for mc in step.matched_conditions:
                            st.code(f"{mc['fact_name']} {mc['required_op']} {mc['required_val']} (Actual: {mc['current_val']}) -> SATISFIED", language="python")
                        st.markdown("**Deductions (THEN Actions):**")
                        for act in step.deduced_actions:
                            st.markdown(f"- `{act['fact_name']}` = **`{act['value']}`** ({act.get('description', '')})")

            with tabs[2]:
                st.markdown("#### Working Memory Assertions")
                facts_data = []
                for name, f in wm.facts.items():
                    facts_data.append({
                        "Fact Name": name,
                        "Value": str(f.value),
                        "Category": f.category,
                        "Source": f.source
                    })
                df_wm = pd.DataFrame(facts_data)
                st.dataframe(df_wm, use_container_width=True)
        else:
            st.info("👈 Enter a mission description in the chat or pick a preset scenario to view the expert system synthesis.")


# =============================================================================
# VIEW 2: INTERACTIVE CONFIGURATION FORM
# =============================================================================
elif mode == "Interactive Configuration":
    st.markdown('<div class="main-header">Interactive Mission Parameter Configurator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Manually adjust mission requirements and fire the expert system inference engine</div>', unsafe_allow_html=True)

    with st.form("config_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("Orbit & Environment")
            altitude = st.number_input("Orbit Altitude (km)", min_value=200, max_value=2000, value=int(st.session_state.working_facts.get("orbit_altitude_km", 500)))
            orbit_type = st.selectbox("Orbit Type", ["sso", "leo", "equatorial", "lunar_orbit", "interplanetary"], index=0)
            mission_duration = st.slider("Mission Lifetime (Years)", min_value=0.5, max_value=10.0, value=float(st.session_state.working_facts.get("mission_duration_years", 2.0)))

        with c2:
            st.subheader("Payload & Form Factor")
            payload = st.selectbox(
                "Payload Instrument",
                ["earth_obs_optical_rgb", "synthetic_aperture_radar_sar", "hyperspectral_imaging", "earth_obs_thermal_tir", "iot_ais_receiver", "iot_lora_transceiver", "radiation_dosimeter_dos", "biology_microfluidics_lab"]
            )
            form_factor = st.selectbox("Desired Form Factor", ["Auto (Infer)", "1U", "2U", "3U", "6U", "12U", "16U"])
            pointing_req = st.slider("Required Pointing Accuracy (deg)", min_value=0.01, max_value=20.0, value=float(st.session_state.working_facts.get("pointing_accuracy_requirement_deg", 0.5)))

        with c3:
            st.subheader("Operational & Safety")
            org_type = st.selectbox("Organization Type", ["university", "commercial", "defense"])
            has_prop = st.checkbox("Include Propulsion System", value=bool(st.session_state.working_facts.get("has_propulsion_system", False)))
            has_drag_sail = st.checkbox("Include Deployable Drag Sail", value=bool(st.session_state.working_facts.get("has_drag_sail", False)))

        submit_btn = st.form_submit_button("Run Expert System Inference 🚀")

    if submit_btn:
        facts = {
            "orbit_altitude_km": float(altitude),
            "orbit_type": orbit_type,
            "mission_duration_years": float(mission_duration),
            "payload_type": payload,
            "pointing_accuracy_requirement_deg": float(pointing_req),
            "mission_organization_type": org_type,
            "has_propulsion_system": has_prop,
            "has_drag_sail": has_drag_sail,
            "mission_status": "in_design"
        }
        if form_factor != "Auto (Infer)":
            facts["form_factor"] = form_factor

        st.session_state.working_facts = facts

        eng = InferenceEngine(kb)
        for k, v in facts.items():
            eng.working_memory.set(k, v, source="manual_config")
        run_res = eng.forward_chain()
        st.session_state.engine_run_results = {"engine": eng, "summary": run_res}
        st.success(f"Inference complete! {run_res['fired_count']} rules fired.")
        st.rerun()


# =============================================================================
# VIEW 3: GOAL VERIFICATION (BACKWARD CHAINING)
# =============================================================================
elif mode == "Goal Verification (Backward Chaining)":
    st.markdown('<div class="main-header">Goal Verification via Backward Chaining</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Evaluate hypotheses, recursive subgoals, and identify missing facts using goal-directed backward search</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1.2])

    with c1:
        st.subheader("Target Hypothesis")
        predefined_goals = [
            ("min_form_factor", "6U", "Is a 6U form factor required?"),
            ("deorbit_regulation_compliant", False, "Will this mission violate FCC deorbit regulations?"),
            ("recommended_comm_downlink_band", "X_Band", "Is an X-Band downlink architecture required?"),
            ("solar_panel_type", "deployable_panels", "Are deployable solar panels necessary?"),
            ("adcs_actuator_type", "3_axis_reaction_wheel_cluster", "Are 3-axis reaction wheels required for pointing?"),
            ("deep_space_regime", True, "Does this mission qualify as deep space exploration?"),
        ]

        selected_goal_idx = st.selectbox(
            "Select Predefined Hypothesis:",
            range(len(predefined_goals)),
            format_func=lambda i: predefined_goals[i][2]
        )
        target_f, target_v, _ = predefined_goals[selected_goal_idx]

        st.markdown(f"**Target Fact:** `{target_f}`\n\n**Expected Value:** `{target_v}`")

        eval_btn = st.button("Evaluate Hypothesis (Backward Chain) 🔍")

    with c2:
        st.subheader("Backward Chaining Proof Tree")
        if eval_btn:
            eng = InferenceEngine(kb)
            # Seed current working memory
            for k, v in st.session_state.working_facts.items():
                eng.working_memory.set(k, v, source="working_memory")

            result = eng.backward_chain(target_f, target_v)

            if result["success"]:
                st.success(f"🎯 **HYPOTHESIS PROVEN TRUE!**\n\nTarget `{target_f} == {target_v}` is satisfied.")
                st.markdown(f"**Derived by Rule:** `{result.get('rule_id', 'Direct Assert')}` — *{result.get('rule_name', '')}*")
                st.markdown(f"**Rationale:** {result.get('rationale', '')}")
            else:
                st.warning(f"❌ **HYPOTHESIS UNPROVEN / FALSE**\n\nTarget `{target_f} == {target_v}` could not be established.")
                st.markdown(f"**Reason:** {result.get('reason', '')}")
                if result.get("missing_facts"):
                    st.markdown("**Missing Antecedent Facts Needed:**")
                    for mf in result["missing_facts"]:
                        st.markdown(f"- ❓ `{mf}`")

            with st.expander("Detailed Proof Tree JSON", expanded=True):
                st.json(result)


# =============================================================================
# VIEW 4: RULE EXPLORER
# =============================================================================
elif mode == "Rule Explorer":
    st.markdown('<div class="main-header">Knowledge Base Rule Explorer</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Inspect and filter all <b>{kb.rule_count} production rules</b> across CubeSat engineering subsystems</div>', unsafe_allow_html=True)

    col_filter, col_rules = st.columns([1, 2.5])

    with col_filter:
        st.subheader("Filter Rules")
        cats = ["All"] + sorted(list(set(r.category for r in kb.rules.values())))
        selected_cat = st.selectbox("Subsystem Category", cats)
        search_kw = st.text_input("Search Keyword in Rule / Rationale", "")
        min_salience = st.slider("Minimum Salience (Priority)", 0, 100, 0)

    with col_rules:
        filtered_rules = []
        for r in kb.rules.values():
            if selected_cat != "All" and r.category != selected_cat:
                continue
            if r.salience < min_salience:
                continue
            if search_kw:
                kw = search_kw.lower()
                if kw not in r.name.lower() and kw not in r.id.lower() and kw not in r.rationale.lower():
                    continue
            filtered_rules.append(r)

        st.markdown(f"**Displaying {len(filtered_rules)} of {kb.rule_count} rules:**")
        
        for r in filtered_rules:
            with st.expander(f"[{r.category.upper()}] {r.id}: {r.name} (Salience: {r.salience})"):
                st.markdown(f"**Rationale:** *{r.rationale}*")
                st.markdown(f"**Reference:** `{r.reference}`")
                
                c_if, c_then = st.columns(2)
                with c_if:
                    st.markdown("**IF Conditions:**")
                    for c in r.conditions:
                        st.markdown(f"- `{c.fact_name}` **{c.operator}** `{c.value}`")
                with c_then:
                    st.markdown("**THEN Deductions:**")
                    for a in r.actions:
                        st.markdown(f"- `{a.fact_name}` = **`{a.value}`** *(Category: {a.category})*")


# =============================================================================
# VIEW 5: KNOWLEDGE BASE EXPLORER
# =============================================================================
elif mode == "Knowledge Base Explorer":
    st.markdown('<div class="main-header">Domain Facts & Component Specifications</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Search and inspect all <b>{kb.fact_count} domain assertions</b> in the knowledge base</div>', unsafe_allow_html=True)

    c_filter, c_data = st.columns([1, 3])

    with c_filter:
        st.subheader("Filter Assertions")
        f_cats = ["All"] + sorted(list(set(f.category for f in kb.facts.values())))
        sel_fcat = st.selectbox("Category", f_cats)
        search_f = st.text_input("Search Fact Name or Description", "")

    with c_data:
        facts_list = []
        for f in kb.facts.values():
            if sel_fcat != "All" and f.category != sel_fcat:
                continue
            if search_f:
                kw = search_f.lower()
                if kw not in f.name.lower() and kw not in f.description.lower() and kw not in f.id.lower():
                    continue
            facts_list.append({
                "ID": f.id,
                "Category": f.category,
                "Fact Name": f.name,
                "Value": str(f.value),
                "Unit": f.unit or "",
                "Description": f.description
            })
        df_facts = pd.DataFrame(facts_list)
        st.markdown(f"**Found {len(df_facts)} domain assertions:**")
        st.dataframe(df_facts, use_container_width=True, height=500)


# =============================================================================
# VIEW 6: SYSTEM DOCUMENTATION
# =============================================================================
elif mode == "System Documentation":
    st.markdown('<div class="main-header">OrbitForge Architectural Documentation</div>', unsafe_allow_html=True)
    st.markdown("""
### 1. System Overview
OrbitForge is an academic rule-based Expert System designed to synthesize complete, flight-standard CubeSat mission configurations based on user specifications and orbital mechanics / engineering constraints.

### 2. Knowledge Representation
- **Explicit Production Rules (112 Rules)**: Represented as IF-THEN structures with:
  - `id`: Unique identifier (e.g., `RULE_PWR_001`).
  - `salience`: Integer priority used in conflict resolution.
  - `conditions`: List of antecedent clauses evaluated against working memory.
  - `actions`: Consequent deductions asserted into working memory upon firing.
  - `rationale`: Human-readable engineering justification for explanation generation.
- **Domain Assertions (386 Facts)**: Cataloged physical constants, component specifications, launch limits, and standard values stored separately in `knowledge_base/facts.json`.

### 3. Inference Mechanisms
- **Forward Chaining (Data-Driven)**:
  - Iteratively executes the Match-Resolve-Act cycle until quiescence.
  - **Conflict Resolution Strategy**:
    1. *Salience (Priority)*: Higher salience rules execute first.
    2. *Specificity (Complexity)*: Rules with more conditions execute before broader rules.
    3. *Definition Order*: Stable tie-breaking based on rule ID order.
- **Backward Chaining (Goal-Directed)**:
  - Recursively evaluates whether target hypotheses can be satisfied through working memory or candidate rule chains.
  - Generates proof trees and isolates missing antecedent facts.
- **Execution Tracer & Explanation Facility**:
  - Maintains timestamped audit logs of all rule firings and explains *Why* deductions were made.

### 4. Natural Language Interface
- Extracts engineering entities (payloads, orbits, altitudes, power, durations, organizations) from ordinary English.
- Evaluates missing mission parameters and queries the user with context-aware follow-up prompts.
- Translates conversational input directly into working memory facts for the deterministic inference engine.

### 5. Assumptions and Limitations
- The knowledge base incorporates standards from NASA CDS Rev 14, ESA ECSS, and FCC orbital debris guidelines.
- Numerical computations (such as solar power scaling and RF path loss) use first-order physical models.
- Hardware implementations should verify detailed structural CAD and thermal finite element analyses prior to flight fabrication.
    """)
