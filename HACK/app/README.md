# Application Rabbit Scan (Backend)

Ce dossier contient le cœur de l'application Rabbit Scan.

## Structure
- `main.py` : Point d'entrée de l'application FastAPI. Il configure le serveur, les logs et inclut les routes.
- `models.py` : Définition des modèles de données (Pydantic) utilisés pour la validation des requêtes et des réponses (requêtes de scan, résumés des agents, recommandation finale).
- `database.py` : Historiquement utilisé pour stocker les règles en dur. En cours d'obsolescence au profit de la base `BDD-Besoins`.
- `ai.py` : Client générique (Wrapper) pour l'API Google Gemini (`google-genai`). Gère l'authentification, les appels et le parsing sécurisé du JSON renvoyé par l'IA.
- `debug.py` : Moteur d'orchestration conçu spécifiquement pour le Dashboard. Il exécute les agents un par un et capture méticuleusement chaque étape (entrées/sorties, prompts, réponses IA) pour rendre le raisonnement de l'IA totalement transparent.

## Architecture
Le système est basé sur un fonctionnement Multi-Agents asynchrone orchestré par les routes définies dans le dossier `api/`. Les agents métier se trouvent dans `agents/`.
