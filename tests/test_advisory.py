"""
Unit tests for the Agro-Climatic Decision Advisory Module (src/advisory.py).
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from advisory import ADVISORIES, get_advisory, get_advisory_api, render_advisory_html


class TestAdvisoryModule:
    def test_emergency_categories(self):
        for cat in ["Large Deficient", "No Rainfall"]:
            adv = get_advisory(cat)
            assert adv["tier"] == "emergency"
            assert adv["color"] == "#f43f5e"
            assert "Emergency" in adv["title"]
            assert len(adv["actions"]) >= 3
            for action in adv["actions"]:
                assert "label" in action and "text" in action

    def test_warning_category(self):
        adv = get_advisory("Deficient")
        assert adv["tier"] == "warning"
        assert adv["color"] == "#f59e0b"
        assert "Mitigation" in adv["title"]
        assert len(adv["actions"]) >= 3

    def test_normal_category(self):
        adv = get_advisory("Normal")
        assert adv["tier"] == "normal"
        assert adv["color"] == "#10b981"
        assert "Standard" in adv["title"]
        assert len(adv["actions"]) >= 2

    def test_surplus_categories(self):
        for cat in ["Excess", "Large Excess", "Arbitrary Surplus"]:
            adv = get_advisory(cat)
            assert adv["tier"] == "surplus"
            assert adv["color"] == "#06b6d4"
            assert "Surplus" in adv["title"]
            assert len(adv["actions"]) >= 2

    def test_get_advisory_api_structure(self):
        for cat in ["Normal", "Deficient", "Large Deficient", "Excess"]:
            api_adv = get_advisory_api(cat)
            assert "title" in api_adv
            assert "tier" in api_adv
            assert "color" in api_adv
            assert "actions" in api_adv
            assert isinstance(api_adv["actions"], list)
            assert all(isinstance(a, str) for a in api_adv["actions"])

    def test_render_advisory_html(self):
        for cat in ["Normal", "Deficient", "Large Deficient", "Excess"]:
            html = render_advisory_html(cat)
            assert isinstance(html, str)
            assert '<div class="advisory-box"' in html
            assert '<div class="advisory-title"' in html
            assert '<div class="advisory-body">' in html
            assert "• <strong>" in html
