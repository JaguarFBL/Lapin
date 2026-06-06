from __future__ import annotations

import logging
from typing import List, Optional, Any
from pydantic import BaseModel
from fastapi import HTTPException

from .models import BesoinsSummary, PersonnelSummary, ProduitSummary, Recommandation
from .agents.besoins_agent import BesoinsAgent
from .agents.personnel_agent import PersonnelAgent, MOCK_LAPINS_DB
from .agents.produit_agent import ProduitAgent
from .agents.comparateur_agent import ComparateurAgent

logger = logging.getLogger("debug")


class TraceStep(BaseModel):
    agent: str
    etape: str
    description: str
    entree: Optional[Any] = None
    sortie: Optional[Any] = None


class DebugScanResult(BaseModel):
    recommandation: Recommandation
    traces: List[TraceStep]


class DebugScanner:
    """Exécute le scan avec traçage de chaque agent et de leurs réflexions IA."""

    def __init__(self):
        self.traces: List[TraceStep] = []

    def _add(self, agent: str, etape: str, description: str, entree=None, sortie=None):
        logger.debug("Trace: %s | %s | %s", agent, etape, description[:60])
        self.traces.append(TraceStep(
            agent=agent, etape=etape, description=description,
            entree=entree, sortie=sortie,
        ))

    async def run(self, barcode: str, lapin_id: str = "lapin_healthy") -> DebugScanResult:
        logger.info("=== DEBUG SCAN RUN === barcode=%s, lapin_id=%s", barcode, lapin_id)

        # ── Agent Besoins ────────────────────────────────────────
        logger.info("--- Phase 1/4: Agent Besoins ---")
        self._add("Besoins", "consultation_db",
            "Consultation de la vraie base de données BDD-Besoins (CSV/JSON) + prompt Gemini",
            {"source": "app/api/BDD-Besoins"})

        besoins_agent = BesoinsAgent()
        self._add("Besoins", "ia_prompt",
            "Prompt envoyé à Gemini avec extraits de la vraie BDD", {"source": "nutrient_requirements.csv"})

        try:
            besoins = await besoins_agent.run()
        except Exception as exc:
            logger.error("BesoinsAgent échoué: %s", exc, exc_info=True)
            raise

        self._add("Besoins", "ia_reponse",
            "Réponse Gemini parsée", None, besoins.model_dump())

        # ── Agent Personnel ──────────────────────────────────────
        logger.info("--- Phase 2/4: Agent Personnel ---")
        self._add("Personnel", "consultation_db",
            "Récupération profil lapin + prompt Gemini",
            {"lapin_id": lapin_id, "table": "MOCK_LAPINS_DB"})

        if lapin_id not in MOCK_LAPINS_DB:
            logger.error("Lapin introuvable: %s", lapin_id)
            raise HTTPException(status_code=404, detail=f"Lapin '{lapin_id}' introuvable.")
        raw_lapin = MOCK_LAPINS_DB[lapin_id]

        self._add("Personnel", "donnees_brutes",
            "Données brutes du lapin", None, raw_lapin)

        personnel_agent = PersonnelAgent()
        self._add("Personnel", "ia_prompt",
            "Prompt envoyé à Gemini", {"lapin_id": lapin_id, "donnees": raw_lapin})

        try:
            personnel = await personnel_agent.run(lapin_id)
        except Exception as exc:
            logger.error("PersonnelAgent échoué: %s", exc, exc_info=True)
            raise

        self._add("Personnel", "ia_reponse",
            "Réponse Gemini parsée", None, personnel.model_dump())

        # ── Agent Produit ────────────────────────────────────────
        logger.info("--- Phase 3/4: Agent Produit ---")
        self._add("Produit", "consultation_api",
            "Appel OpenFoodFacts API + prompt Gemini",
            {"barcode": barcode, "api": "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"})

        agent_produit = ProduitAgent()
        self._add("Produit", "api_response",
            "Réponse JSON parsée depuis OpenFoodFacts", {"barcode": barcode})

        try:
            produit = await agent_produit.run(barcode)
        except Exception as exc:
            logger.error("ProduitAgent échoué: %s", exc, exc_info=True)
            raise

        self._add("Produit", "ia_reponse",
            "Réponse Gemini parsée", None, produit.model_dump())

        # ── Agent Comparateur ────────────────────────────────────
        logger.info("--- Phase 4/4: Agent Comparateur ---")
        self._add("Comparateur", "ia_prompt",
            "Prompt à Gemini: comparaison des 3 sources",
            {"besoins": besoins.model_dump(), "personnel": personnel.model_dump(), "produit": produit.model_dump()})

        comparateur = ComparateurAgent()
        try:
            recommandation = await comparateur.comparer(besoins, personnel, produit)
        except Exception as exc:
            logger.error("ComparateurAgent échoué: %s", exc, exc_info=True)
            raise

        self._add("Comparateur", "ia_reponse",
            "Recommandation finale Gemini", None, recommandation.model_dump())

        logger.info("=== SCAN TERMINÉ === est_adapte=%s, resume=%s",
                     recommandation.est_adapte, recommandation.resume[:100])
        return DebugScanResult(recommandation=recommandation, traces=self.traces)
