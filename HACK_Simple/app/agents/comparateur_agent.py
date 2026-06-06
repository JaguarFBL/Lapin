import json as _json
import logging
import pathlib
from typing import List

from ..models import BesoinsSummary, PersonnelSummary, ProduitSummary, Recommandation, Alternative, ScoreProduit, NoteNutriment
from ..ai import AIClient

logger = logging.getLogger("agent.comparateur")

SYSTEM_PROMPT = """Tu es un vétérinaire expert en décision nutritionnelle pour lagomorphes, chargé de croiser 4 sources d'information pour produire une recommandation finale.

Règles de raisonnement :
1. Les BESOINS IDÉAUX (Source 1) sont la référence générique pour un lapin adulte sain.
2. Le PROFIL LAPIN (Source 2) peut modifier ces seuils : un lapin avec calculs doit avoir un calcium réduit, un jeune a besoin de plus de calcium, un allergique exclut certains aliments.
3. Le PRODUIT (Source 3) est évalué selon les seuils modifiés par le profil.
4. Les RÈGLES CLINIQUES (Source 4) sont impératives : si une règle s'applique, tu dois l'utiliser pour ajuster les seuils.

Tu peux utiliser la RECHERCHE WEB pour vérifier les données du produit (Source 3) si elles te semblent incomplètes ou incohérentes, et pour trouver des alternatives réalistes. Consulte plusieurs sources.
Ne conclus JAMAIS 'adapté' si au moins un seuil critique (calcium, fibres, sucre) est dépassé après application des règles cliniques.
Propose des alternatives réalistes qui répondent aux contraintes du lapin.
Tu réponds UNIQUEMENT en JSON valide, sans texte avant ou après."""


class ComparateurAgent:
    """Agent Comparateur — utilise l'IA pour comparer les 3 entrées et produire la recommandation finale."""

    async def comparer(
        self, besoins: BesoinsSummary, personnel: PersonnelSummary, produit: ProduitSummary
    ) -> Recommandation:
        logger.info("=== COMPARATEUR AGENT RUN ===")
        logger.info("Besoins: sucre_max=%s, fibres_min=%s, calcium_min=%s, calcium_max=%s",
                     besoins.sucre_max, besoins.fibres_min, besoins.calcium_min, besoins.calcium_max)
        logger.info("Personnel: nom=%s, allergies=%s, historique=%s",
                     personnel.nom, personnel.allergies, personnel.historique_medical)
        logger.info("Produit: nom=%s, sucre=%s, fibres=%s, calcium=%s, a_cereales=%s",
                     produit.nom, produit.sucre, produit.fibres, produit.calcium, produit.a_cereales)

        ai = AIClient(model="gemini-3.1-pro-preview")
        
        bdd_dir = pathlib.Path(__file__).parent.parent / "api" / "BDD-Besoins"
        rules_content = (bdd_dir / "clinical_rules.json").read_text(encoding="utf-8")

        prompt = f"""Compare les 3 sources d'information et décide si le produit est adapté à ce lapin.

### Source 1 : BESOINS IDÉAUX (général)
{_json.dumps(besoins.model_dump(), indent=2, ensure_ascii=False)}

### Source 2 : PROFIL DU LAPIN
{_json.dumps(personnel.model_dump(), indent=2, ensure_ascii=False)}

### Source 3 : PRODUIT ANALYSÉ
{_json.dumps(produit.model_dump(), indent=2, ensure_ascii=False)}

### Source 4 : RÈGLES CLINIQUES
{rules_content}

### Source 5 : GRILLE D'ÉVALUATION QUANTIFIÉE (CHUV 2025)
Utilise cette grille pour calculer une NOTE sur 100 :

| Nutriment | Seuil | Type | Pts max | Règle de calcul |
|---|---|---|---|---|
| Fibres brutes | ≥ 18% | min | 25 | 0 pt si 0%, 25 pts si ≥ 18%, proportionnel entre les deux |
| Protéines brutes | ≤ 16% | max | 25 | 25 pts si ≤ 16%, 0 pt si ≥ 30%, dégressif entre les deux |
| Matières grasses | ≤ 2.5% | max | 25 | 25 pts si ≤ 2.5%, 0 pt si ≥ 10%, dégressif entre les deux |
| Calcium | ≤ 1.0% | max | 25 | 25 pts si ≤ 1.0%, 0 pt si ≥ 2.5%, dégressif entre les deux |

**Pénalités :**
- Contient des céréales (blé, maïs, avoine, orge, amidon) : -15 pts
- Sucre > 8g/100g : -10 pts
- Ingrédient interdit/allergène présent : -10 pts
- Une valeur nutritionnelle est à 0 (non renseignée) : -5 pts par valeur manquante

**Grille de grade :**
- A (≥ 90) : Excellent, produit recommandé
- B (≥ 75) : Bon, produit acceptable
- C (≥ 60) : Passable, produit toléré avec précautions
- D (≥ 40) : Médiocre, produit déconseillé
- E (< 40) : Très insuffisant, produit dangereux

Instructions de raisonnement :
1. Analyse le profil du lapin (Source 2) et trouve les Règles Cliniques (Source 4) qui s'appliquent à lui.
2. Calcule les nouveaux seuils personnalisés pour ce lapin.
3. Pour chaque nutriment, calcule les points selon la grille (Source 5).
4. Applique les pénalités si nécessaire.
5. Calcule le score total /100 et détermine le grade.
6. Compare le produit (Source 3) aux nouveaux seuils calculés.
7. Propose jusqu'à 3 alternatives adaptées.

Réponds EXACTEMENT au format JSON suivant :
{{
  "nom_produit": "{produit.nom}",
  "image_produit": "{produit.image_url}",
  "est_adapte": <true/false>,
  "resume": "<résumé de la décision en français incluant le score et le grade>",
  "conseil": "<conseil détaillé en français>",
  "alertes": [<liste des alertes spécifiques>],
  "alternatives": [
    {{"barcode": "code_barre_fictif", "nom": "nom produit", "raison": "pourquoi cette alternative"}}
  ],
  "score": {{
    "total": <float 0-100>,
    "grade": "<A|B|C|D|E>",
    "details": [
      {{"nom": "fibres", "valeur_produit": <float>, "unite": "%", "seuil_min": 18, "seuil_max": null, "points": <float 0-25>, "statut": "ok|below_min|above_max|non_renseigne"}},
      {{"nom": "proteines", "valeur_produit": <float>, "unite": "%", "seuil_min": null, "seuil_max": 16, "points": <float 0-25>, "statut": "ok|below_min|above_max|non_renseigne"}},
      {{"nom": "gras", "valeur_produit": <float>, "unite": "%", "seuil_min": null, "seuil_max": 2.5, "points": <float 0-25>, "statut": "ok|below_min|above_max|non_renseigne"}},
      {{"nom": "calcium", "valeur_produit": <float>, "unite": "%", "seuil_min": null, "seuil_max": 1.0, "points": <float 0-25>, "statut": "ok|below_min|above_max|non_renseigne"}}
    ]
  }}
}}"""

        logger.info("Envoi du prompt Comparateur à Gemini avec règles cliniques et recherche web...")
        data = await ai.generate_json(prompt, SYSTEM_PROMPT, use_web_search=True)
        logger.info("Réponse Comparateur: est_adapte=%s, resume=%s...",
                     data.get("est_adapte"), str(data.get("resume", ""))[:100])

        alternatives_data = data.get("alternatives", [])
        alternatives = [Alternative(**a) for a in alternatives_data] if alternatives_data else []

        score_data = data.get("score")
        score = None
        if score_data and isinstance(score_data, dict):
            details_data = score_data.get("details", [])
            details = [NoteNutriment(**d) for d in details_data] if details_data else []
            score = ScoreProduit(
                total=float(score_data.get("total", 0)),
                grade=str(score_data.get("grade", "")),
                details=details,
            )

        return Recommandation(
            nom_produit=data.get("nom_produit", produit.nom),
            image_produit=data.get("image_produit", produit.image_url),
            est_adapte=bool(data.get("est_adapte", False)),
            resume=data.get("resume", ""),
            conseil=data.get("conseil", ""),
            alertes=data.get("alertes", []),
            alternatives=alternatives,
            score=score,
        )
