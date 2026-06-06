"""
Base de données des besoins idéaux pour le lapin domestique.
"""
from typing import Dict, Any

BESOINS_IDEAL: Dict[str, Any] = {
    "sucre": {
        "max": 8.0,
        "ideal": 4.0,
        "critical": 15.0,
        "description": "Les lapins ont un système digestif sensible aux sucres. Un taux bas est essentiel.",
    },
    "fibres": {
        "min": 15.0,
        "ideal": 20.0,
        "critical": 10.0,
        "description": "Les fibres longues sont indispensables au transit et à l'usure des dents.",
    },
    "calcium": {
        "min": 100.0,
        "max": 500.0,
        "critical": 600.0,
        "description": "Le calcium est vital mais son excès cause des calculs urinaires.",
    },
    "types_ideaux": ["hay_based", "pellets_herbes"],
    "categories_interdites": ["céréales", "graines", "sous-produits animaux", "sucre ajouté"],
    "cereales_keywords": ["blé", "maïs", "avoine", "orge", "amidon", "céréale", "bléd"],
    "sucres_keywords": ["miel", "sirop", "mélasse", "sucre", "fructose", "glucose"],
}
