import random
from typing import Dict, List, Tuple, Optional, Any

# ---------------------------------------------------------------------------
# Market Patterns
# ---------------------------------------------------------------------------
PATTERN_BULL_RALLY = "bull_rally"
PATTERN_BEAR_DECLINE = "bear_decline"
PATTERN_CYCLICAL_WAVE = "cyclical_wave"
PATTERN_SPECULATIVE_BUBBLE = "speculative_bubble"
PATTERN_CONSOLIDATION = "consolidation"

ALL_PATTERNS = [
    PATTERN_BULL_RALLY,
    PATTERN_BEAR_DECLINE,
    PATTERN_CYCLICAL_WAVE,
    PATTERN_SPECULATIVE_BUBBLE,
    PATTERN_CONSOLIDATION,
]

# Base share prices for reference and price anchoring
BASE_PRICES: Dict[str, int] = {
    "silph": 10_000_000,
    "devon": 10_000_000,
    "aether": 5_000_000,
    "mauville": 5_000_000,
    "macro": 20_000_000,
    "viridian": 25_000_000,
}

# ---------------------------------------------------------------------------
# Corporation Lore Hints per Pattern & Phase
# All hints are kept <= 52 characters to fit terminal & board cleanly.
# ---------------------------------------------------------------------------
PATTERN_HINTS: Dict[str, Dict[str, List[Tuple[float, str]]]] = {
    "silph": {
        PATTERN_BULL_RALLY: [
            (+0.06, "Silph R&D leak: next-gen Poké Ball alloy filing!"),
            (+0.14, "Saffron labs confirm breakthrough commercial launch!"),
            (+0.08, "Silph shares near peak resistance; rally maturing."),
            (-0.04, "Momentum slowing; mild cooling pullback expected."),
        ],
        PATTERN_BEAR_DECLINE: [
            (-0.06, "Silph chip export delays expected to soften shares."),
            (-0.12, "Short-sellers aggressively targeting Saffron desk."),
            (-0.04, "Silph testing multi-month floor; buy orders queue."),
            (+0.08, "Oversold bounce expected as value buyers step in."),
        ],
        PATTERN_CYCLICAL_WAVE: [
            (+0.07, "Silph quarterly logistics cycle begins tomorrow."),
            (+0.03, "Silph wave cresting; resistance tests tomorrow."),
            (-0.06, "Post-cycle cooling down; profit taking expected."),
            (-0.03, "Silph wave trough near; buyback orders queued."),
        ],
        PATTERN_SPECULATIVE_BUBBLE: [
            (+0.26, "Speculative mania sweeps Silph; explosive spike!"),
            (+0.10, "WARNING: Extreme top; whale sell walls forming!"),
            (-0.32, "Panic liquidation warning: flash dump at open!"),
            (+0.02, "Silph stabilizing after dump; bargain bids enter."),
        ],
        PATTERN_CONSOLIDATION: [
            (+0.00, "Silph trading in narrow range; awaiting catalyst."),
            (+0.01, "Silph volatility squeeze; sharp move imminent!"),
            (+0.16, "Heavy call buying: Silph upside breakout ahead!"),
        ],
    },
    "devon": {
        PATTERN_BULL_RALLY: [
            (+0.06, "Devon geologists unearth rich evolutionary vein!"),
            (+0.14, "Rustboro confirms massive incubator export surge!"),
            (+0.08, "Devon near all-time peak; profit taking looms."),
            (-0.04, "Devon momentum slowing; mild pullback expected."),
        ],
        PATTERN_BEAR_DECLINE: [
            (-0.06, "Oceanic freight delays pressure Devon shipments."),
            (-0.12, "Mining machinery stall sparks heavy Devon selloff."),
            (-0.04, "Devon shares testing key floor; buy bids queue."),
            (+0.08, "Devon oversold bounce expected as buyers step in."),
        ],
        PATTERN_CYCLICAL_WAVE: [
            (+0.07, "Devon seasonal mining cycle ramping up tomorrow."),
            (+0.03, "Devon wave cresting near upper resistance band."),
            (-0.06, "Devon post-cycle cooling; minor profit taking."),
            (-0.03, "Devon wave trough near; automated dip buybacks."),
        ],
        PATTERN_SPECULATIVE_BUBBLE: [
            (+0.28, "Fossil frenzy ignites speculative Devon buying!"),
            (+0.10, "WARNING: Devon top reached; whale sell wall spotted!"),
            (-0.34, "Panic dump warning: Devon flash crash at open!"),
            (+0.02, "Devon dust settles; value investors step in."),
        ],
        PATTERN_CONSOLIDATION: [
            (+0.00, "Devon trading sideways; awaiting quarterly audit."),
            (-0.01, "Devon volatility squeeze; big breakout imminent!"),
            (-0.14, "Devon downside breakdown warning; support cracked!"),
        ],
    },
    "aether": {
        PATTERN_BULL_RALLY: [
            (+0.06, "Aether Foundation secures major sanctuary grant!"),
            (+0.12, "Alola rehabilitation clinic sets record yields!"),
            (+0.07, "Aether testing upper band; momentum cooling."),
            (-0.03, "Aether momentum tapering; mild pullback ahead."),
        ],
        PATTERN_BEAR_DECLINE: [
            (-0.05, "Tropical squall repairs weigh on Aether overhead."),
            (-0.11, "Conservation budget review triggers Aether drop."),
            (-0.04, "Aether testing foundation floor; donors step in."),
            (+0.07, "Aether oversold rebound expected tomorrow."),
        ],
        PATTERN_CYCLICAL_WAVE: [
            (+0.06, "Aether quarterly donation drive begins tomorrow."),
            (+0.03, "Aether wave cresting near historical resistance."),
            (-0.05, "Aether post-drive cooling; volume tapering."),
            (-0.03, "Aether wave trough near; support bids queuing."),
        ],
        PATTERN_SPECULATIVE_BUBBLE: [
            (+0.24, "Sanctuary hype sparks rare speculative Aether run!"),
            (+0.09, "WARNING: Aether frenzy peaks; whale exit alert!"),
            (-0.30, "Aether flash correction expected at opening bell!"),
            (+0.03, "Aether stabilizing; conservation trust buys dip."),
        ],
        PATTERN_CONSOLIDATION: [
            (+0.00, "Aether range-bound; tranquil market conditions."),
            (+0.01, "Aether volatility tightly compressed; move soon!"),
            (+0.14, "Surprise benefactor deal: Aether breakout ahead!"),
        ],
    },
    "mauville": {
        PATTERN_BULL_RALLY: [
            (+0.07, "Mauville Game Corner reports record tourist slots!"),
            (+0.15, "VIP Poker tournament yields booming token turnover!"),
            (+0.08, "Mauville gaming index testing historic resistance."),
            (-0.04, "Mauville gaming volume cooling; mild pullback."),
        ],
        PATTERN_BEAR_DECLINE: [
            (-0.06, "High-roller cleans out Mauville blackjack vault!"),
            (-0.13, "Mauville utility tax hike sparks sharp selloff."),
            (-0.04, "Mauville shares test floor; house buybacks queue."),
            (+0.09, "Mauville oversold bounce expected as house wins."),
        ],
        PATTERN_CYCLICAL_WAVE: [
            (+0.08, "Mauville weekend tourist surge begins tomorrow."),
            (+0.03, "Mauville wave cresting; weekend peak reached."),
            (-0.06, "Mauville post-weekend cooling; volume easing."),
            (-0.03, "Mauville wave trough near; casino reserve buying."),
        ],
        PATTERN_SPECULATIVE_BUBBLE: [
            (+0.30, "Jackpot mania triggers speculative Mauville run!"),
            (+0.11, "WARNING: Mauville casino bubble; big dump looms!"),
            (-0.36, "Mauville flash crash expected after jackpot payout!"),
            (+0.03, "Mauville vault stabilizes; dip buyers enter."),
        ],
        PATTERN_CONSOLIDATION: [
            (+0.00, "Mauville arcade turnover steady; range-bound."),
            (+0.01, "Mauville compression tight; game expansion soon!"),
            (+0.18, "New entertainment wing approved: Mauville surge!"),
        ],
    },
    "macro": {
        PATTERN_BULL_RALLY: [
            (+0.07, "Macro Cosmos lands Galar power grid expansion!"),
            (+0.15, "Wyndon stadium sponsorship generates huge fees!"),
            (+0.08, "Macro testing ceiling; institutional profit taking."),
            (-0.04, "Macro grid momentum slowing; mild pullback."),
        ],
        PATTERN_BEAR_DECLINE: [
            (-0.06, "Dynamax grid maintenance prompts costly downtime."),
            (-0.13, "Galar environmental audit sparks heavy Macro dump."),
            (-0.04, "Macro tests major support; utility desks buy in."),
            (+0.08, "Macro oversold bounce expected on grid restart."),
        ],
        PATTERN_CYCLICAL_WAVE: [
            (+0.07, "Macro power consumption cycle ramping tomorrow."),
            (+0.03, "Macro wave cresting near upper electrical band."),
            (-0.06, "Macro post-cycle cooling; power demand easing."),
            (-0.03, "Macro wave trough near; grid dividend reinvest."),
        ],
        PATTERN_SPECULATIVE_BUBBLE: [
            (+0.28, "Dynamax energy hype triggers violent Macro rally!"),
            (+0.10, "WARNING: Macro energy bubble; liquidation danger!"),
            (-0.35, "Panic dump warning: Macro grid flash crash ahead!"),
            (+0.02, "Macro emergency liquidity secured; bids enter."),
        ],
        PATTERN_CONSOLIDATION: [
            (+0.00, "Macro grid operating nominal; range-bound trading."),
            (-0.01, "Macro volatility squeeze; grid announcement near!"),
            (-0.15, "Unscheduled power glitch: Macro breakdown risk!"),
        ],
    },
    "viridian": {
        PATTERN_BULL_RALLY: [
            (+0.06, "Viridian expands Celadon nocturnal freight runs!"),
            (+0.14, "Bulk midnight shipments surge across Kanto depot!"),
            (+0.08, "Viridian freight volume testing historic peak."),
            (-0.04, "Viridian trade momentum cooling; slight pullback."),
        ],
        PATTERN_BEAR_DECLINE: [
            (-0.06, "Highway inspections delay nocturnal freight runs."),
            (-0.12, "Subterranean tunnel rumors prompt Viridian selloff."),
            (-0.04, "Viridian testing depot floor; insider bids queue."),
            (+0.08, "Viridian oversold rebound expected as cargo moves."),
        ],
        PATTERN_CYCLICAL_WAVE: [
            (+0.07, "Viridian weekly freight schedule ramps tomorrow."),
            (+0.03, "Viridian wave cresting; depot capacity full."),
            (-0.06, "Viridian post-freight cooling; warehouse reset."),
            (-0.03, "Viridian wave trough near; covert syndicate buys."),
        ],
        PATTERN_SPECULATIVE_BUBBLE: [
            (+0.26, "Covert logistics rumor sparks wild Viridian rally!"),
            (+0.10, "WARNING: Viridian top; syndicate desks dumping!"),
            (-0.32, "Viridian flash dump warning as warehouse clears!"),
            (+0.03, "Viridian covert accounts scoop up cheap shares."),
        ],
        PATTERN_CONSOLIDATION: [
            (+0.00, "Viridian logistics steady; quiet night shifts."),
            (+0.01, "Viridian trade volume squeezed; big shift ahead!"),
            (+0.17, "Covert black-market tie rumored: Viridian surge!"),
        ],
    },
}

# ---------------------------------------------------------------------------
# Stock Market Engine
# ---------------------------------------------------------------------------
class StockMarketEngine:
    """Handles stock price pattern progression, ceilings/floors, and forward hints."""

    @staticmethod
    def get_base_price(corp_key: str) -> int:
        return BASE_PRICES.get(corp_key, 10_000_000)

    @staticmethod
    def get_floor_price(corp_key: str) -> int:
        base = StockMarketEngine.get_base_price(corp_key)
        return max(1_000_000, int(base * 0.25))

    @staticmethod
    def get_ceiling_price(corp_key: str) -> int:
        base = StockMarketEngine.get_base_price(corp_key)
        return int(base * 3.5)

    @staticmethod
    def get_hard_cap(corp_key: str) -> int:
        base = StockMarketEngine.get_base_price(corp_key)
        return int(base * 4.5)

    @staticmethod
    def choose_pattern(corp_key: str, curr_price: int) -> str:
        """Selects a market pattern intelligently based on current price relative to base."""
        base = StockMarketEngine.get_base_price(corp_key)
        ratio = curr_price / float(base)

        if ratio >= 2.8:
            # Overextended: high chance of bear decline or crash
            weights = {
                PATTERN_BULL_RALLY: 0.05,
                PATTERN_BEAR_DECLINE: 0.50,
                PATTERN_CYCLICAL_WAVE: 0.15,
                PATTERN_SPECULATIVE_BUBBLE: 0.10,
                PATTERN_CONSOLIDATION: 0.20,
            }
        elif ratio <= 0.45:
            # Undervalued: high chance of bull rally or value accumulation
            weights = {
                PATTERN_BULL_RALLY: 0.45,
                PATTERN_BEAR_DECLINE: 0.05,
                PATTERN_CYCLICAL_WAVE: 0.25,
                PATTERN_SPECULATIVE_BUBBLE: 0.10,
                PATTERN_CONSOLIDATION: 0.15,
            }
        else:
            # Normal balanced trading
            weights = {
                PATTERN_BULL_RALLY: 0.25,
                PATTERN_BEAR_DECLINE: 0.25,
                PATTERN_CYCLICAL_WAVE: 0.25,
                PATTERN_SPECULATIVE_BUBBLE: 0.10,
                PATTERN_CONSOLIDATION: 0.15,
            }

        patterns = list(weights.keys())
        probabilities = [weights[p] for p in patterns]
        return random.choices(patterns, weights=probabilities, k=1)[0]

    @staticmethod
    def get_pattern_phases(corp_key: str, pattern: str) -> List[Tuple[float, str]]:
        corp_hints = PATTERN_HINTS.get(corp_key, PATTERN_HINTS["silph"])
        return corp_hints.get(pattern, corp_hints[PATTERN_CYCLICAL_WAVE])

    @staticmethod
    def init_corp_state(corp_key: str, curr_price: int) -> Dict[str, Any]:
        """Initializes pattern state and first forward-looking hint."""
        pattern = StockMarketEngine.choose_pattern(corp_key, curr_price)
        phases = StockMarketEngine.get_pattern_phases(corp_key, pattern)
        phase_idx = 0
        bias, hint = phases[phase_idx]

        return {
            "pattern": pattern,
            "phase": phase_idx,
            "duration": len(phases),
            "next_bias": bias,
            "next_hint": hint,
        }

    @staticmethod
    def ensure_market_state(sm_data: dict) -> None:
        """Ensures sm_data['market_state'] exists for all corporations."""
        market_state = sm_data.setdefault("market_state", {})
        prices = sm_data.get("prices", {})
        news = sm_data.setdefault("latest_news", {})

        for c_key in BASE_PRICES:
            if c_key not in market_state:
                p = prices.get(c_key, BASE_PRICES[c_key])
                st = StockMarketEngine.init_corp_state(c_key, p)
                market_state[c_key] = st
                news[c_key] = st["next_hint"]

    @staticmethod
    def step_day(
        sm_data: dict,
        days_to_apply: int,
        streak: int,
        burn_tokens: int,
        catalysts: dict,
        corp_boosts: Dict[str, float],
    ) -> Dict[str, float]:
        """Steps the market forward, updating prices via next_bias and picking new hints for tomorrow."""
        StockMarketEngine.ensure_market_state(sm_data)
        prices = sm_data.setdefault("prices", {})
        histories = sm_data.setdefault("price_history", {})
        news = sm_data.setdefault("latest_news", {})
        market_state = sm_data["market_state"]

        # Calculate macro player alpha
        if burn_tokens >= 500_000:
            burn_mom = random.uniform(0.02, 0.04)
        elif burn_tokens >= 100_000:
            burn_mom = random.uniform(0.00, 0.015)
        else:
            burn_mom = random.uniform(-0.02, 0.0)

        streak_sent = 0.01 if streak >= 5 else 0.0
        final_changes = {}

        for _ in range(days_to_apply):
            day_changes = {}
            for c_key in BASE_PRICES:
                st = market_state.get(c_key)
                curr_price = prices.get(c_key, BASE_PRICES[c_key])
                base_price = StockMarketEngine.get_base_price(c_key)
                floor_price = StockMarketEngine.get_floor_price(c_key)
                hard_cap = StockMarketEngine.get_hard_cap(c_key)

                if not st:
                    st = StockMarketEngine.init_corp_state(c_key, curr_price)
                    market_state[c_key] = st

                planned_bias = st.get("next_bias", 0.0)
                noise = random.uniform(-0.015, 0.015)
                c_boost = corp_boosts.get(c_key, 0.0)

                # Elastic gravity resistance against infinite price growth
                gravity = 0.0
                if curr_price > int(base_price * 1.8):
                    gravity = -0.04 * ((curr_price / float(base_price)) - 1.5)
                elif curr_price < int(base_price * 0.6):
                    gravity = +0.04 * (1.0 - (curr_price / float(base_price)))

                net_pct = planned_bias + noise + burn_mom + streak_sent + c_boost + gravity
                # Clamp daily change between -35% and +35%
                clamped_pct = max(-0.35, min(0.35, net_pct))

                new_price = int(curr_price * (1.0 + clamped_pct))
                new_price = max(floor_price, min(hard_cap, new_price))

                prices[c_key] = new_price
                hist = histories.setdefault(c_key, [curr_price])
                hist.append(new_price)
                histories[c_key] = hist[-7:]
                day_changes[c_key] = (new_price - curr_price) / float(curr_price)

                # Advance pattern phase
                cur_pattern = st.get("pattern", PATTERN_CYCLICAL_WAVE)
                cur_phase = st.get("phase", 0) + 1
                phases = StockMarketEngine.get_pattern_phases(c_key, cur_pattern)

                # Check if pattern completed or price hit extremes
                if cur_phase >= len(phases) or new_price >= hard_cap or new_price <= floor_price:
                    # Pick new pattern for next cycle
                    new_pat = StockMarketEngine.choose_pattern(c_key, new_price)
                    phases = StockMarketEngine.get_pattern_phases(c_key, new_pat)
                    cur_pattern = new_pat
                    cur_phase = 0

                next_bias, next_hint = phases[cur_phase]
                st["pattern"] = cur_pattern
                st["phase"] = cur_phase
                st["duration"] = len(phases)
                st["next_bias"] = next_bias
                st["next_hint"] = next_hint
                news[c_key] = next_hint

            final_changes = day_changes

        return final_changes
