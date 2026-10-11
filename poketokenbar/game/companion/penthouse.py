"""Backward-compatible proxy forwarding to luxury.py."""

from poketokenbar.game.companion.luxury import (
    LuxuryMixin,
    PenthouseMixin,
    VillaMixin,
)

__all__ = ["LuxuryMixin", "PenthouseMixin", "VillaMixin"]
