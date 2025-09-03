"""
Utility functions for extracting and processing patient context data efficiently.
Focuses on token optimization and relevant clinical information extraction.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from settings import logger


def extract_relevant_intake_context(intake_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant patient intake information for progress note generation.
    Focuses on high-value clinical data while minimizing token usage.
    """
    if not intake_data:
        return {}
    
    relevant_context = {}
    
    # Chief complaint and present illness (HIGH PRIORITY)
    if present_illness := intake_data.get("presentIllness"):
        chief_complaint = ""
        pain_info = ""
        
        # Extract chief complaint
        if body_parts := present_illness.get("bodyPartLat", []):
            for body_part in body_parts:
                if pain_symptoms := body_part.get("painSymptoms", {}):
                    if cc := pain_symptoms.get("ChiefComplaint"):
                        chief_complaint = cc
                    
                    # Extract pain characteristics
                    pain_details = []
                    if intensity := pain_symptoms.get("Intensity"):
                        pain_details.append(f"Intensity: {intensity}/10")
                    if pain_types := pain_symptoms.get("Type", []):
                        types = [t.get("Value", "") for t in pain_types if t.get("Value")]
                        if types:
                            pain_details.append(f"Type: {', '.join(types)}")
                    if worsened_by := pain_symptoms.get("WorsenedBy", []):
                        factors = [w.get("Value", "") for w in worsened_by if w.get("Value")]
                        if factors:
                            pain_details.append(f"Worsened by: {', '.join(factors)}")
                    if improved_by := pain_symptoms.get("ImprovedBy", []):
                        factors = [i.get("Value", "") for i in improved_by if i.get("Value")]
                        if factors:
                            pain_details.append(f"Improved by: {', '.join(factors)}")
                    
                    if pain_details:
                        pain_info = "; ".join(pain_details)
        
        if visit_reason := present_illness.get("visitReason"):
            relevant_context["chief_complaint"] = f"{visit_reason}. {chief_complaint}".strip()
        elif chief_complaint:
            relevant_context["chief_complaint"] = chief_complaint
            
        if pain_info:
            relevant_context["pain_characteristics"] = pain_info
    
    # Current medications (HIGH PRIORITY)
    if medications := intake_data.get("medications", {}).get("activeMedications", []):
        current_meds = []
        for med in medications[-10:]:  # Limit to recent 10 medications
            med_name = med.get("medication", "")
            instructions = med.get("instructions", "")
            if med_name:
                if instructions:
                    current_meds.append(f"{med_name}: {instructions}")
                else:
                    current_meds.append(med_name)
        if current_meds:
            relevant_context["current_medications"] = current_meds
    
    # Allergies (HIGH PRIORITY)
    if allergies := intake_data.get("allergies", {}).get("activeAllergies", []):
        allergy_list = []
        for allergy in allergies:
            allergy_name = allergy.get("allergy", "")
            symptom = allergy.get("symptom", "")
            severity = allergy.get("severity", "")
            if allergy_name:
                allergy_info = allergy_name
                if symptom:
                    allergy_info += f" (symptoms: {symptom})"
                if severity:
                    allergy_info += f" - {severity}"
                allergy_list.append(allergy_info)
        if allergy_list:
            relevant_context["allergies"] = allergy_list
    
    # Medical history (MEDIUM PRIORITY)
    if medical_history := intake_data.get("medicalHistory", {}).get("conditions", []):
        conditions = []
        for condition in medical_history:
            desc = condition.get("description", "")
            status = condition.get("status", "")
            if desc:
                condition_info = desc
                if status:
                    condition_info += f" ({status})"
                conditions.append(condition_info)
        if conditions:
            relevant_context["medical_conditions"] = conditions
    
    # Surgical history (MEDIUM PRIORITY) 
    if surgical_history := intake_data.get("surgicalHistory", {}).get("procedures", []):
        surgeries = []
        for surgery in surgical_history:
            procedure = surgery.get("procedure", "")
            time_since = surgery.get("timeSinceSurgery", "")
            if procedure:
                surgery_info = procedure
                if time_since:
                    surgery_info += f" ({time_since} ago)"
                surgeries.append(surgery_info)
        if surgeries:
            relevant_context["surgical_history"] = surgeries
    
    # Social history relevant to current visit (LOW-MEDIUM PRIORITY)
    if social_history := intake_data.get("socialHistory", {}):
        social_factors = []
        
        # Smoking - relevant for many conditions
        if social_history.get("smoking") == "Yes":
            if smoking_data := social_history.get("smokingData", {}):
                smoking_info = "Current smoker"
                if how_much := smoking_data.get("howMuch"):
                    smoking_info += f" ({how_much})"
                if how_long := smoking_data.get("howLong"):
                    smoking_info += f" for {how_long}"
                social_factors.append(smoking_info)
        
        # Alcohol - relevant for medication interactions
        if social_history.get("alcoholConsumption") == "yes":
            if alcohol_data := social_history.get("alcohol", {}):
                drinks_per_week = alcohol_data.get("drinksPerWeek", "")
                if drinks_per_week:
                    social_factors.append(f"Alcohol: {drinks_per_week} drinks/week")
        
        if social_factors:
            relevant_context["social_history"] = social_factors
    
    return relevant_context


def extract_historical_clinical_context(dictations: List[Dict[str, Any]], current_patient_id: str) -> Dict[str, Any]:
    """
    Extract relevant clinical context from historical progress notes for the same patient.
    Focuses on trends, stability, and key clinical patterns.
    """
    if not dictations:
        return {}
    
    # Filter dictations for the same patient
    patient_dictations = []
    for item in dictations:
        dictation = item.get("dictation", {})
        if dictation.get("patientId") == current_patient_id:
            patient_dictations.append(dictation)
    
    if not patient_dictations:
        return {}
    
    # Sort by date (most recent first)
    patient_dictations.sort(key=lambda x: x.get("dateOfService", ""), reverse=True)
    
    historical_context = {
        "visit_count": len(patient_dictations),
        "date_range": {
            "most_recent": patient_dictations[0].get("dateOfService", ""),
            "earliest": patient_dictations[-1].get("dateOfService", "")
        }
    }
    
    # Extract key clinical themes from recent visits (last 3 visits)
    recent_visits = patient_dictations[:3]
    clinical_themes = {
        "conditions_mentioned": set(),
        "medications_mentioned": set(),
        "procedures_mentioned": set(),
        "stability_indicators": []
    }
    
    for visit in recent_visits:
        file_content = visit.get("fileContent", {}).get("data", "")
        if file_content:
            # Extract key clinical information
            content_lower = file_content.lower()
            
            # Common conditions
            conditions = [
                "diabetes", "hypertension", "atrial fibrillation", "heart failure",
                "copd", "asthma", "arthritis", "depression", "anxiety"
            ]
            for condition in conditions:
                if condition in content_lower:
                    clinical_themes["conditions_mentioned"].add(condition)
            
            # Stability indicators
            if "stable" in content_lower:
                clinical_themes["stability_indicators"].append(f"{visit.get('dateOfService', '')}: Stable condition noted")
            if "well-controlled" in content_lower:
                clinical_themes["stability_indicators"].append(f"{visit.get('dateOfService', '')}: Well-controlled")
            if "worsening" in content_lower or "deteriorating" in content_lower:
                clinical_themes["stability_indicators"].append(f"{visit.get('dateOfService', '')}: Concerning changes noted")
    
    # Convert sets to lists for JSON serialization
    if clinical_themes["conditions_mentioned"]:
        historical_context["recurring_conditions"] = list(clinical_themes["conditions_mentioned"])
    
    if clinical_themes["stability_indicators"]:
        historical_context["clinical_trends"] = clinical_themes["stability_indicators"][-3:]  # Last 3 trends
    
    # Extract provider continuity
    providers = list(set(visit.get("provider", "") for visit in patient_dictations if visit.get("provider")))
    if providers:
        historical_context["providers"] = providers
    
    return historical_context


def format_context_for_prompt(
    intake_context: Dict[str, Any], 
    historical_context: Dict[str, Any],
    current_transcription: str,
    patient_info: Dict[str, str]
) -> str:
    """
    Format the extracted context into an optimized prompt structure.
    Balances comprehensive information with token efficiency.
    """
    context_sections = []
    
    # Patient information
    context_sections.append(f"""PATIENT INFORMATION:
Name: {patient_info.get('patient_name', 'Unknown')}
ID: {patient_info.get('patient_id', 'Unknown')}
Date of Birth: {patient_info.get('patient_date_of_birth', 'Unknown')}
Date of Service: {patient_info.get('date_of_service', 'Unknown')}
Provider: {patient_info.get('provider', 'Unknown')}""")
    
    # Current visit context from intake
    if intake_context:
        intake_section = ["CURRENT VISIT CONTEXT:"]
        
        if chief_complaint := intake_context.get("chief_complaint"):
            intake_section.append(f"Chief Complaint: {chief_complaint}")
        
        if pain_chars := intake_context.get("pain_characteristics"):
            intake_section.append(f"Pain Details: {pain_chars}")
        
        if allergies := intake_context.get("allergies"):
            intake_section.append(f"Allergies: {'; '.join(allergies)}")
        
        if meds := intake_context.get("current_medications"):
            intake_section.append(f"Current Medications: {'; '.join(meds[:5])}")  # Limit to 5 most recent
        
        if conditions := intake_context.get("medical_conditions"):
            intake_section.append(f"Active Conditions: {'; '.join(conditions)}")
        
        if surgeries := intake_context.get("surgical_history"):
            intake_section.append(f"Recent Surgeries: {'; '.join(surgeries[:3])}")  # Limit to 3 most recent
        
        if social := intake_context.get("social_history"):
            intake_section.append(f"Relevant Social History: {'; '.join(social)}")
        
        context_sections.append("\n".join(intake_section))
    
    # Historical clinical context
    if historical_context:
        historical_section = ["HISTORICAL CLINICAL CONTEXT:"]
        
        if historical_context.get("visit_count", 0) > 1:
            historical_section.append(f"Previous visits: {historical_context['visit_count']} visits on record")
        
        if recurring_conditions := historical_context.get("recurring_conditions"):
            historical_section.append(f"Recurring conditions: {', '.join(recurring_conditions)}")
        
        if trends := historical_context.get("clinical_trends"):
            historical_section.append(f"Recent trends: {'; '.join(trends)}")
        
        if providers := historical_context.get("providers"):
            if len(providers) > 1:
                historical_section.append(f"Provider continuity: Multiple providers ({', '.join(providers)})")
            else:
                historical_section.append(f"Provider continuity: Consistent care with {providers[0]}")
        
        context_sections.append("\n".join(historical_section))
    
    # Current transcription
    context_sections.append(f"""CURRENT TRANSCRIPTION:
{current_transcription}""")
    
    return "\n\n".join(context_sections)


def log_context_metrics(intake_context: Dict[str, Any], historical_context: Dict[str, Any], session_id: str) -> None:
    """Log metrics about the context extraction for monitoring and optimization."""
    
    intake_fields = len(intake_context.keys()) if intake_context else 0
    historical_visits = historical_context.get("visit_count", 0) if historical_context else 0
    
    logger.debug("📊 Context Extraction Metrics",
                session_id=session_id,
                intake_fields_extracted=intake_fields,
                historical_visits_found=historical_visits,
                has_chief_complaint=bool(intake_context.get("chief_complaint")) if intake_context else False,
                has_medications=bool(intake_context.get("current_medications")) if intake_context else False,
                has_allergies=bool(intake_context.get("allergies")) if intake_context else False,
                has_clinical_trends=bool(historical_context.get("clinical_trends")) if historical_context else False)
