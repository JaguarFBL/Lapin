# Agents IA (Team Rabbit Scan)

Ce dossier regroupe la logique des agents "métier". Chaque agent a un rôle strict et opère comme un module indépendant capable de raisonner grâce à Gemini.

## Les Agents

1. **`besoins_agent.py` (Team Besoins)**
   - **Rôle :** Analyser les bases de données vétérinaires brutes (CSV, JSON) et en extraire les règles universelles (seuils nutritionnels idéaux).
   - **Source :** Dossier `api/BDD-Besoins/`.
   - **Modèle :** Rapide (`gemini-3-flash-preview`).

2. **`personnel_agent.py` (Team Personnel)**
   - **Rôle :** Comprendre le profil spécifique du lapin scanné (âge, poids, historique médical, allergies).
   - **Source :** Actuellement un dictionnaire mocké (`MOCK_LAPINS_DB`), destiné à être remplacé par `animal_profiles.csv`.
   - **Modèle :** Rapide (`gemini-3-flash-preview`).

3. **`produit_agent.py` (Team Produit)**
   - **Rôle :** Analyser l'aliment scanné (ingrédients, taux de sucre/fibres/calcium) et repérer les risques immédiats (céréales, etc.).
   - **Source :** Actuellement un mock (`MOCK_PRODUITS_DB`), simulant un appel OpenFoodFacts.
   - **Modèle :** Rapide (`gemini-3-flash-preview`).

4. **`comparateur_agent.py` (Team Comparateur)**
   - **Rôle :** Le "Juge". Il reçoit les résumés des 3 agents précédents + le fichier de règles cliniques (`clinical_rules.json`), croise toutes les informations, calcule les seuils personnalisés, et rend son verdict final (adapté ou non) avec conseils et alternatives.
   - **Modèle :** Avancé (`gemini-3.1-pro-preview`) pour un raisonnement fiable et sans faille.
