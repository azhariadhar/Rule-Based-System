import streamlit as st
import json
import operator

st.set_page_config(page_title="Scholarship Rule Engine", layout="centered")

DEFAULT_RULES = {}
try:
    from pathlib import Path
    p = Path(__file__).parent / "Rules.json"
    DEFAULT_RULES = json.loads(p.read_text(encoding="utf-8"))
except Exception:
    DEFAULT_RULES = []

OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt
}

def evaluate_rule(rule, facts):
    """Return True if all conditions in rule are satisfied by facts."""
    for cond in rule.get("conditions", []):
        if len(cond) != 3:
            return False
        field, op, value = cond
        # missing field -> treat as not satisfied
        if field not in facts:
            return False
        try:
            left = facts[field]
            # attempt numeric conversion when appropriate
            if isinstance(value, (int, float)) or isinstance(left, (int, float)):
                # convert both to float if possible
                try:
                    left_num = float(left)
                    right_num = float(value)
                    if not OPERATORS[op](left_num, right_num):
                        return False
                    else:
                        continue
                except Exception:
                    pass
            if not OPERATORS[op](left, value):
                return False
        except Exception:
            return False
    return True

def run_rules(rules, facts):
    """Evaluate rules and return the chosen action based on priority."""
    # Sort rules by priority descending
    sorted_rules = sorted(rules, key=lambda r: r.get("priority", 0), reverse=True)
    matched = []
    for r in sorted_rules:
        if evaluate_rule(r, facts):
            matched.append(r)
    return matched

st.title("Scholarship Advisory — Rule-Based System")

st.sidebar.header("Applicant facts")
cgpa = st.sidebar.number_input("Cumulative GPA (CGPA)", min_value=0.0, max_value=4.0, value=3.0, step=0.01)
family_income = st.sidebar.number_input("Monthly family income (MYR)", min_value=0.0, value=5000.0, step=100.0)
co_curricular_score = st.sidebar.number_input("Co-curricular score (0-100)", min_value=0, max_value=100, value=50, step=1)
community_service_hours = st.sidebar.number_input("Community service hours", min_value=0, value=0, step=1)
current_semester = st.sidebar.number_input("Current semester", min_value=1, value=1, step=1)
disciplinary_actions = st.sidebar.number_input("Number of disciplinary actions", min_value=0, value=0, step=1)

facts = {
    "cgpa": float(cgpa),
    "family_income": float(family_income),
    "co_curricular_score": int(co_curricular_score),
    "community_service_hours": int(community_service_hours),
    "current_semester": int(current_semester),
    "disciplinary_actions": int(disciplinary_actions)
}

st.write("### Current applicant facts")
st.json(facts)

st.write("---")
st.write("### Rules (JSON editor)")
rules_text = st.text_area("Paste or edit the rules JSON here (use the provided default rules)", height=240, value=json.dumps(DEFAULT_RULES, indent=2))
try:
    rules = json.loads(rules_text)
except Exception as e:
    st.error(f"Invalid JSON: {e}")
    rules = []

if st.button("Evaluate rules"):
    if not rules:
        st.warning("No rules available. Please paste valid rules JSON.")
    else:
        matched = run_rules(rules, facts)
        if not matched:
            st.info("No matching rules. Decision: NO_DECISION")
        else:
            st.success(f"{len(matched)} rule(s) matched. Showing highest-priority match first.")
            for r in matched:
                st.write("**Rule:**", r.get("name"))
                st.write("Priority:", r.get("priority"))
                st.write("Decision:", r.get("action", {}).get("decision"))
                st.write("Reason:", r.get("action", {}).get("reason"))
                st.write("---")

st.write("### Notes")
st.markdown("""
- Rules are evaluated in descending priority. Multiple matches will be shown (highest priority first).
- Conditions must be lists of the form `[field, operator, value]`. Supported operators: `==, !=, >=, <=, >, <`.
- If a required fact is missing the condition is considered not satisfied.
""")