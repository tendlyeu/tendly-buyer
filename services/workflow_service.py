"""Workflow state machine for procurement plans."""

VALID_TRANSITIONS = {
    "draft": ["planning", "cancelled"],
    "planning": ["review", "cancelled"],
    "review": ["approved", "planning", "cancelled"],
    "approved": ["published", "review", "cancelled"],
    "published": ["completed", "cancelled"],
    "completed": [],
    "cancelled": ["draft"],
}

STEP_ROLES = {
    1: "domain_lead",
    2: "domain_lead",
    3: "procurement_manager",
    4: "board",
    5: "domain_specialist",
}

STEP_NAMES = {
    1: "domain_review",
    2: "market_research",
    3: "plan_review",
    4: "board_approval",
    5: "document_preparation",
}

STEP_NAMES_ET = {
    1: "Vajaduse ülevaade",
    2: "Turu-uuring",
    3: "Hankeplaani ülevaade",
    4: "Eelarve kinnitamine",
    5: "Dokumentide koostamine",
}


def can_transition(current_status, new_status):
    return new_status in VALID_TRANSITIONS.get(current_status, [])


def can_user_act_on_step(step_number, user_role):
    required_role = STEP_ROLES.get(step_number)
    if not required_role:
        return False
    if user_role == "admin":
        return True
    return user_role == required_role


def get_step_info(step_number):
    return {
        "number": step_number,
        "name": STEP_NAMES.get(step_number, ""),
        "name_et": STEP_NAMES_ET.get(step_number, ""),
        "role": STEP_ROLES.get(step_number, ""),
    }
