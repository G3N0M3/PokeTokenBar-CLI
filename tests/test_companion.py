"""Backward-compatibility shim for tests.game.test_companion."""
from tests.game.test_companion import TestCompanionEngine
from tests.game.test_feeding import TestOranBerryFeeding
from tests.game.test_banking import TestBankDailyInterest
from tests.tui.test_confirmations import TestLargeQuantityPurchaseConfirmation

__all__ = [
    "TestCompanionEngine",
    "TestOranBerryFeeding",
    "TestBankDailyInterest",
    "TestLargeQuantityPurchaseConfirmation",
]
