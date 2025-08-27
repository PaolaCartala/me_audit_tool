"""Patient Code Mapper - Handles new vs. established patient code mappings."""

from typing import Dict, Optional
from settings import logger


class PatientCodeMapper:
    """Maps between new patient and established patient E/M codes."""
    
    # Mapping: established_code -> new_patient_code
    ESTABLISHED_TO_NEW_MAPPING: Dict[str, str] = {
        "99212": "99202",
        "99213": "99203", 
        "99214": "99204",
        "99215": "99205"
    }
    
    # Reverse mapping: new_patient_code -> established_code
    NEW_TO_ESTABLISHED_MAPPING: Dict[str, str] = {
        "99202": "99212",
        "99203": "99213",
        "99204": "99214", 
        "99205": "99215"
    }
    
    @classmethod
    def get_appropriate_code(cls, base_code: str, is_new_patient: Optional[bool]) -> str:
        """
        Get the appropriate E/M code based on patient type.
        
        Args:
            base_code: The base code (established patient code like 99212-99215)
            is_new_patient: Boolean indicating if this is a new patient visit
            
        Returns:
            Appropriate E/M code for the patient type
        """
        if is_new_patient is None:
            logger.debug(
                "Patient type not specified, defaulting to established patient codes",
                base_code=base_code,
                function=f"{__name__}.PatientCodeMapper.get_appropriate_code"
            )
            return base_code
            
        if is_new_patient:
            # Convert to new patient code
            new_code = cls.ESTABLISHED_TO_NEW_MAPPING.get(base_code, base_code)
            logger.debug(
                "Converting to new patient code",
                established_code=base_code,
                new_patient_code=new_code,
                function=f"{__name__}.PatientCodeMapper.get_appropriate_code"
            )
            return new_code
        else:
            # Return established patient code as-is
            logger.debug(
                "Using established patient code",
                code=base_code,
                function=f"{__name__}.PatientCodeMapper.get_appropriate_code"
            )
            return base_code
    
    @classmethod
    def get_code_description(cls, code: str, is_new_patient: Optional[bool] = None) -> str:
        """
        Get a human-readable description of the E/M code.
        
        Args:
            code: E/M code
            is_new_patient: Optional patient type indicator
            
        Returns:
            Human-readable description
        """
        descriptions = {
            "99202": "New Patient Office/Outpatient Visit - Straightforward MDM or 15-29 minutes",
            "99203": "New Patient Office/Outpatient Visit - Low MDM or 30-44 minutes", 
            "99204": "New Patient Office/Outpatient Visit - Moderate MDM or 45-59 minutes",
            "99205": "New Patient Office/Outpatient Visit - High MDM or 60-74 minutes",
            "99212": "Established Patient Office/Outpatient Visit - Straightforward MDM or 10-19 minutes",
            "99213": "Established Patient Office/Outpatient Visit - Low MDM or 20-29 minutes",
            "99214": "Established Patient Office/Outpatient Visit - Moderate MDM or 30-39 minutes", 
            "99215": "Established Patient Office/Outpatient Visit - High MDM or 40-54 minutes"
        }
        
        return descriptions.get(code, f"Unknown E/M code: {code}")
    
    @classmethod
    def get_equivalent_codes(cls, code: str) -> Dict[str, str]:
        """
        Get both new and established patient codes for the same complexity level.
        
        Args:
            code: Any E/M code (new or established)
            
        Returns:
            Dictionary with 'new' and 'established' keys
        """
        if code in cls.ESTABLISHED_TO_NEW_MAPPING:
            # It's an established patient code
            return {
                "established": code,
                "new": cls.ESTABLISHED_TO_NEW_MAPPING[code]
            }
        elif code in cls.NEW_TO_ESTABLISHED_MAPPING:
            # It's a new patient code  
            return {
                "established": cls.NEW_TO_ESTABLISHED_MAPPING[code],
                "new": code
            }
        else:
            logger.error(
                "Unknown E/M code provided",
                code=code,
                function=f"{__name__}.PatientCodeMapper.get_equivalent_codes"
            )
            return {"established": code, "new": code}

    @classmethod
    def validate_code_for_patient_type(cls, code: str, is_new_patient: bool) -> bool:
        """
        Validate if the given code is appropriate for the patient type.
        
        Args:
            code: E/M code to validate
            is_new_patient: Patient type
            
        Returns:
            True if code matches patient type, False otherwise
        """
        if is_new_patient:
            # Code should be 99202-99205
            valid = code in cls.NEW_TO_ESTABLISHED_MAPPING
        else:
            # Code should be 99212-99215
            valid = code in cls.ESTABLISHED_TO_NEW_MAPPING
            
        if not valid:
            logger.error(
                "Code validation failed - mismatch between code and patient type",
                code=code,
                is_new_patient=is_new_patient,
                function=f"{__name__}.PatientCodeMapper.validate_code_for_patient_type"
            )
            
        return valid
