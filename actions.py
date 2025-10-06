# actions.py
from typing import Any, Dict, Text, List, Optional
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

class ValidateHospitalForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_hospital_form"

    def validate_location(
        self, value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        if value and value.strip():
            return {"location": value.strip()}
        dispatcher.utter_message(text="Please provide a valid area or pincode.")
        return {"location": None}

    def validate_radius_km(
        self, value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        try:
            v = float(value)
            if v <= 0:
                raise ValueError()
            return {"radius_km": v}
        except Exception:
            dispatcher.utter_message(text="Radius should be a positive number (km). Try 3, 5, or 10.")
            return {"radius_km": None}

    def validate_specialty(
        self, value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        # accept anything; treat "any" as general
        if not value:
            return {"specialty": "general"}
        v = value.strip().lower()
        if v in {"", "any", "all", "na", "none"}:
            v = "general"
        return {"specialty": v}

class ActionFindHospitals(Action):
    def name(self) -> Text:
        return "action_find_hospitals"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:
        loc: Optional[str] = tracker.get_slot("location")
        spec: Optional[str] = tracker.get_slot("specialty") or "general"
        radius = tracker.get_slot("radius_km") or 5
        # ✅ GUARANTEED reply (mocked list so you see something)
        lines = [
            f"1) MediCare Multi-Speciality — Hazratganj (📞 +91-522-111111)",
            f"2) CityCare Hospital — Sapru Marg (📞 +91-522-222222)",
            f"3) ApolloMed Clinic & ER — Near Saharaganj (📞 +91-522-333333)",
        ]
        msg = f"Hospitals near **{loc}** within **{radius} km** for **{spec}**:\n" + "\n".join(lines)
        dispatcher.utter_message(text=msg)
        return []
