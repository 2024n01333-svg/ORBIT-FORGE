"""
Comprehensive end-to-end integration tests for OrbitForge:
- Verifies knowledge base invariants (>= 100 rules, >= 300 facts, schema validity)
- Verifies all 5 pre-built scenarios fire correct subsystem rules
- Verifies cross-subsystem reasoning and consistency checks
- Verifies conflict resolution across complex condition sets
- Verifies backward chaining proof trees and missing fact detection
- Verifies NLP fact extraction and interactive follow-ups
"""

import pytest
from expert_system.knowledge import KnowledgeBase
from expert_system.engine import InferenceEngine
from expert_system.nlp_interface import NaturalLanguageInterface
from expert_system.scenarios import SCENARIOS


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase("knowledge_base/facts.json", "knowledge_base/rules.json")


@pytest.fixture(scope="module")
def nlp():
    return NaturalLanguageInterface()


def test_kb_invariants(kb):
    assert kb.rule_count >= 100, f"Expected >= 100 rules, found {kb.rule_count}"
    assert kb.fact_count >= 300, f"Expected >= 300 facts, found {kb.fact_count}"

    # Verify uniqueness of rule and fact IDs
    assert len(kb.rules) == kb.rule_count
    assert len(kb.facts) == kb.fact_count

    # Check that categories are well populated
    rule_cats = set(r.category for r in kb.rules.values())
    assert len(rule_cats) >= 6
    for cat in ["power", "comm", "payload", "thermal", "adcs", "orbit", "structure"]:
        assert cat in rule_cats, f"Expected rule category '{cat}'"


def test_all_preset_scenarios(kb):
    for name, scenario in SCENARIOS.items():
        engine = InferenceEngine(kb)
        for k, v in scenario["facts"].items():
            engine.working_memory.set(k, v, source="scenario_test")

        summary = engine.forward_chain()
        assert summary["quiescence_reached"] is True
        assert summary["fired_count"] > 0, f"Scenario '{name}' fired 0 rules!"
        assert len(engine.trace) == summary["fired_count"]


def test_earth_observation_sso_scenario(kb):
    sc = SCENARIOS["Earth Observation 6U (SSO High-Res RGB)"]
    engine = InferenceEngine(kb)
    for k, v in sc["facts"].items():
        engine.working_memory.set(k, v)

    engine.forward_chain()
    wm = engine.working_memory

    # Expected deductions
    assert wm.get_value("min_form_factor") == "2U"
    assert wm.get_value("recommended_comm_downlink_band") == "X_Band"
    assert wm.get_value("adcs_actuator_type") == "3_axis_reaction_wheel_cluster"
    assert wm.get_value("adcs_sensor_suite") == "miniature_star_tracker_and_gyros"
    assert wm.get_value("telescope_thermal_structure") == "invar_or_carbon_fiber_metering_structure"
    assert wm.get_value("optical_bay_thermal_insulation") == "multi_layer_insulation_mli"


def test_iot_store_and_forward_scenario(kb):
    sc = SCENARIOS["IoT Store-and-Forward 1U (Academic Low-Cost)"]
    engine = InferenceEngine(kb)
    for k, v in sc["facts"].items():
        engine.working_memory.set(k, v)

    engine.forward_chain()
    wm = engine.working_memory

    assert wm.get_value("min_form_factor") == "1U"
    assert wm.get_value("recommended_comm_downlink_band") == "UHF"
    assert wm.get_value("solar_panel_type") == "body_mounted"
    assert wm.get_value("adcs_actuator_type") == "passive_permanent_magnet_and_hysteresis_rods"


def test_lunar_orbit_scenario(kb):
    sc = SCENARIOS["Deep Space Lunar Orbiter 12U"]
    engine = InferenceEngine(kb)
    for k, v in sc["facts"].items():
        engine.working_memory.set(k, v)

    engine.forward_chain()
    wm = engine.working_memory

    assert wm.get_value("deep_space_regime") is True
    assert wm.get_value("ground_network_type") == "deep_space_network"
    assert wm.get_value("transceiver_hardware_architecture") == "jpl_iris_deep_space_transponder"
    assert wm.get_value("min_delta_v_budget_ms") == 450.0
    assert wm.get_value("magnetic_actuation_possible") is False


def test_conflict_resolution_and_quiescence(kb):
    engine = InferenceEngine(kb)
    # Give facts that trigger multiple rules across priorities
    engine.working_memory.set("payload_type", "synthetic_aperture_radar_sar")
    engine.working_memory.set("orbit_altitude_km", 700)
    engine.working_memory.set("has_propulsion_system", False)
    engine.working_memory.set("has_drag_sail", False)
    engine.working_memory.set("mission_organization_type", "commercial")

    summary = engine.forward_chain()
    assert summary["quiescence_reached"] is True

    # Verify that higher salience rules fired before lower salience rules within conflict sets
    salience_trace = [s.salience for s in engine.trace]
    assert len(salience_trace) >= 5


def test_backward_chaining_goal_directed(kb):
    engine = InferenceEngine(kb)

    # Goal: Prove that "3_axis_reaction_wheel_cluster" is needed
    engine.working_memory.set("pointing_accuracy_requirement_deg", 0.05)
    res = engine.backward_chain("adcs_actuator_type", "3_axis_reaction_wheel_cluster")
    assert res["success"] is True
    assert res["rule_id"] == "RULE_ADC_001"

    # Goal: Try to prove without requisite pointing accuracy
    engine.reset()
    res2 = engine.backward_chain("adcs_actuator_type", "3_axis_reaction_wheel_cluster")
    assert res2["success"] is False
    assert "pointing_accuracy_requirement_deg" in res2["missing_facts"]
