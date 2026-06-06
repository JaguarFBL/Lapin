# Interface API & Web (Routes)

Ce dossier gère toutes les routes et l'interface utilisateur (Dashboard) de l'application FastAPI.

## Fichiers

- `__init__.py` : Fichier de configuration qui agrège tous les routeurs (routers) pour les exposer à `main.py`.
- `health.py` : Route basique (`GET /`) pour vérifier que le serveur est bien en ligne. Utile pour les sondes (healthchecks).
- `scan.py` : Route de production (`POST /scan`). Elle exécute l'analyse de manière optimisée en lançant les 3 premiers agents (Besoins, Personnel, Produit) de manière **asynchrone et parallèle** via `asyncio.gather`, avant de passer le relais au Comparateur. Retourne uniquement le verdict JSON.
- `dashboard.py` : Route de débogage et d'administration. 
  - Expose l'interface web (`GET /dashboard`).
  - Gère l'analyse détaillée étape par étape (`POST /debug-scan`) en utilisant la classe `DebugScanner`.
  - Gère les tests automatisés intégrés à l'interface web (`POST /run-tests`).
- `dashboard.html` : Interface web "frontend" du projet (Single Page Application) permettant d'interagir avec les endpoints de debug et de visualiser le comportement interne de l'IA (prompts/réponses).
- `BDD-Besoins/` (Dossier) : Contient la véritable base de connaissances vétérinaires sous forme de fichiers bruts (CSV, JSON) requêtés dynamiquement par l'IA.
