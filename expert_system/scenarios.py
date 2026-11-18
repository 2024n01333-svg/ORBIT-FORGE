"""
Preset CubeSat mission scenarios for OrbitForge.
Demonstrates various payloads, orbits, and operational constraints.
"""

SCENARIOS = {
    "Earth Observation 6U (SSO High-Res RGB)": {
        "description": "Commercial 6U Sun-Synchronous optical imaging satellite operating at 500 km with sub-3m ground sampling.",
        "input_text": "We are designing a commercial 6U CubeSat for high-resolution optical Earth observation at 500 km Sun-Synchronous Orbit (SSO) with a 3-year mission lifetime.",
        "facts": {
            "mission_type": "earth_observation",
            "payload_type": "earth_obs_optical_rgb",
            "form_factor": "6U",
            "orbit_altitude_km": 500.0,
            "orbit_type": "sso",
            "orbit_inclination_deg": 97.5,
            "mission_duration_years": 3.0,
            "mission_organization_type": "commercial",
            "daily_data_volume_mb": 15000,
            "pointing_accuracy_requirement_deg": 0.08,
            "has_propulsion_system": False,
            "has_drag_sail": False
        }
    },
    "IoT Store-and-Forward 1U (Academic Low-Cost)": {
        "description": "University educational 1U CubeSat relaying sensor data via UHF/LoRa from 400 km ISS-deployment orbit.",
        "input_text": "We are a university team building a 1U IoT LoRa telecom CubeSat deployed from the ISS at 400 km altitude for 1 year.",
        "facts": {
            "mission_type": "iot_telecom",
            "payload_type": "iot_lora_transceiver",
            "form_factor": "1U",
            "orbit_altitude_km": 400.0,
            "orbit_type": "leo",
            "orbit_inclination_deg": 51.6,
            "mission_duration_years": 1.0,
            "mission_organization_type": "university",
            "average_power_consumption_w": 2.5,
            "daily_data_volume_mb": 150,
            "pointing_accuracy_requirement_deg": 15.0,
            "has_propulsion_system": False,
            "has_drag_sail": False
        }
    },
    "Synthetic Aperture Radar (SAR) 12U High-Power": {
        "description": "High-power commercial radar imaging satellite operating at 550 km demanding deployable solar arrays and X-band downlink.",
        "input_text": "We are a commercial aerospace company building a 12U CubeSat carrying synthetic aperture radar (SAR) at 550 km SSO orbit.",
        "facts": {
            "mission_type": "sar_imaging",
            "payload_type": "synthetic_aperture_radar_sar",
            "form_factor": "12U",
            "orbit_altitude_km": 550.0,
            "orbit_type": "sso",
            "orbit_inclination_deg": 97.5,
            "mission_duration_years": 2.0,
            "mission_organization_type": "commercial",
            "pointing_accuracy_requirement_deg": 0.05,
            "has_propulsion_system": True,
            "has_drag_sail": False
        }
    },
    "Deep Space Lunar Orbiter 12U": {
        "description": "Interplanetary CubeSat entering lunar orbit equipped with Iris deep space transponder and green monopropellant.",
        "input_text": "We are designing a 12U deep space Lunar orbit CubeSat with propulsion and radiation hardening.",
        "facts": {
            "mission_type": "deep_space_exploration",
            "payload_type": "gamma_ray_burst_detector",
            "form_factor": "12U",
            "orbit_altitude_km": 100.0,
            "orbit_type": "lunar_orbit",
            "mission_duration_years": 1.5,
            "mission_organization_type": "commercial",
            "has_propulsion_system": True,
            "propulsion_type": "chemical_monoprop",
            "has_drag_sail": False
        }
    },
    "Maritime AIS Tracking 3U": {
        "description": "3U constellation satellite monitoring global commercial vessel tracking signals with VHF antennas.",
        "input_text": "Commercial 3U constellation satellite for maritime AIS ship tracking at 550 km SSO orbit with 3 years operational life.",
        "facts": {
            "mission_type": "iot_telecom",
            "payload_type": "iot_ais_receiver",
            "form_factor": "3U",
            "orbit_altitude_km": 550.0,
            "orbit_type": "sso",
            "orbit_inclination_deg": 97.5,
            "mission_duration_years": 3.0,
            "mission_organization_type": "commercial",
            "pointing_accuracy_requirement_deg": 3.0,
            "has_propulsion_system": False,
            "has_drag_sail": False
        }
    }
}
