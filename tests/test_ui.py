"""
Commodity Option Valuator Pro
=============================

UI Framework Tests

Commit 0008
------------

Author : Simon
Version : 0.2.0
"""

from __future__ import annotations


# ==========================================================
# Imports
# ==========================================================

from ui.app import (
    ApplicationFrame,
    PAGE_TITLES,
)

from ui.sidebar import (
    Sidebar,
    NAVIGATION_ITEMS,
)

from ui.dashboard import (
    DashboardPage,
)

from ui.components import (
    MetricCard,
    SectionCard,
    StatusIndicator,
    PrimaryButton,
    PlaceholderPage,
)

from ui.styles import (
    initialize_theme,
)


# ==========================================================
# Application
# ==========================================================

def test_application_frame_import():

    assert (
        ApplicationFrame
        is not None
    )


# ==========================================================
# Page Metadata
# ==========================================================

def test_page_titles():

    expected = {
        "dashboard",
        "valuation",
        "scanner",
        "risk",
        "market",
        "charts",
        "reports",
    }

    assert expected.issubset(
        PAGE_TITLES.keys()
    )


# ==========================================================
# Navigation
# ==========================================================

def test_navigation_items():

    page_ids = {
        page_id
        for page_id, _ in NAVIGATION_ITEMS
    }

    expected = {
        "dashboard",
        "valuation",
        "scanner",
        "risk",
        "market",
        "charts",
        "reports",
    }

    assert page_ids == expected


def test_navigation_labels():

    labels = dict(
        NAVIGATION_ITEMS
    )

    assert (
        labels["dashboard"]
        ==
        "首页"
    )

    assert (
        labels["valuation"]
        ==
        "期权估值"
    )

    assert (
        labels["scanner"]
        ==
        "期权扫描"
    )

    assert (
        labels["risk"]
        ==
        "风险分析"
    )


# ==========================================================
# Dashboard
# ==========================================================

def test_dashboard_import():

    assert (
        DashboardPage
        is not None
    )


# ==========================================================
# Components
# ==========================================================

def test_metric_card_import():

    assert (
        MetricCard
        is not None
    )


def test_section_card_import():

    assert (
        SectionCard
        is not None
    )


def test_status_indicator_import():

    assert (
        StatusIndicator
        is not None
    )


def test_primary_button_import():

    assert (
        PrimaryButton
        is not None
    )


def test_placeholder_page_import():

    assert (
        PlaceholderPage
        is not None
    )


# ==========================================================
# Sidebar
# ==========================================================

def test_sidebar_import():

    assert (
        Sidebar
        is not None
    )


# ==========================================================
# Theme
# ==========================================================

def test_initialize_theme_import():

    assert callable(
        initialize_theme
    )