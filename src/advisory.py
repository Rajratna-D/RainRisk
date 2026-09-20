"""
RainRisk: Agro-Climatic Decision Advisory Module.

Single source of truth for drought/surplus advisory content.
Used by both the Streamlit dashboard (app.py) and the FastAPI backend
(backend/main.py) to eliminate the previously duplicated advisory logic.
"""

from constants import CATEGORY_COLORS


# ---------------------------------------------------------------------------
# Advisory Data (structured, format-agnostic)
# ---------------------------------------------------------------------------
ADVISORIES = {
    "emergency": {
        "title": "Severe Drought Emergency Protocol",
        "tier": "emergency",
        "color": "#f43f5e",
        "actions": [
            {
                "label": "Crop Substitution",
                "text": "Prohibit high water-footprint crops (Paddy, Sugarcane); "
                        "immediately transition to short-duration pulses (Moong, Urad), "
                        "Bajra, or drought-tolerant fodder.",
            },
            {
                "label": "Surface Water Rationing",
                "text": "Reserve major reservoir storage strictly for municipal and "
                        "livestock drinking water contingencies.",
            },
            {
                "label": "Soil Conservation",
                "text": "Deploy mulching and inter-row conservation tillage to retard "
                        "evaporative loss.",
            },
        ],
    },
    "warning": {
        "title": "Moderate Drought Mitigation Protocol",
        "tier": "warning",
        "color": "#f59e0b",
        "actions": [
            {
                "label": "Sowing Strategy",
                "text": "Stagger sowing windows by 10-14 days aligned with localized "
                        "radar progression.",
            },
            {
                "label": "Cultivar Selection",
                "text": "Promote drought-hardy Soybean, Groundnut, and hybrid Cotton "
                        "with supplemental sprinkler support.",
            },
            {
                "label": "Nutrient Optimization",
                "text": "Fractionate nitrogen applications to avoid leaf scorch during "
                        "dry spells.",
            },
        ],
    },
    "normal": {
        "title": "Standard Climatological Operations",
        "tier": "normal",
        "color": "#10b981",
        "actions": [
            {
                "label": "Standard Cropping",
                "text": "Proceed with full-scale Kharif acreage planting (Paddy, "
                        "Cotton, Maize, Pulses).",
            },
            {
                "label": "Runoff Harvesting",
                "text": "Maximize farm-pond and check-dam recharge for winter Rabi "
                        "irrigation security.",
            },
        ],
    },
    "surplus": {
        "title": "Monsoon Surplus & Drainage Management",
        "tier": "surplus",
        "color": "#06b6d4",
        "actions": [
            {
                "label": "Drainage Management",
                "text": "Clear field drains to avoid prolonged root submergence in "
                        "Cotton and Pulse acreage.",
            },
            {
                "label": "Agronomic Measures",
                "text": "Adopt broad-bed and furrow (BBF) systems to manage heavy "
                        "surface runoff.",
            },
        ],
    },
}


def get_advisory(predicted_category):
    """
    Returns the advisory dict for a given predicted drought category.

    Parameters
    ----------
    predicted_category : str
        One of the IMD operational categories (e.g. "Normal", "Deficient").

    Returns
    -------
    dict
        Advisory dict with keys: title, tier, color, actions.
    """
    if predicted_category in ("Large Deficient", "No Rainfall"):
        return ADVISORIES["emergency"]
    elif predicted_category == "Deficient":
        return ADVISORIES["warning"]
    elif predicted_category == "Normal":
        return ADVISORIES["normal"]
    else:
        return ADVISORIES["surplus"]


def get_advisory_api(predicted_category):
    """
    Returns the advisory in flat API-friendly format (for JSON serialization).

    Returns
    -------
    dict
        {title, tier, color, actions: [str, ...]}
    """
    adv = get_advisory(predicted_category)
    return {
        "title": adv["title"],
        "tier": adv["tier"],
        "color": adv["color"],
        "actions": [a["text"] for a in adv["actions"]],
    }


def render_advisory_html(predicted_category):
    """
    Returns a Streamlit-ready HTML string for the advisory card.

    Used by app.py's Climate Cockpit tab.
    """
    adv = get_advisory(predicted_category)
    title_color = adv["color"]
    # Use a slightly different accent for surplus title
    if adv["tier"] == "surplus":
        title_color = "#38bdf8"

    actions_html = "<br>".join(
        f"• <strong>{a['label']}:</strong> {a['text']}" for a in adv["actions"]
    )

    return f"""
    <div class="advisory-box" style="border-left: 3px solid {adv['color']};">
        <div class="advisory-title" style="color: {title_color};">{adv['title']}</div>
        <div class="advisory-body">
            {actions_html}
        </div>
    </div>"""
