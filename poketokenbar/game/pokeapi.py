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
        cache_file = CACHE_DIR / f"species_{species_id}.json"
        url = f"https://pokeapi.co/api/v2/pokemon-species/{species_id}/"
        return self._fetch_json(url, cache_file)

    def get_evolution_chain(self, chain_id: int) -> Optional[Dict[str, Any]]:
        cache_file = CACHE_DIR / f"evo_chain_{chain_id}.json"
        url = f"https://pokeapi.co/api/v2/evolution-chain/{chain_id}/"
        return self._fetch_json(url, cache_file)
        
    def get_pokemon_info(self, species_id: int) -> Optional[Dict[str, Any]]:
        cache_file = CACHE_DIR / f"pokemon_{species_id}.json"
        url = f"https://pokeapi.co/api/v2/pokemon/{species_id}/"
        return self._fetch_json(url, cache_file)

    def download_sprite(self, species_id: int, is_shiny: bool = False) -> Optional[Path]:
        prefix = "shiny_" if is_shiny else "normal_"
        target_path = SPRITE_DIR / f"{prefix}{species_id}.png"
        if target_path.exists():
            return target_path

        # URL for PokeAPI sprites
        subfolder = "shiny" if is_shiny else ""
        url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{'shiny/' if is_shiny else ''}{species_id}.png"

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
        species_data = self.get_pokemon_species(species_id)
        if not species_data:
            return f"#{species_id}"
        names = self.extract_names(species_data)
        return names.get("en", f"#{species_id}")
