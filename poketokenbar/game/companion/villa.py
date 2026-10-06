"""Backward-compatibility module redirecting VillaMixin to PenthouseMixin."""

from poketokenbar.game.companion.penthouse import PenthouseMixin, VillaMixin

__all__ = ["PenthouseMixin", "VillaMixin"]
