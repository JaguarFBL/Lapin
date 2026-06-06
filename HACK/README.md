# Rabbit Scan

API backend type **Yuka** pour lapins. Scannez un code-barres via OpenFoodFacts + recherche web Gemini, croisez avec le profil du lapin et les besoins vétérinaires, obtenez une recommandation avec **score quantifié (0-100, grade A-E)**.

## Architecture

```
POST /debug-scan { barcode, rabbit_id }
          │
     DebugScanner (séquentiel, tracé)
     ┌────┴────┐────┐────┐
     │         │    │    │
  Besoins  Personnel Produit  ← 3 agents → Comparateur
  (BDD    (MOCK     (OFF     (croise tout +
   locale) lapins)   API+Web) grille score)
     │         │    │         │
     └─────────┴────┴─────────┘
                    │
          Recommandation + Score /100
```

## Fichiers clés

| Fichier | Rôle |
|---|---|
| `app/main.py` | Point d'entrée FastAPI (port 8080) |
| `app/ai.py` | Client Gemini : `generate()` / `generate_json()`, support Google Search grounding |
| `app/models.py` | Modèles Pydantic : entrées/sorties de tous les agents, score, grade |
| `app/debug.py` | Ordonnanceur : enchaîne les 4 agents avec traçage complet |
| `app/api/dashboard.py` | Routes : `GET /dashboard`, `POST /debug-scan`, `POST /run-tests` |
| `app/api/dashboard.html` | UI complète : scan + tests + score visuel |

## 4 Agents (modèle → entrée → source → sortie)

| Agent | Fichier | Modèle | Entrée | Source | Sortie |
|---|---|---|---|---|---|
| **Besoins** | `agents/besoins_agent.py` | `gemini-3-flash-preview` | (rien) | Fichiers `BDD-Besoins/` (CSV, JSON) | `BesoinsSummary` |
| **Personnel** | `agents/personnel_agent.py` | `gemini-3-flash-preview` | `lapin_id` | `MOCK_LAPINS_DB` (dict) | `PersonnelSummary` |
| **Produit** | `agents/produit_agent.py` | `gemini-3-flash-preview` (+ web) | `barcode` | OpenFoodFacts API + Google Search | `ProduitSummary` |
| **Comparateur** | `agents/comparateur_agent.py` | `gemini-3.1-pro-preview` (+ web) | 3 sorties ci-dessus | Règles cliniques + grille CHUV 2025 | `Recommandation` + `Score` |

## Où insérer le code-barres

- **Dashboard** : champ texte libre (suggestions : Flocons avoine `3229820019307`, Cruesly `3168930010265`)
- **API directe** : `POST /debug-scan {"barcode":"3229820019307","rabbit_id":"lapin_healthy"}`

## Où sont récupérées les données

| Donnée | Source | Code |
|---|---|---|
| Produit (OFF) | `https://world.openfoodfacts.org/api/v2/product/{code}.json` | `produit_agent.py:12` |
| Données manquantes OFF | Google Search grounding dans Gemini | `produit_agent.py` (use_web_search=True) |
| Besoins vétérinaires | `app/api/BDD-Besoins/` (FEDIAF 2024, Merck, CHUV, NCSU) | `besoins_agent.py:22-24` |
| Profils lapins | `MOCK_LAPINS_DB` (dict) | `personnel_agent.py:11-44` |
| Règles cliniques | `BDD-Besoins/clinical_rules.json` | `comparateur_agent.py:41` |
| Grille de score | Intégrée dans le prompt du Comparateur | `comparateur_agent.py` (Source 5) |

## Modèles (entrées/sorties)

```
ScanRequest { barcode, rabbit_id? }

BesoinsSummary { sucre_max, fibres_min, calcium_min, calcium_max,
                 types_ideaux[], ingredients_interdits[], resume }
PersonnelSummary { id, nom, poids, age, allergies[], historique_medical[], resume }
ProduitSummary { barcode, nom, image_url, sucre, fibres, calcium,
                 ingredients[], a_cereales, ingredients_risques[], resume, sources[] }

Recommandation {
  nom_produit, image_produit, est_adapte, resume, conseil,
  alertes[], alternatives[],
  score: { total/100, grade(A-E), details: [{ nom, valeur, points/25, statut }] }
}
```

## Grille de score (Source 5 — CHUV 2025)

| Nutriment | Seuil | Pts max | Calcul |
|---|---|---|---|
| Fibres brutes | ≥ 18% | 25 | 0 si 0%, 25 si ≥ 18%, proportionnel |
| Protéines brutes | ≤ 16% | 25 | 25 si ≤ 16%, 0 si ≥ 30% |
| Matières grasses | ≤ 2.5% | 25 | 25 si ≤ 2.5%, 0 si ≥ 10% |
| Calcium | ≤ 1.0% | 25 | 25 si ≤ 1.0%, 0 si ≥ 2.5% |

**Pénalités** : céréales -15, sucre >8g -10, allergène -10, valeur manquante -5

**Grades** : A ≥90, B ≥75, C ≥60, D ≥40, E <40

## Quick start

```powershell
$env:GEMINI_API_KEY = 'ta_cle'
C:\Program Files\LibreOffice\program\python.exe -m uvicorn app.main:app --port 8080
```

## Endpoints

| Route | Méthode | Description |
|---|---|---|
| `/dashboard` | GET | Interface de debug interactive |
| `/debug-scan` | POST | Scan complet avec traces agent par agent |
| `/run-tests` | POST | Batterie de 5 tests sur vrais barcodes OFF |
