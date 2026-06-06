# Hugo — Version lite Rabbit Scan

Outil développeur pour tester le pipeline complet sans lancer le serveur.

## Utilisation

1. Ouvre `scan.py`
2. Change `BARCODE` et `LAPIN_ID` en haut du fichier (lignes 12-13)
3. Lance :

```powershell
$env:GEMINI_API_KEY = 'ta_cle'
C:\Program Files\LibreOffice\program\python.exe scan.py
```

4. Récupère la réponse JSON dans stdout

## Variables disponibles

### Lapins (LAPIN_ID)

| ID | Nom | Profil |
|---|---|---|
| `lapin_healthy` | Panpan | Adulte sain |
| `lapin_stones` | Gribouille | Calculs urinaires |
| `lapin_allergic` | Cacahuète | Allergique carotte |
| `lapin_young` | Junior | Jeune en croissance |

### Barcodes OFF qui marchent

| Code | Produit |
|---|---|
| `3229820019307` | Flocons d'avoine (fibres=11, sucre=1.7) |
| `3168930010265` | Cruesly noix (fibres=10, sucre=12) |
| `5015622204403` | Selective Lapin (trouvé via web search) |

## Sortie JSON

```json
{
  "barcode": "3229820019307",
  "lapin_id": "lapin_healthy",
  "recommandation": {
    "nom_produit": "...",
    "est_adapte": true/false,
    "resume": "...",
    "conseil": "...",
    "alertes": [...],
    "alternatives": [...]
  },
  "traces": [
    { "agent": "Besoins", "etape": "...", "entree": ..., "sortie": ... },
    ...
  ]
}
```
