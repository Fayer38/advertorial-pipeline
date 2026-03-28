"""
Classe abstraite de base pour tous les agents du pipeline.
Chaque agent hérite de BaseAgent et implémente sa méthode `run()`.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Classe de base pour tous les agents du pipeline advertorial."""

    def __init__(self, name: str, output_dir: str = "data/output"):
        self.name = name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    async def run(self, **kwargs) -> dict:
        """
        Méthode principale de l'agent.
        Chaque agent implémente sa propre logique ici.
        Retourne un dict conforme au schéma Pydantic correspondant.
        """
        pass

    def save_output(self, data: dict, filename: str) -> Path:
        """Sauvegarde la sortie JSON de l'agent."""
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        self.logger.info(f"[{self.name}] Sortie sauvegardée : {filepath}")
        return filepath

    def load_input(self, filepath: str) -> dict:
        """Charge un fichier JSON d'entrée (sortie d'un agent précédent)."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"[{self.name}] Fichier introuvable : {filepath}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.logger.info(f"[{self.name}] Input chargé : {filepath}")
        return data

    def log_start(self, **kwargs):
        """Log le démarrage de l'agent avec ses paramètres."""
        params = ", ".join(f"{k}={v}" for k, v in kwargs.items() if v)
        self.logger.info(f"[{self.name}] Démarrage — {params}")

    def log_done(self, result_summary: str = ""):
        """Log la fin d'exécution de l'agent."""
        self.logger.info(f"[{self.name}] Terminé — {result_summary}")

    def log_error(self, error: Exception, context: str = ""):
        """Log une erreur avec contexte."""
        self.logger.error(f"[{self.name}] Erreur ({context}): {error}")
