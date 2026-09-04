import json
import uuid
import datetime
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from poketokenbar.game.models import MonState, DexEntry, Rarity, PokemonNature

def get_state_file() -> Path:
    override = os.environ.get("PTB_STATE_FILE")
    if override:
        return Path(override)
    return Path.home() / ".poketokenbar" / "state.json"

STATE_FILE = get_state_file()

class StorageManager:
    """Handles saving and loading of the PokeTokenBar game state."""

    @staticmethod
    def load_state() -> Dict[str, Any]:
        state = StorageManager.default_state()
        state_file = get_state_file()
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    state.update(saved)
            except Exception:
                pass
        return state

    @staticmethod
    def save_state(state_data: Dict[str, Any]) -> bool:
        state_file = get_state_file()
        state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = state_file.with_suffix(f".{uuid.uuid4().hex}.json.tmp")
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
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
            "egg_usage": 0,
            "egg_tier": None,
            "pending_hatch_id": None,
            "active_mon": None,
            "dex": [],
            "collected_finals": [],
            "inventory": {
                "rare_candy": 0,
                "mint": 0,
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
            "is_mega": mon.is_mega,
            "mega_form": mon.mega_form,
            "happiness": mon.happiness
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
                is_mega=data.get("is_mega", False),
                mega_form=data.get("mega_form"),
                happiness=data.get("happiness", 100)
            )
        except Exception:
            return None
