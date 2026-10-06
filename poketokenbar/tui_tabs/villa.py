"""Backward-compatibility module redirecting to penthouse.py."""

from poketokenbar.tui_tabs.penthouse import (
    render_penthouse_view,
    render_penthouse_invitation,
    render_villa_view,
    print_bounded,
    strip_ansi
)

__all__ = [
    "render_penthouse_view",
    "render_penthouse_invitation",
    "render_villa_view",
    "print_bounded",
    "strip_ansi",
]
