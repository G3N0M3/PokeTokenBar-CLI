import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

CACHE_DIR = Path.home() / ".poketokenbar" / "cache" / "pokeapi"
SPRITE_DIR = Path.home() / ".poketokenbar" / "cache" / "sprites"

class PokeAPIClient:
    """Client for PokéAPI with local filesystem caching."""

    def __init__(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        SPRITE_DIR.mkdir(parents=True, exist_ok=True)

    def _fetch_json(self, url: str, cache_file: Path) -> Optional[Dict[str, Any]]:
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PokeTokenBar/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                return data
        except Exception:
            return None

    def get_pokemon_species(self, species_id: int) -> Optional[Dict[str, Any]]:
        from poketokenbar.game.models import SPECIAL_SPECIES
        if species_id in SPECIAL_SPECIES:
            base_id = SPECIAL_SPECIES[species_id]["base_id"]
            base_data = self.get_pokemon_species(base_id)
            if base_data:
                import copy
                spec_copy = copy.deepcopy(base_data)
                spec_copy["id"] = species_id
                spec_copy["name"] = SPECIAL_SPECIES[species_id]["name"].lower().replace(" ", "-")
                names = spec_copy.get("names", [])
                for n in names:
                    if n.get("language", {}).get("name") == "en":
                        n["name"] = SPECIAL_SPECIES[species_id]["name"]
                return spec_copy
            return {
                "id": species_id,
                "name": SPECIAL_SPECIES[species_id]["name"].lower().replace(" ", "-"),
                "capture_rate": 45,
                "is_legendary": False,
                "names": [{"language": {"name": "en"}, "name": SPECIAL_SPECIES[species_id]["name"]}]
            }
        cache_file = CACHE_DIR / f"species_{species_id}.json"
        url = f"https://pokeapi.co/api/v2/pokemon-species/{species_id}/"
        return self._fetch_json(url, cache_file)

    def get_evolution_chain(self, chain_id: int) -> Optional[Dict[str, Any]]:
        cache_file = CACHE_DIR / f"evo_chain_{chain_id}.json"
        url = f"https://pokeapi.co/api/v2/evolution-chain/{chain_id}/"
        return self._fetch_json(url, cache_file)
        
    def get_pokemon_info(self, species_id: int) -> Optional[Dict[str, Any]]:
        from poketokenbar.game.models import SPECIAL_SPECIES
        target_id = SPECIAL_SPECIES[species_id]["base_id"] if species_id in SPECIAL_SPECIES else species_id
        cache_file = CACHE_DIR / f"pokemon_{target_id}.json"
        url = f"https://pokeapi.co/api/v2/pokemon/{target_id}/"
        return self._fetch_json(url, cache_file)

    def download_sprite(self, species_id: int, is_shiny: bool = False, is_back: bool = False) -> Optional[Path]:
        from poketokenbar.game.models import SPECIAL_SPECIES
        target_id = SPECIAL_SPECIES[species_id]["base_id"] if species_id in SPECIAL_SPECIES else species_id
        prefix = "shiny_" if is_shiny else "normal_"
        prefix += "back_" if is_back else "front_"
        target_path = SPRITE_DIR / f"{prefix}{target_id}.png"
        if target_path.exists():
            return target_path

        # URL for PokeAPI sprites
        subfolder = "shiny/" if is_shiny else ""
        backfolder = "back/" if is_back else ""
        url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{backfolder}{subfolder}{target_id}.png"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PokeTokenBar/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                content = resp.read()
                with open(target_path, "wb") as f:
                    f.write(content)
                return target_path
        except Exception:
            return None

    def extract_names(self, species_data: Dict[str, Any]) -> Dict[str, str]:
        names = {}
        for entry in species_data.get("names", []):
            lang = entry.get("language", {}).get("name")
            name = entry.get("name")
            if lang and name:
                names[lang] = name
        return names

    def get_species_name(self, species_id: int) -> str:
        from poketokenbar.game.models import SPECIAL_SPECIES
        if species_id in SPECIAL_SPECIES:
            return SPECIAL_SPECIES[species_id]["name"]
        species_data = self.get_pokemon_species(species_id)
        if not species_data:
            return f"#{species_id}"
        names = self.extract_names(species_data)
        return names.get("en", f"#{species_id}")
