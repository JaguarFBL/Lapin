import json as _json
import logging
from typing import Dict, List, Optional
from fastapi import HTTPException
import httpx

from ..models import ProduitRaw, ProduitSummary
from ..ai import AIClient

logger = logging.getLogger("agent.produit")

OFF_API_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json?fields=product_name,brands,ingredients_text,nutriments,image_front_url"
REQUEST_TIMEOUT = 10

PLACEHOLDER_IMG = "https://images.unsplash.com/photo-1548767797-d8c844163c4c?w=400"

SYSTEM_PROMPT = """Tu es un analyste spécialisé dans l'évaluation d'aliments pour lapins domestiques, chargé d'examiner les données issues de l'API OpenFoodFacts.
Tu évalues le produit sur la base des valeurs nutritionnelles fournies (sucre, fibres, calcium, ingrédients) et des seuils critiques donnés dans le prompt.
Si les données OpenFoodFacts sont incomplètes (valeurs à 0 ou liste d'ingrédients vide), tu PEUX utiliser la recherche web pour trouver des informations nutritionnelles supplémentaires sur ce produit. Consulte au moins 2 sources différentes pour vérifier.
Cite les sources web consultées dans le champ 'sources' de ta réponse.
Détecte les ingrédients à risque (céréales, sucres ajoutés) dans la liste fournie ou trouvée via recherche.
Tu réponds UNIQUEMENT en JSON valide, sans texte avant ou après."""


def _split_ingredients(text: Optional[str]) -> List[str]:
    if not text:
        return []
    return [i.strip() for i in text.split(",") if i.strip()]


def _safe_float(val, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _map_api_to_raw(barcode: str, api_product: dict) -> ProduitRaw:
    nutriments = api_product.get("nutriments", {})

    sucre = _safe_float(nutriments.get("sugars_100g"), 0.0)
    fibres = _safe_float(nutriments.get("fiber_100g"), 0.0)
    calcium_g = _safe_float(nutriments.get("calcium_100g"), None)
    if calcium_g is None:
        calcium_mg = 0.0
    else:
        calcium_mg = calcium_g * 1000

    ingredients = _split_ingredients(api_product.get("ingredients_text"))
    nom = api_product.get("product_name") or f"Produit {barcode}"
    image_url = api_product.get("image_front_url") or PLACEHOLDER_IMG

    return ProduitRaw(
        barcode=barcode,
        nom=nom,
        image_url=image_url,
        sucre=sucre,
        fibres=fibres,
        calcium=calcium_mg,
        ingredients=ingredients,
    )


class ProduitAgent:
    """Agent Produit — récupère les données via OpenFoodFacts API et les analyse via Gemini."""

    async def fetch(self, barcode: str) -> ProduitRaw:
        url = OFF_API_URL.format(barcode=barcode)
        logger.info("Appel OpenFoodFacts API: %s", url)

        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                logger.error("Produit non trouvé sur OpenFoodFacts: %s", barcode)
                raise HTTPException(
                    status_code=404,
                    detail=f"Produit '{barcode}' introuvable sur OpenFoodFacts.",
                )
            logger.error("Erreur HTTP OpenFoodFacts: %s", exc)
            raise HTTPException(status_code=502, detail=f"Erreur API OpenFoodFacts: {exc}")
        except httpx.TimeoutException:
            logger.error("Timeout OpenFoodFacts pour: %s", barcode)
            raise HTTPException(status_code=504, detail="Timeout API OpenFoodFacts")
        except httpx.RequestError as exc:
            logger.error("Erreur réseau OpenFoodFacts: %s", exc)
            raise HTTPException(status_code=502, detail=f"Erreur réseau: {exc}")

        if data.get("status") != 1 or not data.get("product"):
            logger.error("Produit non trouvé sur OpenFoodFacts (status=0): %s", barcode)
            raise HTTPException(
                status_code=404,
                detail=f"Produit '{barcode}' introuvable sur OpenFoodFacts.",
            )

        api_product = data["product"]
        logger.info("Produit trouvé: %s", api_product.get("product_name", "?"))

        raw = _map_api_to_raw(barcode, api_product)
        logger.info(
            "Données parsées: sucre=%s, fibres=%s, calcium=%s, %d ingrédients",
            raw.sucre, raw.fibres, raw.calcium, len(raw.ingredients),
        )
        return raw

    async def run(self, barcode: str) -> ProduitSummary:
        logger.info("=== PRODUIT AGENT RUN === barcode=%s", barcode)
        raw = await self.fetch(barcode)
        ai = AIClient()

        raw_dict = raw.model_dump()
        prompt = f"""Analyse ce produit pour lapin (domestique) et résume ses caractéristiques et risques.

Données brutes du produit (issues de OpenFoodFacts) :
{_json.dumps(raw_dict, indent=2, ensure_ascii=False)}

Critères d'évaluation pour un lapin :
- Sucre maximum idéal : 8g/100g (critique si > 15g)
- Fibres minimum idéal : 15g/100g (critique si < 10g)
- Calcium idéal : 100-500 mg/100g (critique si > 600mg)
- Céréales interdites pour les lapins (mots-clés : blé, maïs, avoine, orge, amidon, céréale)
- Sucres ajoutés interdits (mots-clés : miel, sirop, mélasse, sucre, fructose, glucose)

Si les données ci-dessus sont incomplètes (valeurs à 0 ou ingrédients vides), effectue une RECHERCHE WEB sur ce produit (nom + marque + code-barres) pour trouver les informations nutritionnelles manquantes. Consulte au moins 2 sources différentes (sites marchands, fiches fabricant, avis). Ne te fie pas à une seule source.

Réponds EXACTEMENT au format JSON suivant, sans texte avant ni après :
{{
  "barcode": "{raw.barcode}",
  "nom": "{raw.nom}",
  "image_url": "{raw.image_url}",
  "sucre": <float, valeur trouvée sur OFF ou via recherche web, 0 si absente>,
  "fibres": <float, idem>,
  "calcium": <float, idem>,
  "ingredients": [<liste d'ingrédients, vide si aucun trouvé>],
  "a_cereales": <true/false>,
  "ingredients_risques": [<liste des ingrédients à risque détectés>],
  "resume": "<résumé complet en français du produit, de ses risques/nutriments, et des sources consultées>",
  "sources": [<URLs des sites web consultés pour compléter les données>]
}}"""

        logger.info("Envoi du prompt Produit à Gemini avec recherche web...")
        data = await ai.generate_json(prompt, SYSTEM_PROMPT, use_web_search=True)
        logger.info(
            "Réponse Produit reçue: nom=%s, a_cereales=%s, resume=%s...",
            data.get("nom"), data.get("a_cereales"), str(data.get("resume", ""))[:80],
        )

        return ProduitSummary(
            barcode=data.get("barcode", raw.barcode),
            nom=data.get("nom", raw.nom),
            image_url=data.get("image_url", raw.image_url),
            sucre=float(data.get("sucre", raw.sucre)),
            fibres=float(data.get("fibres", raw.fibres)),
            calcium=float(data.get("calcium", raw.calcium)),
            ingredients=data.get("ingredients", raw.ingredients),
            a_cereales=bool(data.get("a_cereales", False)),
            ingredients_risques=data.get("ingredients_risques", []),
            resume=data.get("resume", ""),
            sources=data.get("sources", []),
        )
