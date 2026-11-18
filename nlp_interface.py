"""
OrbitForge Natural Language Interface Module.

Enables ordinary English interaction for CubeSat mission configuration:
- Extracts engineering facts (mission type, payload, orbit altitude, orbit type, form factor,
  power bounds, data volume, duration, organization) using regex and semantic mapping.
- Analyzes missing mission-critical parameters.
- Formulates context-aware follow-up clarification questions.
- Bridges extracted facts into the deterministic rule-based inference engine.
"""

import re
from typing import Any, Dict, List, Optional, Tuple


class NaturalLanguageInterface:
    """Extracts facts from natural language text and generates targeted follow-up queries."""

    # Essential mission dimensions needed for a complete baseline CubeSat design
    CRITICAL_DIMENSIONS = [
        ("payload_type", "What type of payload instrument will the satellite carry (e.g. optical camera, SAR radar, hyperspectral spectrometer, IoT/AIS, radiation dosimeter)?"),
        ("orbit_altitude_km", "What is your target orbital altitude in kilometers (e.g. 400 km, 550 km, 700 km)?"),
        ("orbit_type", "What orbit geometry do you plan to use (e.g. Sun-Synchronous SSO, Equatorial, Inclined LEO, or Lunar)?"),
        ("form_factor", "Do you have a desired CubeSat form factor in mind (e.g. 1U, 2U, 3U, 6U, 12U), or would you like OrbitForge to recommend one?"),
        ("mission_organization_type", "What is the mission organization type (university/academic, commercial, or government/defense)?"),
    ]

    def extract_facts(self, text: str) -> Dict[str, Any]:
        """Extracts structured mission facts from ordinary English text."""
        facts: Dict[str, Any] = {}
        text_lower = text.lower()

        # 1. Payload Extraction
        if re.search(r"\b(sar|synthetic aperture radar|radar imaging)\b", text_lower):
            facts["payload_type"] = "synthetic_aperture_radar_sar"
            facts["mission_type"] = "sar_imaging"
        elif re.search(r"\b(hyperspectral|spectrometer|spectral imaging)\b", text_lower):
            facts["payload_type"] = "hyperspectral_imaging"
            facts["mission_type"] = "hyperspectral_imaging"
        elif re.search(r"\b(thermal infrared|tir|thermal camera|infrared sensor|lwir)\b", text_lower):
            facts["payload_type"] = "earth_obs_thermal_tir"
            facts["mission_type"] = "earth_observation"
        elif re.search(r"\b(optical|camera|rgb|earth observation|imagery|photograph)\b", text_lower):
            facts["payload_type"] = "earth_obs_optical_rgb"
            facts["mission_type"] = "earth_observation"
        elif re.search(r"\b(ais|ship tracking|maritime|vessel)\b", text_lower):
            facts["payload_type"] = "iot_ais_receiver"
            facts["mission_type"] = "iot_telecom"
        elif re.search(r"\b(iot|lora|telecom|store-and-forward|sensor relay)\b", text_lower):
            facts["payload_type"] = "iot_lora_transceiver"
            facts["mission_type"] = "iot_telecom"
        elif re.search(r"\b(radiation|dosimeter|space weather|cosmic ray)\b", text_lower):
            facts["payload_type"] = "radiation_dosimeter_dos"
            facts["mission_type"] = "space_weather"
        elif re.search(r"\b(plasma|langmuir|ionosphere|sheath)\b", text_lower):
            facts["payload_type"] = "langmuir_plasma_probe"
            facts["mission_type"] = "space_weather"
        elif re.search(r"\b(biology|microfluidics|cell|yeast|life science|lab-on-a-chip)\b", text_lower):
            facts["payload_type"] = "biology_microfluidics_lab"
            facts["mission_type"] = "biology_experiment"

        # 2. Orbit Altitude Extraction
        alt_match = re.search(r"(\d{3,4})\s*(km|kilometers|kilometer)", text_lower)
        if alt_match:
            facts["orbit_altitude_km"] = float(alt_match.group(1))
        elif re.search(r"\biss\b|international space station", text_lower):
            facts["orbit_altitude_km"] = 400.0
            facts["orbit_inclination_deg"] = 51.6

        # 3. Orbit Type Extraction
        if re.search(r"\b(sso|sun[\s-]synchronous|polar)\b", text_lower):
            facts["orbit_type"] = "sso"
            facts["orbit_inclination_deg"] = 97.5
        elif re.search(r"\b(equatorial)\b", text_lower):
            facts["orbit_type"] = "equatorial"
            facts["orbit_inclination_deg"] = 0.0
        elif re.search(r"\b(lunar|moon|translunar)\b", text_lower):
            facts["orbit_type"] = "lunar_orbit"
        elif re.search(r"\b(deep space|interplanetary|mars)\b", text_lower):
            facts["orbit_type"] = "interplanetary"
        elif "orbit_altitude_km" in facts and "orbit_type" not in facts:
            facts["orbit_type"] = "leo"

        # 4. Form Factor Extraction
        size_match = re.search(r"\b(0\.5|1|1\.5|2|3|6|8|12|16|27)\s*u\b", text_lower)
        if size_match:
            val = size_match.group(1)
            facts["form_factor"] = f"{val}U"

        # 5. Organization Type
        if re.search(r"\b(university|student|academic|college|amateur|research institute)\b", text_lower):
            facts["mission_organization_type"] = "university"
        elif re.search(r"\b(commercial|startup|company|for-profit|constellation company)\b", text_lower):
            facts["mission_organization_type"] = "commercial"
        elif re.search(r"\b(military|defense|air force|space force|classified)\b", text_lower):
            facts["mission_organization_type"] = "defense"

        # 6. Mission Duration
        dur_match = re.search(r"(\d+)\s*(year|years|yr|yrs)", text_lower)
        if dur_match:
            facts["mission_duration_years"] = float(dur_match.group(1))
        else:
            month_match = re.search(r"(\d+)\s*(month|months|mo)", text_lower)
            if month_match:
                facts["mission_duration_years"] = round(float(month_match.group(1)) / 12.0, 2)

        # 7. Explicit Power requirement
        pwr_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:watts?|w)\s*(?:average|avg|consumption|draw)", text_lower)
        if pwr_match:
            facts["average_power_consumption_w"] = float(pwr_match.group(1))
            facts["peak_power_requirement_w"] = float(pwr_match.group(1)) * 2.0

        # 8. Propulsion / Drag Sail mentions
        if re.search(r"\b(with propulsion|has propulsion|chemical thruster|electric propulsion|propulsion included)\b", text_lower):
            facts["has_propulsion_system"] = True
            facts["requires_propulsion"] = True
        elif re.search(r"\b(no propulsion|propulsionless|passive decay|without propulsion)\b", text_lower):
            facts["has_propulsion_system"] = False
            facts["requires_propulsion"] = False

        if re.search(r"\b(drag sail|aerodynamic sail|deorbit sail)\b", text_lower):
            facts["has_drag_sail"] = True
        elif re.search(r"\b(no sail|no drag sail)\b", text_lower):
            facts["has_drag_sail"] = False

        # 9. Mission status default
        facts["mission_status"] = "in_design"

        return facts

    def analyze_missing_information(self, current_facts: Dict[str, Any]) -> List[Tuple[str, str]]:
        """Identifies which critical parameters are absent from working memory."""
        missing = []
        for key, question in self.CRITICAL_DIMENSIONS:
            if key not in current_facts or current_facts[key] is None:
                missing.append((key, question))
        return missing

    def generate_response(self, user_input: str, current_facts: Dict[str, Any],
                          engine_summary: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processes user conversational message, updates fact base,
        evaluates readiness, and produces dynamic follow-up prompts.
        """
        extracted = self.extract_facts(user_input)
        updated_facts = dict(current_facts)
        updated_facts.update(extracted)

        missing = self.analyze_missing_information(updated_facts)

        feedback_notes = []
        if extracted:
            for k, v in extracted.items():
                if k != "mission_status":
                    feedback_notes.append(f"• **{k.replace('_', ' ').title()}**: `{v}`")

        # Determine prompt
        if missing:
            next_param, next_question = missing[0]
            if feedback_notes:
                msg = (
                    f"I have extracted the following parameters from your description:\n\n"
                    + "\n".join(feedback_notes)
                    + f"\n\nTo refine your CubeSat mission configuration, please clarify:\n\n👉 **{next_question}**"
                )
            else:
                msg = (
                    f"I've received your mission overview. To build the deterministic engineering configuration, "
                    f"could you tell me:\n\n👉 **{next_question}**"
                )
            ready_to_infer = False
        else:
            msg = (
                f"✅ **Mission parameters established!** All critical dimensions have been identified:\n\n"
                + "\n".join(feedback_notes)
                + "\n\nThe deterministic inference engine has evaluated production rules across all CubeSat subsystems."
            )
            ready_to_infer = True

        return {
            "reply": msg,
            "extracted_facts": extracted,
            "all_facts": updated_facts,
            "missing_parameters": [m[0] for m in missing],
            "ready_to_infer": ready_to_infer
        }
