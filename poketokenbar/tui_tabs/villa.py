"""Backward-compatibility module redirecting to luxury.py."""

from poketokenbar.tui_tabs.luxury import (
    render_luxury_view,
    render_luxury_invitation,
    render_penthouse_view,
    render_penthouse_invitation,
    render_villa_view,
    print_bounded,
    strip_ansi
)

__all__ = [
    "render_luxury_view",
    "render_luxury_invitation",
    "render_penthouse_view",
    "render_penthouse_invitation",
    "render_villa_view",
    "print_bounded",
    "strip_ansi",
]
