import math
import re
from typing import Dict, List, Optional, Tuple, Any, Union


class FeedingMixin:
    """Provides happiness replenishment and feeding logic with support for threshold and targeted feeding."""

    def _get_companion_happiness(self, m: Any) -> int:
        active = self.active_mon
        if isinstance(m, dict):
            sp_id = m.get("species_id", m.get("final_id", m.get("base_id")))
            if active and active.current_id == sp_id:
                return active.happiness
            m_st = m.get("mon_state")
            if isinstance(m_st, dict) and "happiness" in m_st:
                return m_st["happiness"]
            return m.get("happiness", 100)
        elif hasattr(m, "happiness"):
            return m.happiness
        return 100

    def _get_companion_name(self, m: Any) -> str:
        if isinstance(m, dict):
            sp_id = m.get("species_id", m.get("final_id", m.get("base_id")))
            return self.api.get_species_name(sp_id)
        elif hasattr(m, "current_id"):
            return self.api.get_species_name(m.current_id)
        return "Pokémon"

    def _get_companion_boost_per_berry(self, m: Any) -> int:
        held = None
        if isinstance(m, dict):
            m_st = m.get("mon_state")
            if isinstance(m_st, dict):
                held = m_st.get("held_item")
        elif hasattr(m, "held_item"):
            held = m.held_item
        return 50 if held == "soothe_bell" else 25

    def _get_companion_species_id(self, m: Any) -> Optional[int]:
        if isinstance(m, dict):
            sp = m.get("species_id", m.get("final_id", m.get("base_id")))
        elif hasattr(m, "current_id"):
            sp = m.current_id
        elif hasattr(m, "base_id"):
            sp = m.base_id
        else:
            sp = None
        if sp is not None:
            try:
                return int(sp)
            except (ValueError, TypeError):
                return None
        return None

    def _get_expedition_species_ids(self) -> set:
        exp_ids = set()
        for e in self.state.get("expeditions", []):
            sp = e.get("sp_id")
            if sp is not None:
                try:
                    exp_ids.add(int(sp))
                except (ValueError, TypeError):
                    exp_ids.add(sp)
        return exp_ids

    def _get_roster_and_active_candidates(self, exclude_expeditions: bool = False) -> List[Any]:
        dex = self.state.get("dex", [])
        roster = [d for d in dex if d.get("status") != "evolved"]
        active = self.active_mon
        candidates = list(roster)
        if active:
            active_sp_ids = {d.get("species_id", d.get("final_id", d.get("base_id"))) for d in roster}
            if active.current_id not in active_sp_ids:
                candidates.append(active)
        if exclude_expeditions:
            exp_ids = self._get_expedition_species_ids()
            candidates = [c for c in candidates if self._get_companion_species_id(c) not in exp_ids]
        return candidates

    def get_feed_threshold_plan(self, max_happiness: int, qty: Optional[int] = None, op: str = "<=") -> Dict[str, Any]:
        """Calculates a feeding plan for all companions matching the happiness condition (<=, <, =)."""
        inv = self.state.get("inventory", {})
        available_berries = inv.get("berry_oran", 0)
        if available_berries <= 0:
            return {"ok": False, "error": "You don't have any Oran Berries 🫐 in your bag! Purchase some from the Pokémart (Tab [4])."}

        norm_op = "<="
        if op in ["<", "lt"]:
            norm_op = "<"
        elif op in ["=", "==", "eq"]:
            norm_op = "="

        candidates = self._get_roster_and_active_candidates(exclude_expeditions=True)
        if norm_op == "<":
            target_mons = [c for c in candidates if self._get_companion_happiness(c) < max_happiness and self._get_companion_happiness(c) < 100]
        elif norm_op == "=":
            target_mons = [c for c in candidates if self._get_companion_happiness(c) == max_happiness and self._get_companion_happiness(c) < 100]
        else:
            target_mons = [c for c in candidates if self._get_companion_happiness(c) <= max_happiness and self._get_companion_happiness(c) < 100]

        if not target_mons:
            all_candidates = self._get_roster_and_active_candidates(exclude_expeditions=False)
            if norm_op == "<":
                deployed_targets = [c for c in all_candidates if self._get_companion_happiness(c) < max_happiness and self._get_companion_happiness(c) < 100]
            elif norm_op == "=":
                deployed_targets = [c for c in all_candidates if self._get_companion_happiness(c) == max_happiness and self._get_companion_happiness(c) < 100]
            else:
                deployed_targets = [c for c in all_candidates if self._get_companion_happiness(c) <= max_happiness and self._get_companion_happiness(c) < 100]

            if deployed_targets:
                if max_happiness == 0:
                    return {"ok": False, "error": "All exhausted Pokémon are currently deployed on expeditions and cannot be fed until they return."}
                return {"ok": False, "error": f"All matching Pokémon ({norm_op}{max_happiness}%) are currently deployed on expeditions and cannot be fed."}

            if max_happiness == 0:
                return {"ok": False, "error": "No Pokémon in your roster currently have 0% Happiness! All companions are in high spirits."}
            if norm_op == "=":
                return {"ok": False, "error": f"No Pokémon found with happiness == {max_happiness}% needing berries! All companions are in high spirits."}
            elif norm_op == "<":
                return {"ok": False, "error": f"No Pokémon found with happiness < {max_happiness}% needing berries! All companions are in high spirits."}
            return {"ok": False, "error": f"No Pokémon found with happiness <= {max_happiness}% needing berries! All companions are in high spirits."}

        qty_per_mon = 4 if (qty is None and max_happiness == 0) else (max(1, int(qty)) if qty is not None else None)
        plan_items = []
        rem_berries = available_berries

        for c in target_mons:
            if rem_berries <= 0:
                break
            cur_h = self._get_companion_happiness(c)
            boost = self._get_companion_boost_per_berry(c)
            needed = math.ceil((100 - cur_h) / boost)
            user_qty = needed if qty_per_mon is None else qty_per_mon
            give = min(user_qty, needed, rem_berries)
            if give > 0:
                new_h = min(100, cur_h + give * boost)
                rem_berries -= give
                plan_items.append({
                    "mon": c,
                    "name": self._get_companion_name(c),
                    "cur_h": cur_h,
                    "give_berries": give,
                    "boost": boost,
                    "new_h": new_h,
                    "user_qty": user_qty
                })

        if not plan_items:
            return {"ok": False, "error": "No berries available to feed Pokémon."}

        total_req = sum(item["give_berries"] for item in plan_items)
        b_word = "Oran Berry" if total_req == 1 else "Oran Berries"
        count = len(plan_items)
        plan_type = "exhausted" if max_happiness == 0 else "threshold"

        if max_happiness == 0:
            summary_names = f"{count} exhausted Pokémon" if count > 1 else plan_items[0]["name"]
        else:
            summary_names = f"{count} Pokémon ({norm_op}{max_happiness}%)" if count > 1 else f"{plan_items[0]['name']} ({norm_op}{max_happiness}%)"

        prompt = f"🫐 Feed {total_req} {b_word} to {summary_names} (Req: {total_req}, In Bag: {available_berries})? Type 'confirm' (or 'y')"
        if len(prompt) > 72:
            prompt = f"🫐 Feed {total_req} 🫐 to {summary_names} (Req: {total_req}, Bag: {available_berries})? Type 'y'"
        if len(prompt) > 72:
            prompt = f"Feed {total_req} 🫐 to {summary_names} (Req:{total_req}, Bag:{available_berries})? [y/N]"
        if len(prompt) > 72:
            short_s = f"{count} mons ({norm_op}{max_happiness}%)"
            prompt = f"Feed {total_req} 🫐 to {short_s} (Req:{total_req}, Bag:{available_berries})? [y/N]"
        if len(prompt) > 72:
            prompt = prompt[:69] + "..."

        return {
            "ok": True,
            "error": None,
            "plan_type": plan_type,
            "threshold": max_happiness,
            "op": norm_op,
            "items": plan_items,
            "total_berries": total_req,
            "available_berries": available_berries,
            "summary_names": summary_names,
            "prompt": prompt
        }

    def feed_by_happiness_threshold(
        self,
        max_happiness: int,
        qty: Optional[int] = None,
        confirm: bool = False,
        op: str = "<="
    ) -> Tuple[bool, str]:
        """Feeds a specific amount of Oran Berries to all Pokémon companions matching happiness threshold/equality."""
        plan = self.get_feed_threshold_plan(max_happiness=max_happiness, qty=qty, op=op)
        if not plan.get("ok"):
            return False, plan.get("error", "Could not feed Pokémon.")
        if confirm:
            return True, plan["prompt"]
        return self.execute_feed_plan(plan)

    def get_feed_plan(self, target: Optional[Union[str, int, List[Union[str, int]]]] = None, qty: Optional[int] = None) -> Dict[str, Any]:
        """Calculates the feeding plan without mutating game state."""
        inv = self.state.get("inventory", {})
        available_berries = inv.get("berry_oran", 0)
        if available_berries <= 0:
            return {"ok": False, "error": "You don't have any Oran Berries 🫐 in your bag! Purchase some from the Pokémart (Tab [4])."}

        candidates = self._get_roster_and_active_candidates()
        active = self.active_mon

        # Helper to parse threshold from target
        s_target = str(target).strip().lower() if target is not None else ""

        def _parse_threshold_val(val_str: str) -> Optional[Tuple[str, int]]:
            s = val_str.strip().lower()
            if s in ["0", "0%", "=0", "=0%", "==0", "==0%", "exhausted", "revive", "rev", "zero", "all-zero"]:
                return ("<=", 0)
            m_le = re.match(r"^<=\s*(\d{1,3})%?$", s)
            if m_le:
                return ("<=", min(100, max(0, int(m_le.group(1)))))
            m_lt = re.match(r"^<\s*(\d{1,3})%?$", s)
            if m_lt:
                return ("<", min(100, max(0, int(m_lt.group(1)))))
            m_eq = re.match(r"^={1,2}\s*(\d{1,3})%?$", s)
            if m_eq:
                return ("=", min(100, max(0, int(m_eq.group(1)))))
            m_pct = re.match(r"^(\d{1,3})%$", s)
            if m_pct:
                return ("=", min(100, max(0, int(m_pct.group(1)))))
            if s.isdigit() and 0 <= int(s) <= 100:
                return ("=", int(s))
            return None

        # 1. Check for threshold-based feeding (e.g. "0", "<=50%", "<70", "=70", "70%", "70")
        if target is not None and not isinstance(target, (list, set, tuple)):
            thresh_res = _parse_threshold_val(s_target)
            if thresh_res is not None:
                thresh_op, thresh_val = thresh_res
                return self.get_feed_threshold_plan(max_happiness=thresh_val, qty=qty, op=thresh_op)

        # 2. Check for removed "all" option
        if s_target in ["all", "party", "roster"]:
            return {"ok": False, "error": "The 'all' option has been removed. Feed by species '#id' (e.g. '#25'), or happiness threshold/equality (e.g. '<=50%', '<70', '=70', '70%', '0')."}

        # 3. Default with target=None or empty
        if not s_target:
            if active:
                if active.happiness < 100:
                    target = "active"
                    if qty is None and active.happiness == 0:
                        qty = 4
                    elif qty is None:
                        qty = 1
                else:
                    candidates_avail = self._get_roster_and_active_candidates(exclude_expeditions=True)
                    exhausted_count = len([c for c in candidates_avail if self._get_companion_happiness(c) == 0])
                    if exhausted_count > 0:
                        return {"ok": False, "error": f"Active companion is already at 100% Happiness! You have {exhausted_count} exhausted Pokémon (0% Happiness) in your roster. Type 'feed 0' to restore them all to 100%!"}
                    return {"ok": False, "error": "Active companion is already at 100% Happiness! Usage: feed <#[id]|<=[pct]|<[pct]|[pct]|0> [qty]"}
            else:
                candidates_avail = self._get_roster_and_active_candidates(exclude_expeditions=True)
                exhausted_count = len([c for c in candidates_avail if self._get_companion_happiness(c) == 0])
                if exhausted_count > 0:
                    return {"ok": False, "error": f"No active companion selected! You have {exhausted_count} exhausted Pokémon in your roster. Type 'feed 0' to restore them all to 100%!"}
                return {"ok": False, "error": "No active companion! Usage: feed <#[id]|<=[pct]|<[pct]|[pct]|0> [qty]"}

        # 4. Resolve specific target or list of targets
        target_tokens = []
        if isinstance(target, (list, set, tuple)):
            target_tokens = [str(x).strip() for x in target if str(x).strip()]
        elif "," in str(target):
            target_tokens = [p.strip() for p in str(target).split(",") if p.strip()]
        elif "-" in str(target):
            clean_t = str(target).strip()
            parts_hyphen = clean_t.split("-")
            if len(parts_hyphen) == 2:
                p0 = parts_hyphen[0].strip().lstrip("#")
                p1 = parts_hyphen[1].strip().lstrip("#")
                if p0.isdigit() and p1.isdigit():
                    target_tokens = [f"#{i}" for i in range(int(p0), int(p1) + 1)]
                else:
                    target_tokens = [clean_t]
            else:
                target_tokens = [clean_t]
        else:
            target_tokens = [str(target).strip()]

        matched_targets = []
        for token in target_tokens:
            t_low = token.lower()
            matched = None
            if t_low in ["active", "current"]:
                matched = active
            elif t_low.startswith("#"):
                raw_sp = t_low[1:].strip()
                if raw_sp.isdigit():
                    t_sp_id = int(raw_sp)
                    for c in candidates:
                        sp = self._get_companion_species_id(c)
                        if sp == t_sp_id:
                            matched = c
                            break

            if matched and matched not in matched_targets:
                matched_targets.append(matched)

        if not matched_targets:
            if s_target.isdigit() and int(s_target) > 100:
                return {"ok": False, "error": f"Invalid target '{target}'. For species ID, use '#{target}'. For happiness percentage, specify 0-100 (e.g. '<=70', '=70', '70%')."}
            return {"ok": False, "error": f"Pokémon '{target}' not found in your Roster! Use species ID (e.g. '#25'), 'active', '0' for exhausted, or happiness percentage (e.g. '<=50%', '<70', '=70', '70%')."}

        exp_ids = self._get_expedition_species_ids()

        # Single target
        if len(matched_targets) == 1:
            mon = matched_targets[0]
            mon_sp_id = self._get_companion_species_id(mon)
            name = self._get_companion_name(mon)
            if mon_sp_id in exp_ids:
                msg = f"Cannot feed {name}! They are currently deployed on an expedition."
                if len(msg) > 72:
                    msg = f"Cannot feed {name}! Deployed on an expedition."
                return {"ok": False, "error": msg}

            cur_h = self._get_companion_happiness(mon)
            boost = self._get_companion_boost_per_berry(mon)
            needed = math.ceil((100 - cur_h) / boost)
            user_qty = (4 if cur_h == 0 else 1) if qty is None else max(1, int(qty))

            if cur_h >= 100:
                actual_qty = 1
            else:
                actual_qty = min(user_qty, needed)

            if available_berries < actual_qty:
                return {"ok": False, "error": f"Not enough Oran Berries 🫐! You need {actual_qty}, but only have {available_berries} in your bag."}

            new_h = min(100, cur_h + actual_qty * boost)
            b_word = "Oran Berry" if actual_qty == 1 else "Oran Berries"
            treat_note = " as treat" if cur_h >= 100 else ""
            prompt = f"🫐 Feed {actual_qty} {b_word} to {name}{treat_note} (Req: {actual_qty}, In Bag: {available_berries})? Type 'confirm' (or 'y')"
            if len(prompt) > 72:
                prompt = f"🫐 Feed {actual_qty} 🫐 to {name}{treat_note} (Req: {actual_qty}, Bag: {available_berries})? Type 'y'"
            if len(prompt) > 72:
                prompt = f"Feed {actual_qty} 🫐 to {name} (Req:{actual_qty}, Bag:{available_berries})? [y/N]"
            if len(prompt) > 72:
                prompt = prompt[:69] + "..."

            return {
                "ok": True,
                "error": None,
                "plan_type": "single",
                "items": [{
                    "mon": mon,
                    "name": name,
                    "cur_h": cur_h,
                    "give_berries": actual_qty,
                    "boost": boost,
                    "new_h": new_h,
                    "user_qty": user_qty
                }],
                "total_berries": actual_qty,
                "available_berries": available_berries,
                "summary_names": name,
                "prompt": prompt
            }

        # Multiple targets
        deployed_matched = [m for m in matched_targets if self._get_companion_species_id(m) in exp_ids]
        if len(deployed_matched) == len(matched_targets):
            return {"ok": False, "error": "All targeted Pokémon are currently deployed on expeditions and cannot be fed."}

        plan_items = []
        rem_berries = available_berries
        for mon in matched_targets:
            if self._get_companion_species_id(mon) in exp_ids:
                continue
            if rem_berries <= 0:
                break
            cur_h = self._get_companion_happiness(mon)
            boost = self._get_companion_boost_per_berry(mon)
            needed = math.ceil((100 - cur_h) / boost)
            user_qty = (4 if cur_h == 0 else 1) if qty is None else max(1, int(qty))
            if cur_h >= 100:
                give = 0
            else:
                give = min(user_qty, needed, rem_berries)

            if give > 0:
                new_h = min(100, cur_h + give * boost)
                rem_berries -= give
                plan_items.append({
                    "mon": mon,
                    "name": self._get_companion_name(mon),
                    "cur_h": cur_h,
                    "give_berries": give,
                    "boost": boost,
                    "new_h": new_h,
                    "user_qty": user_qty
                })

        if not plan_items:
            return {"ok": False, "error": "All selected Pokémon are already at 100% Happiness! 💖"}

        total_req = sum(item["give_berries"] for item in plan_items)
        b_word = "Oran Berry" if total_req == 1 else "Oran Berries"
        count = len(plan_items)
        summary_names = f"{count} Pokémon"
        prompt = f"🫐 Feed {total_req} {b_word} to {summary_names} (Req: {total_req}, In Bag: {available_berries})? Type 'confirm' (or 'y')"
        if len(prompt) > 72:
            prompt = f"🫐 Feed {total_req} 🫐 to {summary_names} (Req: {total_req}, Bag: {available_berries})? Type 'y'"
        if len(prompt) > 72:
            prompt = f"Feed {total_req} 🫐 to {summary_names} (Req:{total_req}, Bag:{available_berries})? [y/N]"
        if len(prompt) > 72:
            prompt = prompt[:69] + "..."

        return {
            "ok": True,
            "error": None,
            "plan_type": "batch",
            "items": plan_items,
            "total_berries": total_req,
            "available_berries": available_berries,
            "summary_names": summary_names,
            "prompt": prompt
        }

    def execute_feed_plan(self, plan: Dict[str, Any]) -> Tuple[bool, str]:
        """Executes a validated feeding plan, consuming berries and updating happiness."""
        if not plan.get("ok"):
            return False, plan.get("error", "Invalid feed plan.")

        total_berries = plan.get("total_berries", 0)
        inv = self.state.get("inventory", {})
        available_berries = inv.get("berry_oran", 0)
        if available_berries < total_berries:
            return False, f"Not enough Oran Berries 🫐! Needed {total_berries}, but only have {available_berries} in your bag."

        dex = self.state.get("dex", [])
        active = self.active_mon

        def _apply_feed(m, num_berries: int, boost: int) -> int:
            cur_h = 100
            if isinstance(m, dict):
                m_st = m.get("mon_state")
                if isinstance(m_st, dict) and "happiness" in m_st:
                    cur_h = m_st["happiness"]
                else:
                    cur_h = m.get("happiness", 100)
            elif hasattr(m, "happiness"):
                cur_h = m.happiness

            new_h = min(100, cur_h + (num_berries * boost))
            if isinstance(m, dict):
                m_st = m.get("mon_state")
                if isinstance(m_st, dict):
                    m_st["happiness"] = new_h
                m["happiness"] = new_h
                sp_id = m.get("species_id", m.get("final_id", m.get("base_id")))
                base_id = m.get("base_id", sp_id)
                if active and (active.current_id == sp_id or active.base_id == base_id):
                    active.happiness = new_h
            elif hasattr(m, "happiness"):
                m.happiness = new_h
                sp_id = getattr(m, "current_id", getattr(m, "base_id", None))
                base_id = getattr(m, "base_id", sp_id)
                if active and (m is active or active.current_id == sp_id or active.base_id == base_id):
                    active.happiness = new_h
                for d in dex:
                    d_sp_id = d.get("species_id", d.get("final_id", d.get("base_id")))
                    d_base_id = d.get("base_id", d_sp_id)
                    if d_sp_id == sp_id or (base_id is not None and d_base_id == base_id):
                        m_st = d.get("mon_state")
                        if isinstance(m_st, dict):
                            m_st["happiness"] = new_h
                        d["happiness"] = new_h
            return new_h

        items = plan.get("items", [])
        for item in items:
            item["new_h"] = _apply_feed(item["mon"], item["give_berries"], item["boost"])

        inv["berry_oran"] = available_berries - total_berries
        if inv["berry_oran"] <= 0:
            del inv["berry_oran"]
        self.state["inventory"] = inv
        if active:
            self.set_active_mon(active)
            self.state["happiness"] = active.happiness
        self.save()

        # Generate return message
        if plan.get("plan_type") == "single":
            item = items[0]
            b_str = "Oran Berry" if item["give_berries"] == 1 else "Oran Berries"
            saved_note = f" (Max reached, saved {item['user_qty'] - item['give_berries']} berries!)" if item["user_qty"] > item["give_berries"] else ""
            boost_note = " (+50% Soothe Bell boost!)" if item["boost"] == 50 else ""
            hap_gain = min(100 - item["cur_h"], item["give_berries"] * item["boost"]) if item["cur_h"] < 100 else 0
            return True, f"Fed {item['give_berries']} {b_str} 🫐 to {item['name']}! (+{hap_gain}% Happiness! Current: {item['new_h']}%){boost_note}{saved_note}"

        count = len(items)
        fed_summary = [f"{item['name']} (💖{item['new_h']}%)" for item in items]
        names_str = ", ".join(fed_summary[:6])
        if len(fed_summary) > 6:
            names_str += f" and {len(fed_summary) - 6} more"
        b_word = "Oran Berry" if total_berries == 1 else "Oran Berries"
        qualifier = ""
        if plan.get("plan_type") == "exhausted":
            qualifier = " exhausted"
        elif plan.get("plan_type") == "threshold":
            t_val = plan.get("threshold", 100)
            op_sym = plan.get("op", "<=")
            qualifier = f" ({op_sym}{t_val}% Hap)"
        return True, f"🫐 Fed {total_berries} {b_word} to {count}{qualifier} Pokémon ({names_str})! Restored to readiness!"

    def feed_pokemon(self, target: Optional[Union[str, int, List[Union[str, int]]]] = None, qty: Optional[int] = None, confirm: bool = False) -> Tuple[bool, str]:
        """Feeds Oran Berries (🫐) to Pokémon companions to restore Happiness."""
        plan = self.get_feed_plan(target=target, qty=qty)
        if not plan.get("ok"):
            return False, plan.get("error", "Could not feed Pokémon.")
        if confirm:
            return True, plan["prompt"]
        return self.execute_feed_plan(plan)
