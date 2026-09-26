"""Spieler-Entity (T-004, Deliverable 4).

Stats kommen ausschließlich aus `balance/stat_curves.json` + ausgerüsteten Items;
Fähigkeiten/Keys werden an ihren `granted_at`-Nodes vergeben (map_graph.json) und
als registrierte Ability-Handler geführt. Kein hartkodierter Content.
"""
from __future__ import annotations

from .constants import CRIT_DAMAGE_BASE, CRIT_CHANCE_BASE
from .data import GameData


class Player:
    """Kämpfer mit Schwert — Stats, Ausrüstung, Fähigkeiten, Meta-Fortschritt."""

    def __init__(self, data: GameData):
        self.data = data
        self.level = 1
        self.xp = 0
        self.lumen = 0
        self.abilities: set[str] = set()   # Fähigkeit- + Schlüssel-IDs (Gating)
        self.bosses_defeated: set[str] = set()
        self.visited_nodes: set[str] = set()
        self.equipment: dict[str, dict] = {}  # slot → Item-Dict (inkl. gerollter Affixe)
        self.inventory: list[dict] = []

    # --- Stats -----------------------------------------------------------------
    def _level_row(self) -> dict:
        return self.data.level_row(self.level)

    @property
    def max_hp(self) -> int:
        total = float(self._level_row()["base_hp"])
        for item in self.equipment.values():
            total += float(item["base_stats"].get("max_hp", 0))
            for affix in item.get("affixes_rolled", []):
                if affix["stat_key"] == "max_hp":
                    total += affix["value"]
        return max(1, int(total))

    @property
    def attack(self) -> float:
        total = float(self._level_row()["base_attack"])
        for item in self.equipment.values():
            total += float(item["base_stats"].get("attack", 0))
            for affix in item.get("affixes_rolled", []):
                if affix["stat_key"] == "attack":
                    total += affix["value"]
        return max(1.0, total)

    @property
    def defense(self) -> float:
        total = float(self._level_row()["base_defense"])
        for item in self.equipment.values():
            total += float(item["base_stats"].get("defense", 0))
            for affix in item.get("affixes_rolled", []):
                if affix["stat_key"] == "defense":
                    total += affix["value"]
        return max(0.0, total)

    @property
    def speed_pct(self) -> float:
        """Bewegungsgeschwindigkeit in % des Basiswerts (100 = normal)."""
        bonus = 0.0
        for item in self.equipment.values():
            bonus += float(item["base_stats"].get("speed", 0))
            for affix in item.get("affixes_rolled", []):
                if affix["stat_key"] == "speed":
                    bonus += affix["value"]
        return max(25.0, min(175.0, 100.0 + bonus))

    @property
    def crit_chance(self) -> float:
        bonus = 0.0
        for item in self.equipment.values():
            bonus += float(item["base_stats"].get("crit_chance", 0))
            for affix in item.get("affixes_rolled", []):
                if affix["stat_key"] == "crit_chance":
                    bonus += affix["value"]
        return max(0.0, min(60.0, CRIT_CHANCE_BASE + bonus))

    @property
    def crit_damage(self) -> float:
        bonus = 0.0
        for item in self.equipment.values():
            bonus += float(item["base_stats"].get("crit_damage", 0))
            for affix in item.get("affixes_rolled", []):
                if affix["stat_key"] == "crit_damage":
                    bonus += affix["value"]
        return CRIT_DAMAGE_BASE + max(0.0, bonus)

    @property
    def lumen_gain_pct(self) -> float:
        """Bonus auf Lumen-Ertrag in % (Meta-Währung, GDD-Pillar 1)."""
        bonus = 0.0
        for item in self.equipment.values():
            bonus += float(item["base_stats"].get("lumen_gain", 0))
            for affix in item.get("affixes_rolled", []):
                if affix["stat_key"] == "lumen_gain":
                    bonus += affix["value"]
        return max(0.0, bonus)

    # --- Fähigkeiten (Ability-Handler) -------------------------------------------
    def has_ability(self, ability_id: str) -> bool:
        """Gating-Check: Fähigkeit oder Schlüssel vorhanden?"""
        return ability_id in self.abilities

    def grant(self, ability_id: str) -> None:
        """Fähigkeit/Schlüssel vergeben (wird am granted_at-Node aufgerufen)."""
        if ability_id not in {a["id"] for a in self.data.abilities}:
            raise KeyError(f"Unbekannte Fähigkeit/Schlüssel-ID: {ability_id}")
        self.abilities.add(ability_id)

    # --- Ausrüstung ----------------------------------------------------------------
    def equip(self, item: dict) -> None:
        """Item einsammeln; pro Slot wird das zuletzt gefundene Item ausgerüstet."""
        self.inventory.append(item)
        slot = item["slot"]
        if slot in ("weapon", "armor", "accessory"):
            self.equipment[slot] = item

    # --- Fortschritt -----------------------------------------------------------------
    def gain_xp(self, amount: float) -> int:
        """XP vergeben; liefert Anzahl aufgestiegener Level."""
        self.xp += max(0.0, amount)
        gained = 0
        while (self.level < len(self.data.levels)
               and self.xp >= self._level_row()["xp_to_next"]):
            self.xp -= self._level_row()["xp_to_next"]
            self.level += 1
            gained += 1
        return gained

    def gain_lumen(self, amount: float) -> None:
        self.lumen += max(0.0, amount) * (1.0 + self.lumen_gain_pct / 100.0)

    # --- Persistenz (Save-System, Deliverable 6) ---------------------------------------
    def to_save(self) -> dict:
        return {
            "level": self.level,
            "xp": self.xp,
            "lumen": round(self.lumen, 2),
            "abilities": sorted(self.abilities),
            "bosses_defeated": sorted(self.bosses_defeated),
            "visited_nodes": sorted(self.visited_nodes),
        }

    @classmethod
    def from_save(cls, data: GameData, save: dict) -> "Player":
        player = cls(data)
        player.level = int(save.get("level", 1))
        player.xp = float(save.get("xp", 0.0))
        player.lumen = float(save.get("lumen", 0.0))
        for ability_id in save.get("abilities", []):
            player.grant(ability_id)
        player.bosses_defeated.update(save.get("bosses_defeated", []))
        player.visited_nodes.update(save.get("visited_nodes", []))
        return player
