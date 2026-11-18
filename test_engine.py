"""
Unit tests for the Inference Engine:
- Forward Chaining
- Backward Chaining
- Conflict Resolution Strategy (Salience, Specificity, Definition Order)
- Quiescence and Loop Prevention
- Explanation Facility
"""

import pytest
from expert_system.knowledge import KnowledgeBase, Rule, Condition, Action
from expert_system.engine import InferenceEngine, WorkingMemory


@pytest.fixture
def test_engine():
    kb = KnowledgeBase("knowledge_base/facts.json", "knowledge_base/rules.json")
    return InferenceEngine(kb)


def test_working_memory_crud():
    wm = WorkingMemory()
    wm.set("orbit_altitude_km", 550, category="orbit", unit="km")
    assert wm.has("orbit_altitude_km")
    assert wm.get_value("orbit_altitude_km") == 550
    assert wm.get_value("nonexistent", default=42) == 42


def test_forward_chaining_leo_sar(test_engine):
    # Setup working memory for SAR mission
    test_engine.reset()
    test_engine.working_memory.set("payload_type", "synthetic_aperture_radar_sar")
    test_engine.working_memory.set("orbit_altitude_km", 550)
    test_engine.working_memory.set("has_propulsion_system", False)
    test_engine.working_memory.set("has_drag_sail", False)

    summary = test_engine.forward_chain()
    
    assert summary["fired_count"] > 0
    assert summary["quiescence_reached"] is True

    # Check deductions
    wm = test_engine.working_memory
    assert wm.get_value("min_form_factor") == "6U"
    assert wm.get_value("peak_power_requirement_w") == 120.0
    # SAR high data rate should deduce X_Band or Optical_Laser
    assert wm.get_value("recommended_comm_downlink_band") in ["X_Band", "Optical_Laser"]
    # Deorbit check for 550km shouldn't trigger RULE_ORB_001 (>600km)
    assert wm.get_value("deorbit_regulation_compliant") is None


def test_forward_chaining_high_orbit_deorbit_violation(test_engine):
    test_engine.reset()
    test_engine.working_memory.set("orbit_altitude_km", 750)
    test_engine.working_memory.set("has_propulsion_system", False)
    test_engine.working_memory.set("has_drag_sail", False)

    test_engine.forward_chain()
    wm = test_engine.working_memory

    # Should trigger deorbit non-compliance rule
    assert wm.get_value("deorbit_regulation_compliant") is False
    assert wm.get_value("recommended_deorbit_device") == "drag_sail_or_propulsion"
    # Over 650km, should also deduce delta-v
    assert wm.get_value("required_deorbit_delta_v_ms") == 120.0


def test_conflict_resolution_salience():
    # Construct a small dedicated KB to test conflict resolution ordering
    kb = KnowledgeBase()
    # Rule A: salience 50
    rule_a = Rule(
        id="R_A", name="Rule A", category="test", salience=50,
        conditions=[Condition("input", "==", 1)],
        actions=[Action("output", "from_A", "test")],
        rationale="Rule A rationale"
    )
    # Rule B: salience 90
    rule_b = Rule(
        id="R_B", name="Rule B", category="test", salience=90,
        conditions=[Condition("input", "==", 1)],
        actions=[Action("output", "from_B", "test")],
        rationale="Rule B rationale"
    )
    kb.rules = {"R_A": rule_a, "R_B": rule_b}

    engine = InferenceEngine(kb)
    engine.working_memory.set("input", 1)
    
    # Conflict set resolution
    resolved = engine.resolve_conflicts([rule_a, rule_b])
    assert resolved[0].id == "R_B"
    assert resolved[1].id == "R_A"

    # Forward chain: R_B fires first
    engine.forward_chain()
    assert engine.trace[0].rule_id == "R_B"


def test_conflict_resolution_specificity():
    kb = KnowledgeBase()
    # Rule General: 1 condition
    rule_gen = Rule(
        id="R_GEN", name="Rule General", category="test", salience=50,
        conditions=[Condition("input", "==", 1)],
        actions=[Action("out", "gen", "test")],
        rationale="gen"
    )
    # Rule Specific: 2 conditions
    rule_spec = Rule(
        id="R_SPEC", name="Rule Specific", category="test", salience=50,
        conditions=[Condition("input", "==", 1), Condition("sub", "==", 2)],
        actions=[Action("out", "spec", "test")],
        rationale="spec"
    )
    kb.rules = {"R_GEN": rule_gen, "R_SPEC": rule_spec}

    engine = InferenceEngine(kb)
    engine.working_memory.set("input", 1)
    engine.working_memory.set("sub", 2)

    resolved = engine.resolve_conflicts([rule_gen, rule_spec])
    assert resolved[0].id == "R_SPEC"


def test_backward_chaining_proven(test_engine):
    test_engine.reset()
    # Assert conditions for RULE_STR_001
    test_engine.working_memory.set("payload_type", "synthetic_aperture_radar_sar")

    # Goal: Is min_form_factor == "6U"?
    result = test_engine.backward_chain(target_fact="min_form_factor", target_value="6U")
    assert result["success"] is True
    assert result["rule_id"] == "RULE_STR_001"


def test_backward_chaining_missing_facts(test_engine):
    test_engine.reset()
    # Working memory empty
    # Goal: Is min_form_factor == "6U"?
    result = test_engine.backward_chain(target_fact="min_form_factor", target_value="6U")
    assert result["success"] is False
    assert "payload_type" in result["missing_facts"]


def test_explanation_facility(test_engine):
    test_engine.reset()
    test_engine.working_memory.set("orbit_altitude_km", 750)
    test_engine.working_memory.set("has_propulsion_system", False)
    test_engine.working_memory.set("has_drag_sail", False)

    test_engine.forward_chain()
    explanation = test_engine.explain_fact("deorbit_regulation_compliant")
    
    assert explanation["exists"] is True
    assert explanation["source_type"] == "deduced_by_rule"
    assert "RULE_ORB_001" in explanation["rule_id"]
    assert "rationale" in explanation
