"""Backward-compatible proxy forwarding to luxury.py."""

from poketokenbar.tui_tabs.luxury import (
    render_luxury_invitation,
    render_luxury_view,
    render_penthouse_view,
    render_villa_view,
    render_penthouse_invitation,
    _render_concierge_desk_view,
    _render_deed_inspection_view,
    _render_unlocked_luxury_view,
    _render_unlocked_penthouse_view,
    _render_wing_help_view,
    _render_facility_help_view,
)

__all__ = [
    "render_luxury_invitation",
    "render_luxury_view",
    "render_penthouse_view",
    "render_villa_view",
    "render_penthouse_invitation",
    "_render_concierge_desk_view",
    "_render_deed_inspection_view",
    "_render_unlocked_luxury_view",
    "_render_unlocked_penthouse_view",
    "_render_wing_help_view",
    "_render_facility_help_view",
]
