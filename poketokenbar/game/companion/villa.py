"""Backward-compatibility module redirecting VillaMixin and PenthouseMixin to LuxuryMixin."""

from poketokenbar.game.companion.luxury import (
    LuxuryMixin,
    PenthouseMixin,
    VillaMixin,
)

__all__ = ["LuxuryMixin", "PenthouseMixin", "VillaMixin"]
