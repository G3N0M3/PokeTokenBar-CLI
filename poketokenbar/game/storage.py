import json
import uuid
import datetime
import os
import sys
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any

from poketokenbar.game.models import MonState, DexEntry, Rarity, VIP_PATRON_DAILY_BANKROLLS

def get_state_file() -> Path:
    override = os.environ.get("PTB_STATE_FILE")
    if override:
        return Path(override)
    # Safety guard: If running inside a test framework and PTB_STATE_FILE was not set,
    # route to a temporary sandbox to protect the user's live save data.
    is_testing = (
        "pytest" in sys.modules
        or "PYTEST_CURRENT_TEST" in os.environ
        or any("unittest" in arg or "pytest" in arg for arg in sys.argv)
    )
    if is_testing:
        return Path(tempfile.gettempdir()) / "ptb_test_auto_state.json"
    return Path.home() / ".poketokenbar" / "state.json"

STATE_FILE = get_state_file()

class StorageManager:
    """Handles saving and loading of the PokeTokenBar game state."""

    @staticmethod
    def _deep_merge_defaults(target: Dict[str, Any], defaults: Dict[str, Any]) -> None:
        for k, v in defaults.items():
            if k not in target or target[k] is None:
                target[k] = v
            elif isinstance(v, dict) and isinstance(target.get(k), dict):
                StorageManager._deep_merge_defaults(target[k], v)

    @staticmethod
    def load_state() -> Dict[str, Any]:
        defaults = StorageManager.default_state()
        state = StorageManager.default_state()
        state_file = get_state_file()
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    if isinstance(saved, dict):
                        state.update(saved)
            except Exception:
                pass

        for nested_key in (
            "stock_market",
            "luxury",
            "velvet_sting",
            "matrix",
            "rocket_ops",
            "rocket_armory_charges",
            "settings",
            "trainer_battles",
        ):
            if isinstance(state.get(nested_key), dict) and isinstance(defaults.get(nested_key), dict):
                StorageManager._deep_merge_defaults(state[nested_key], defaults[nested_key])
            elif nested_key not in state or not isinstance(state.get(nested_key), dict):
                state[nested_key] = defaults[nested_key]

        # Migration: ensure VIP bankrolls are present
        vb = state.setdefault("vip_bankrolls", {})
        for name, max_val in VIP_PATRON_DAILY_BANKROLLS.items():
            if name not in vb:
                vb[name] = {"current": max_val, "max": max_val}
            else:
                vb[name].setdefault("max", max_val)
                vb[name].setdefault("current", max_val)
        if "vip_bankrolls_date" not in state:
            state["vip_bankrolls_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
        state.setdefault("vip_clean_sweep_claimed", False)
        state.setdefault("vip_clean_sweeps_count", 0)

        return state

    @staticmethod
    def save_state(state_data: Dict[str, Any]) -> bool:
        state_file = get_state_file()
        state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = state_file.with_suffix(f".{uuid.uuid4().hex}.json.tmp")
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            if state_file.exists():
                try:
                    shutil.copy2(state_file, state_file.with_suffix(".json.bak"))
                except Exception:
                    pass
            tmp_file.replace(state_file)
            return True
        except Exception:
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except Exception:
                    pass
            return False

    @staticmethod
    def default_state() -> Dict[str, Any]:
        return {
            "install_baseline_set": False,
            "used_since_install": 0,
            "spent_tokens": 0,
            "billing_cycle_day": 1,
            "week_start_day": "monday",
            "custom_token_file": None,
            "baseline_total_tokens": 0,
            "baseline_date": None,
            "egg_usage": 0,
            "egg_tier": None,
            "pending_eggs": [],
            "pending_hatch_id": None,
            "active_mon": None,
            "dex": [],
            "collected_finals": [],
            "last_milestone": None,
            "last_evolution": None,
            "inventory": {
                "rare_candy": 0,
                "berry_oran": 0,
                "berry_golden": 0
            },
            "streak_days": 1,
            "last_active_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "happiness": 100,
            "gym_badges": [],
            "achievements": [],
            "daily_quests": {},
            "active_boss": None,
            "expeditions": [],
            "expedition_logs": [],
            "trainer_battles": {"wins": 0, "losses": 0},
            "battle_logs": [],
            "golden_razz_active": False,
            "last_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "term_deposits": [],
            "cd_sort_criteria": "days",
            "nursery_sort_criteria": "default",
            "investments": {
                "silph": 0,
                "devon": 0,
                "aether": 0,
                "mauville": 0,
                "macro": 0,
                "viridian": 0
            },
            "black_market": None,
            "stock_market": {
                "prices": {
                    "silph": 10_000_000,
                    "devon": 10_000_000,
                    "aether": 5_000_000,
                    "mauville": 5_000_000,
                    "macro": 20_000_000,
                    "viridian": 25_000_000
                },
                "price_history": {
                    "silph": [10_000_000],
                    "devon": [10_000_000],
                    "aether": [5_000_000],
                    "mauville": [5_000_000],
                    "macro": [20_000_000],
                    "viridian": [25_000_000]
                },
                "cost_basis": {
                    "silph": 0,
                    "devon": 0,
                    "aether": 0,
                    "mauville": 0,
                    "macro": 0,
                    "viridian": 0
                },
                "latest_news": {
                    "silph": "Silph Co. operations running steadily across Kanto.",
                    "devon": "Devon Corp reports steady retail demand in Hoenn.",
                    "aether": "Aether Foundation maintaining peaceful sanctuary conditions.",
                    "mauville": "Greater Mauville Game Corner seeing standard foot traffic.",
                    "macro": "Macro Cosmos power grid operating at nominal capacity.",
                    "viridian": "Viridian Global Logistics freight operations proceeding on schedule."
                },
                "daily_catalysts": {
                    "expeditions_completed": 0,
                    "shop_tokens_spent": 0,
                    "casino_net_pnl": 0,
                    "bosses_defeated": 0
                },
                "market_headline": "📈 POKÉMON EXCHANGE: Indices opening with steady volume."
            },
            "rocket_story_unlocked": False,
            "rocket_story_viewed": False,
            "rocket_alliance_accepted": False,
            "rocket_transmission_state": "intro",
            "rocket_rank": "Informant",
            "rocket_reputation": 0,
            "rocket_ops": {
                f"op_{i}": {
                    "status": "available" if i == 1 else "locked",
                    "progress": 0,
                    "claimed": False,
                    "objective_done": False,
                    "boss_hp_remaining": (
                        150_000 if i == 3 else
                        200_000 if i == 6 else
                        300_000 if i == 9 else
                        350_000 if i == 10 else 0
                    ),
                    "briefing_viewed": False,
                    "expeditions_done": 0,
                    "battle_wins": 0,
                    "black_market_trades": 0
                }
                for i in range(1, 11)
            },
            "rocket_intel_unlocked": ["intel_001"],
            "permanent_black_market": False,
            "has_exp_splitter": False,
            "last_authority_date": None,
            "pending_authority_delivery": None,
            "rocket_battle_state": {},
            "rocket_armory_charges": {
                "spray": {"charges": 0, "progress": 0, "target": 15_000_000},
                "chrono": {"charges": 0, "progress": 0, "target": 25_000_000},
                "catalyst": {"charges": 0, "progress": 0, "target": 25_000_000}
            },
            "luxury": {
                "invitation_sent": False,
                "invitation_pending": False,
                "vip_fee_paid": False,
                "unlocked": False,
                "facilities": {
                    "nursery": 0,
                    "springs": 0,
                    "trading_desk": 0,
                    "chromatic_lab": 0
                },
                "decor": [],
                "last_shiny_transmute": None
            },
            "poker_vip_unlocked": False,
            "vip_bankrolls_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "vip_clean_sweep_claimed": False,
            "vip_clean_sweeps_count": 0,
            "vip_bankrolls": {
                name: {"current": max_val, "max": max_val}
                for name, max_val in VIP_PATRON_DAILY_BANKROLLS.items()
            },
            "velvet_sting": {
                "chapter": "1",
                "recruited": False,
                "cleared": False,
                "boss_stack": 0,
                "boss_max_stack": 0,
                "syndicate_wins": 0,
                "vip_winnings": 0,
                "chapter_winnings": 0,
                "chapter_pot": 0,
                "max_pot_won": 0,
                "ranked_wins": 0,
            },
            "matrix": {
                "unlocked": False,
                "story_viewed": False,
                "ram_blocks": [],
                "hacked_nodes": [],
                "active_tweaks": {},
                "trace_level": 0,
                "deck_hardware": {"integrity": 100, "firewall": 500, "max_firewall": 500, "threads": 1},
                "tools": ["overflow"],
                "tool_upgrades": [],
                "deck_upgrades": {
                    "shield": 0,
                    "stealth": 0,
                    "nanites": 0,
                    "clock": 0,
                },
                "active_breach": None,
                "active_threat": None,
                "patches": [],
                "sectors": [],
                "quantum_flux": 0,
                "overclock_levels": {"ram": 0, "amp": 0},
                "daemon_raid_tier": 1,
                "defeated_daemons": [],
                "root_transcended": False,
                "total_tokens_consumed": 0,
                "collider_state": None,
                "combat_state": None,
                "tutorial_step": 1,
                "tutorial_completed": False,
                "tutorial_active": True,
            },
            "bank_balance": 0,
            "bank_loan": 0,
            "loan_days_active": 0,
            "tokens_init_ts": None,
            "expedition_slots": 10,
            "expedition_insurance": False,
            "rocket_radar_charges": 0,
            "daily_grunt_bribe": None,
            "gacha_pity": 0,
            "red_battle_state": {},
            "red_wins": 0,
            "red_hof": [],
            "unread_alerts": [],
            "settings": {
                "auto_hatch": False,
                "auto_feed": False,
                "notifications": True
            }
        }

    @staticmethod
    def mon_to_dict(mon: MonState) -> Dict[str, Any]:
        return {
            "base_id": mon.base_id,
            "path_ids": mon.path_ids,
            "planned_path_ids": mon.planned_path_ids,
            "stage_index": mon.stage_index,
            "used_at_stage": mon.used_at_stage,
            "rarity": mon.rarity.value,
            "total_forms": mon.total_forms,
            "is_shiny": mon.is_shiny,
            "ditto_disguise": mon.ditto_disguise,
            "ditto_revealed": mon.ditto_revealed,
            "is_mega": mon.is_mega,
            "mega_form": mon.mega_form,
            "happiness": mon.happiness,
            "held_item": mon.held_item,
            "is_graduated": getattr(mon, "is_graduated", False)
        }

    @staticmethod
    def dict_to_mon(data: Optional[Dict[str, Any]]) -> Optional[MonState]:
        if not data:
            return None
        try:
            return MonState(
                base_id=data["base_id"],
                path_ids=data.get("path_ids", [data["base_id"]]),
                planned_path_ids=data.get("planned_path_ids", data.get("path_ids", [data["base_id"]])),
                stage_index=data.get("stage_index", 0),
                used_at_stage=data.get("used_at_stage", 0),
                rarity=Rarity(data["rarity"]) if isinstance(data.get("rarity"), str) else data.get("rarity", Rarity.COMMON),
                total_forms=data.get("total_forms", len(data.get("path_ids", [1]))),
                is_shiny=data.get("is_shiny", False),
                ditto_disguise=data.get("ditto_disguise"),
                ditto_revealed=data.get("ditto_revealed", False),
                is_mega=data.get("is_mega", False),
                mega_form=data.get("mega_form"),
                happiness=data.get("happiness", 100),
                held_item=data.get("held_item"),
                is_graduated=data.get("is_graduated", False)
            )
        except Exception:
            return None
