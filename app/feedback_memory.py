# ================= FORCE-RULE MEMORY =================

from collections import defaultdict

# user_id -> rule_name -> True / False
FORCED_RULES = defaultdict(dict)


def set_force_rule(user_id: str, rule: str, value: bool):
    """
    Save a forced behavioral rule for a user.
    Example:
      rule = "DETAILED_EXPLANATION"
      value = True / False
    """
    FORCED_RULES[user_id][rule] = value


def get_force_rule(user_id: str, rule: str):
    """
    Retrieve a forced rule for a user.
    Returns:
      True / False / None
    """
    return FORCED_RULES.get(user_id, {}).get(rule, None)


def clear_force_rule(user_id: str, rule: str):
    """
    Remove a forced rule for a user.
    """
    if rule in FORCED_RULES.get(user_id, {}):
        del FORCED_RULES[user_id][rule]

