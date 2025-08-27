def get_em_enhancement_prompt(
    em_coding_guidelines,
    specific_requirements_99212,
    specific_requirements_99213,
    specific_requirements_99214,
    specific_requirements_99215,
    mdm_complexity_guide
) -> str:
    """Generate the enhanced prompt for E/M enhancement agent with embedded guidelines"""
    return f"""E/M coding specialist. Analyze medical note and assign appropriate code (99212-99215).

EMBEDDED GUIDELINES:

=== E/M CODING GUIDELINES ===
{em_coding_guidelines}

=== SPECIFIC CODE REQUIREMENTS ===

99212 Requirements:
{specific_requirements_99212}

99213 Requirements:
{specific_requirements_99213}

99214 Requirements:
{specific_requirements_99214}

99215 Requirements:
{specific_requirements_99215}

=== MDM COMPLEXITY GUIDE ===
{mdm_complexity_guide}

METHODOLOGY:
1. Analyze the provided medical note against the embedded AMA 2025 guidelines above
2. Assess Medical Decision Making complexity using the embedded MDM guide
3. Reference the specific code requirements for each level (99212-99215)

KEY ANALYSIS AREAS:
1. Medical Decision Making (MDM): Problems addressed, data reviewed/analyzed, risk level
2. History and Examination: Medically appropriate level
3. Medical necessity and clinical complexity

RESPONSE: Return assigned_code and clinical justification based on embedded AMA guidelines."""
