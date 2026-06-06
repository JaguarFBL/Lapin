import json as _json
import logging
from typing import Dict
from fastapi import HTTPException

from ..models import PersonnelRaw, PersonnelSummary
from ..ai import AIClient

logger = logging.getLogger("agent.personnel")

MOCK_LAPINS_DB: Dict[str, dict] = {
    "lapin_healthy": {
        "id": "lapin_healthy",
        "nom": "Panpan",
        "poids": 2.2,
        "age": 2.0,
        "allergies": [],
        "historique_medical": [],
    },
    "lapin_stones": {
        "id": "lapin_stones",
        "nom": "Gribouille",
        "poids": 2.0,
        "age": 4.0,
        "allergies": [],
        "historique_medical": ["calculs urinaires"],
    },
    "lapin_allergic": {
        "id": "lapin_allergic",
        "nom": "Cacahuète",
        "poids": 1.8,
        "age": 1.0,
        "allergies": ["carotte"],
        "historique_medical": [],
    },
    "lapin_young": {
        "id": "lapin_young",
        "nom": "Junior",
        "poids": 0.7,
        "age": 0.5,
        "allergies": [],
        "historique_medical": [],
    },
}


SYSTEM_PROMPT = """Tu es un vétérinaire clinicien spécialisé en médecine des lagomorphes, chargé d'analyser le profil individuel d'un lapin.
Tu interprètes son âge, son poids, ses allergies et son historique médical pour en déduire les implications nutritionnelles personnalisées.
Sois précis : un jeune en croissance a des besoins différents d'un adulte sain ou d'un lapin avec antécédents de calculs urinaires.
N'invente PAS d'allergies ou d'antécédents supplémentaires.
Tu réponds UNIQUEMENT en JSON valide, sans texte avant ou après."""


class PersonnelAgent:
    """Agent Personnel — utilise l'IA pour analyser le profil du lapin et résumer ses besoins personnalisés."""

    async def run(self, lapin_id: str) -> PersonnelSummary:
        logger.info("=== PERSONNEL AGENT RUN === lapin_id=%s", lapin_id)
        if lapin_id not in MOCK_LAPINS_DB:
            logger.error("Lapin introuvable: %s", lapin_id)
            raise HTTPException(status_code=404, detail=f"Lapin '{lapin_id}' introuvable.")
        raw = PersonnelRaw(**MOCK_LAPINS_DB[lapin_id])
        ai = AIClient()

        prompt = f"""Analyse le profil de ce lapin et résume ses besoins nutritionnels personnalisés.

Profil du lapin :
{_json.dumps(MOCK_LAPINS_DB[lapin_id], indent=2, ensure_ascii=False)}

Réponds EXACTEMENT au format JSON suivant, sans texte avant ni après :
{{
  "id": "{raw.id}",
  "nom": "{raw.nom}",
  "poids": {raw.poids},
  "age": {raw.age},
  "allergies": {_json.dumps(raw.allergies)},
  "historique_medical": {_json.dumps(raw.historique_medical)},
  "resume": "<un résumé du profil du lapin et des implications nutritionnelles pour lui>"
}}"""

        logger.info("Envoi du prompt Personnel à Gemini...")
        data = await ai.generate_json(prompt, SYSTEM_PROMPT)
        logger.info("Réponse Personnel reçue: nom=%s, resume=%s...",
                     data.get("nom"), str(data.get("resume", ""))[:80])

        return PersonnelSummary(
            id=data.get("id", raw.id),
            nom=data.get("nom", raw.nom),
            poids=float(data.get("poids", raw.poids)),
            age=float(data.get("age", raw.age)),
            allergies=data.get("allergies", raw.allergies),
            historique_medical=data.get("historique_medical", raw.historique_medical),
            resume=data.get("resume", ""),
        )
