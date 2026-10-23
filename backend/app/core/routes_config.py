"""Workflow route definitions and default seed data."""

from typing import Any

# Seed Route Templates:
# 1. "Only Scrutiny": Mechanical intake -> Scrutiny Committee (human decision) -> Approval
# 2. "Scrutiny + EVC": Mechanical intake -> Scrutiny -> EVC Inspection (decision) -> Approval
# 3. "EVC + SAC/SHC": Mechanical intake -> EVC -> SAC/SHC Appellate Hearing -> Approval
# 4. "Only EVC": Mechanical intake -> EVC Inspection -> Approval

ROUTE_TEMPLATES_SEED: list[dict[str, Any]] = [
    {
        "name": "Only Scrutiny",
        "version": 1,
        "description": "Standard route requiring document scrutiny committee review.",
        "stages_definition": [
            {
                "stage_key": "APPLICATION_SUBMITTED",
                "label": "Application Submitted",
                "is_mechanical": True,
                "auto_advance_target": "SCRUTINY_PENDING",
                "allowed_roles": ["institution", "admin"],
                "sla_days": 1,
            },
            {
                "stage_key": "SCRUTINY_PENDING",
                "label": "Scrutiny Committee Review",
                "is_mechanical": False,
                "auto_advance_target": None,
                "allowed_roles": ["committee", "regional_officer", "admin"],
                "sla_days": 15,
                "next_stages": ["APPROVED", "REVERTED_TO_DEFICIENCY", "REJECTED"],
            },
            {
                "stage_key": "REVERTED_TO_DEFICIENCY",
                "label": "Deficiency Rectification",
                "is_mechanical": False,
                "auto_advance_target": None,
                "allowed_roles": ["institution", "regional_officer", "admin"],
                "sla_days": 10,
                "next_stages": ["SCRUTINY_PENDING"],
            },
            {
                "stage_key": "APPROVED",
                "label": "Letter of Approval Issued",
                "is_mechanical": False,
                "auto_advance_target": None,
                "allowed_roles": ["bureau_officer", "admin"],
                "sla_days": 5,
                "next_stages": [],
            },
            {
                "stage_key": "REJECTED",
                "label": "Application Rejected",
                "is_mechanical": False,
                "auto_advance_target": None,
                "allowed_roles": ["bureau_officer", "admin"],
                "sla_days": 0,
                "next_stages": [],
            },
        ],
    },
    {
        "name": "Scrutiny + EVC",
        "version": 1,
        "description": "Scrutiny followed by physical/expert visit committee (EVC) verification.",
        "stages_definition": [
            {
                "stage_key": "APPLICATION_SUBMITTED",
                "label": "Application Submitted",
                "is_mechanical": True,
                "auto_advance_target": "SCRUTINY_PENDING",
                "allowed_roles": ["institution", "admin"],
                "sla_days": 1,
            },
            {
                "stage_key": "SCRUTINY_PENDING",
                "label": "Scrutiny Committee Review",
                "is_mechanical": False,
                "auto_advance_target": None,
                "allowed_roles": ["committee", "regional_officer", "admin"],
                "sla_days": 15,
                "next_stages": ["EVC_PENDING", "REVERTED_TO_DEFICIENCY", "REJECTED"],
            },
            {
                "stage_key": "EVC_PENDING",
                "label": "Expert Visit Committee (EVC)",
                "is_mechanical": False,
                "auto_advance_target": None,
                "allowed_roles": ["committee", "regional_officer", "admin"],
                "sla_days": 20,
                "next_stages": ["APPROVED", "REVERTED_TO_DEFICIENCY", "REJECTED"],
            },
            {
                "stage_key": "REVERTED_TO_DEFICIENCY",
                "label": "Deficiency Rectification",
                "is_mechanical": False,
                "auto_advance_target": None,
                "allowed_roles": ["institution", "regional_officer", "admin"],
                "sla_days": 10,
                "next_stages": ["SCRUTINY_PENDING", "EVC_PENDING"],
            },
            {
                "stage_key": "APPROVED",
                "label": "Letter of Approval Issued",
                "is_mechanical": False,
                "auto_advance_target": None,
                "allowed_roles": ["bureau_officer", "admin"],
                "sla_days": 5,
                "next_stages": [],
            },
            {
                "stage_key": "REJECTED",
                "label": "Application Rejected",
                "is_mechanical": False,
                "auto_advance_target": None,
                "allowed_roles": ["bureau_officer", "admin"],
                "sla_days": 0,
                "next_stages": [],
            },
        ],
    },
    {
        "name": "EVC + SAC/SHC",
        "version": 1,
        "description": "EVC verification followed by Standing Hearing / Appellate Committee.",
        "stages_definition": [
            {
                "stage_key": "APPLICATION_SUBMITTED",
                "label": "Application Submitted",
                "is_mechanical": True,
                "auto_advance_target": "EVC_PENDING",
                "allowed_roles": ["institution", "admin"],
                "sla_days": 1,
            },
            {
                "stage_key": "EVC_PENDING",
                "label": "Expert Visit Committee (EVC)",
                "is_mechanical": False,
                "auto_advance_target": None,
                "allowed_roles": ["committee", "regional_officer", "admin"],
                "sla_days": 20,
                "next_stages": ["SAC_SHC_HEARING", "REVERTED_TO_DEFICIENCY", "REJECTED"],
            },
            {
                "stage_key": "SAC_SHC_HEARING",
                "label": "SAC/SHC Appellate Hearing",
                "is_mechanical": False,
                "auto_advance_target": None,
                "allowed_roles": ["committee", "bureau_officer", "admin"],
                "sla_days": 15,
                "next_stages": ["APPROVED", "REJECTED"],
            },
            {
                "stage_key": "REVERTED_TO_DEFICIENCY",
                "label": "Deficiency Rectification",
                "is_mechanical": False,
                "auto_advance_target": None,
                "allowed_roles": ["institution", "regional_officer", "admin"],
                "sla_days": 10,
                "next_stages": ["EVC_PENDING"],
            },
            {
                "stage_key": "APPROVED",
                "label": "Letter of Approval Issued",
                "is_mechanical": False,
                "auto_advance_target": None,
                "allowed_roles": ["bureau_officer", "admin"],
                "sla_days": 5,
                "next_stages": [],
            },
            {
                "stage_key": "REJECTED",
                "label": "Application Rejected",
                "is_mechanical": False,
                "auto_advance_target": None,
                "allowed_roles": ["bureau_officer", "admin"],
                "sla_days": 0,
                "next_stages": [],
            },
        ],
    },
    {
        "name": "Only EVC",
        "version": 1,
        "description": "Expedited route requiring on-site EVC inspection.",
        "stages_definition": [
            {
                "stage_key": "APPLICATION_SUBMITTED",
                "label": "Application Submitted",
                "is_mechanical": True,
                "auto_advance_target": "EVC_PENDING",
                "allowed_roles": ["institution", "admin"],
                "sla_days": 1,
            },
            {
                "stage_key": "EVC_PENDING",
                "label": "Expert Visit Committee (EVC)",
                "is_mechanical": False,
                "auto_advance_target": None,
                "allowed_roles": ["committee", "regional_officer", "admin"],
                "sla_days": 20,
                "next_stages": ["APPROVED", "REJECTED"],
            },
            {
                "stage_key": "APPROVED",
                "label": "Letter of Approval Issued",
                "is_mechanical": False,
                "auto_advance_target": None,
                "allowed_roles": ["bureau_officer", "admin"],
                "sla_days": 5,
                "next_stages": [],
            },
            {
                "stage_key": "REJECTED",
                "label": "Application Rejected",
                "is_mechanical": False,
                "auto_advance_target": None,
                "allowed_roles": ["bureau_officer", "admin"],
                "sla_days": 0,
                "next_stages": [],
            },
        ],
    },
]

# Escalation policy ladder default
ESCALATION_POLICY_SEED: list[dict[str, Any]] = [
    {
        "name": "Standard SLA Escalation Policy",
        "version": 1,
        "steps": [
            {
                "step": "T-30",
                "offset_days": -30,
                "target_role": "institution",
                "message": "Obligation deadline in 30 calendar days.",
            },
            {
                "step": "T-7",
                "offset_days": -7,
                "target_role": "regional_officer",
                "message": "Obligation deadline in 7 days. Action required.",
            },
            {
                "step": "T-0",
                "offset_days": 0,
                "target_role": "regional_officer",
                "message": "Obligation deadline reached today.",
            },
            {
                "step": "OVERDUE_3D",
                "offset_days": 3,
                "target_role": "bureau_officer",
                "message": "Obligation breached by 3 days. Escalated to Bureau Officer.",
            },
            {
                "step": "OVERDUE_7D",
                "offset_days": 7,
                "target_role": "admin",
                "message": "Critical breach: obligation overdue by 7 days. Escalated to Admin.",
            },
        ],
    }
]
