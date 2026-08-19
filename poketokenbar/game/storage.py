import json
import uuid
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from poketokenbar.game.models import MonState, DexEntry, Rarity, PokemonNature

STATE_FILE = Path.home() / ".poketokenbar" / "state.json"

class StorageManager:
    """Handles saving and loading of the PokeTokenBar game state."""

    @staticmethod
    def load_state() -> Dict[str, Any]:
        state = StorageManager.default_state()
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    state.update(saved)
                    # Ensure nested settings dictionary is merged properly
                    if "settings" in saved:
                        state["settings"] = {**StorageManager.default_state()["settings"], **saved["settings"]}
            except Exception:
                pass
        return state

    @staticmethod
    def save_state(state_data: Dict[str, Any]) -> bool:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    @staticmethod
    def default_state() -> Dict[str, Any]:
        return {
            "install_baseline_set": False,
            "used_since_install": 0,
            "spent_tokens": 0,
            "egg_usage": 0,
            "egg_tier": None,
            "pending_hatch_id": None,
            "active_mon": None,
            "dex": [],
            "collected_finals": [],
            "settings": {
                "auto_tracking_enabled": True,
                "refresh_interval": 3.0
            },
            "inventory": {
                "rare_candy": 0,
                "mint": 0,
                "shiny_charm": 0,
                "berry_oran": 0,
                "berry_golden": 0,
                "mega_stone": 0
            },
            "streak_days": 1,
            "last_active_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "happiness": 100,
            "gym_badges": [],
            "achievements": [],
            "daily_quests": {},
            "active_boss": None,
            "expeditions": [],
            "trainer_battles": {"wins": 0, "losses": 0},
            "golden_razz_active": False,
            "last_date": datetime.datetime.now().strftime("%Y-%m-%d")
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
            "nature": mon.nature.value if mon.nature else None,
            "ditto_disguise": mon.ditto_disguise,
            "ditto_revealed": mon.ditto_revealed,
            "is_mega": mon.is_mega
        }

    @staticmethod
    def dict_to_mon(data: Optional[Dict[str, Any]]) -> Optional[MonState]:
        if not data:
            return None
        try:
            return MonState(
                base_id=data["base_id"],
                path_ids=data["path_ids"],
                planned_path_ids=data.get("planned_path_ids", data["path_ids"]),
                stage_index=data["stage_index"],
                used_at_stage=data["used_at_stage"],
                rarity=Rarity(data["rarity"]),
                total_forms=data["total_forms"],
                is_shiny=data.get("is_shiny", False),
                nature=PokemonNature(data["nature"]) if data.get("nature") else None,
                ditto_disguise=data.get("ditto_disguise"),
                ditto_revealed=data.get("ditto_revealed", False),
                is_mega=data.get("is_mega", False)
            )
        except Exception:
            return None
