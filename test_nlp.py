"""
Tests for NaturalLanguageInterface:
- Extraction of mission parameters (orbit, altitude, payload, form factor, duration, org)
- Handling of conversational follow-up questions
- Missing parameter analysis
"""

import pytest
from expert_system.nlp_interface import NaturalLanguageInterface


@pytest.fixture
def nlp():
    return NaturalLanguageInterface()


def test_full_mission_extraction(nlp):
    text = (
        "We are designing a 6U CubeSat for an academic university mission conducting "
        "earth observation with an optical RGB camera at 500 km Sun-Synchronous Orbit (SSO) "
        "with an expected mission duration of 2 years."
    )
    facts = nlp.extract_facts(text)
    assert facts["form_factor"] == "6U"
    assert facts["mission_organization_type"] == "university"
    assert facts["payload_type"] == "earth_obs_optical_rgb"
    assert facts["orbit_altitude_km"] == 500.0
    assert facts["orbit_type"] == "sso"
    assert facts["mission_duration_years"] == 2.0


def test_partial_extraction_and_missing_analysis(nlp):
    text = "We want to build a CubeSat to track maritime AIS signals."
    facts = nlp.extract_facts(text)
    assert facts["payload_type"] == "iot_ais_receiver"
    assert "orbit_altitude_km" not in facts

    missing = nlp.analyze_missing_information(facts)
    missing_keys = [m[0] for m in missing]
    assert "orbit_altitude_km" in missing_keys
    assert "form_factor" in missing_keys


def test_conversational_response_generation(nlp):
    # Initial message
    resp1 = nlp.generate_response("We are a university team building a SAR radar CubeSat.", {})
    assert resp1["ready_to_infer"] is False
    assert "synthetic_aperture_radar_sar" == resp1["extracted_facts"]["payload_type"]
    assert len(resp1["missing_parameters"]) > 0

    # Follow-up adding altitude and orbit
    resp2 = nlp.generate_response("We will fly at 550 km in Sun-Synchronous Orbit.", resp1["all_facts"])
    assert resp2["all_facts"]["orbit_altitude_km"] == 550.0
    assert resp2["all_facts"]["orbit_type"] == "sso"

    # Follow-up adding form factor
    resp3 = nlp.generate_response("The form factor will be 6U.", resp2["all_facts"])
    assert resp3["ready_to_infer"] is True
