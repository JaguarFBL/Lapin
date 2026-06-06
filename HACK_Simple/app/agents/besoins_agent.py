import json as _json
import logging
import pathlib

from ..models import BesoinsSummary
from ..ai import AIClient

logger = logging.getLogger("agent.besoins")

SYSTEM_PROMPT = """Tu es un vétérinaire nutritionniste spécialisé en lagomorphes, chargé d'extraire les références nutritionnelles de la base de données vétérinaire BDD-Besoins.
Tu dois t'appuyer exclusivement sur les fichiers fournis (nutrient_requirements.csv, ai_tool_contract.json). N'invente AUCUNE valeur. Si une donnée est absente, mets 0 ou [] selon le type.
Tu cites toujours la source exacte (FEDIAF 2024, Merck 2024, CHUV 2025, NCSU) dans le champ 'resume'.
Tu réponds UNIQUEMENT en JSON valide, sans texte avant ou après."""


class BesoinsAgent:
    """Agent Besoins — utilise l'IA pour analyser la base vétérinaire BDD-Besoins et résumer les attentes nutritionnelles."""

    async def run(self) -> BesoinsSummary:
        logger.info("=== BESOINS AGENT RUN ===")
        ai = AIClient()

        bdd_dir = pathlib.Path(__file__).parent.parent / "api" / "BDD-Besoins"
        csv_content = (bdd_dir / "nutrient_requirements.csv").read_text(encoding="utf-8")
        json_content = (bdd_dir / "rabbit_knowledge_pack.json").read_text(encoding="utf-8")
        contract_content = (bdd_dir / "ai_tool_contract.json").read_text(encoding="utf-8")

        prompt = f"""Analyse ces documents de la base de données vétérinaire pour le lapin domestique et extrais les besoins idéaux pour un lapin adulte en entretien (rabbit_adult_maintenance).

Règle importante : Dans ton résumé, cite EXPLICITEMENT les sources utilisées (ex: "Selon les directives FEDIAF 2024..." ou "D'après le CHUV..."). 

=== Fichier 1 : nutrient_requirements.csv ===
{csv_content}

=== Fichier 2 : ai_tool_contract.json ===
{contract_content}

Réponds EXACTEMENT au format JSON suivant, sans texte avant ni après :
{{
  "sucre_max": <float, ex: limite supérieure pour l'amidon/sucre (utiliser starch max si sucre non trouvé)>,
  "fibres_min": <float, ex: minimum pour crude_fibre en %>,
  "calcium_min": <float, conversion en mg/100g (ex: si 0.4% -> 400 mg)>,
  "calcium_max": <float, conversion en mg/100g (ex: si 0.5% -> 500 mg) ou limite supérieure de sécurité en mg>,
  "types_ideaux": [<liste des types recommandés, ex: "hay_based", "pellets_herbes">],
  "ingredients_interdits": [<liste des catégories interdites extraites des notes ou contrats>],
  "resume": "<un résumé clair en français des attentes nutritionnelles. Tu DOIS citer les sources (FEDIAF, Merck, etc.) dans ce texte.>"
}}"""

        logger.info("Envoi du prompt Besoins à Gemini (avec BDD)...")
        data = await ai.generate_json(prompt, SYSTEM_PROMPT)
        logger.info("Réponse Besoins reçue: %s", data)

        return BesoinsSummary(
            sucre_max=float(data["sucre_max"]),
            fibres_min=float(data["fibres_min"]),
            calcium_min=float(data["calcium_min"]),
            calcium_max=float(data["calcium_max"]),
            types_ideaux=data["types_ideaux"],
            ingredients_interdits=data["ingredients_interdits"],
            resume=data["resume"],
        )
