from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

class ScanRequest(BaseModel):
    barcode: str
    rabbit_id: Optional[str] = None

class BesoinsRaw(BaseModel):
    sucre_max: float
    fibres_min: float
    calcium_min: float
    calcium_max: float
    types_ideaux: List[str]
    ingredients_interdits: List[str]

class BesoinsSummary(BaseModel):
    sucre_max: float
    fibres_min: float
    calcium_min: float
    calcium_max: float
    types_ideaux: List[str]
    ingredients_interdits: List[str]
    resume: str

class PersonnelRaw(BaseModel):
    id: str
    nom: str
    poids: float
    age: float
    allergies: List[str] = Field(default_factory=list)
    historique_medical: List[str] = Field(default_factory=list)

class PersonnelSummary(BaseModel):
    id: str
    nom: str
    poids: float
    age: float
    allergies: List[str]
    historique_medical: List[str]
    resume: str

class ProduitRaw(BaseModel):
    barcode: str
    nom: str
    image_url: str
    sucre: float
    fibres: float
    calcium: float
    ingredients: List[str] = Field(default_factory=list)

class ProduitSummary(BaseModel):
    barcode: str
    nom: str
    image_url: str
    sucre: float
    fibres: float
    calcium: float
    ingredients: List[str]
    a_cereales: bool
    ingredients_risques: List[str] = Field(default_factory=list)
    resume: str
    sources: List[str] = Field(default_factory=list, description="URLs des sources web consultées")

class Alternative(BaseModel):
    barcode: str
    nom: str
    raison: str

class NoteNutriment(BaseModel):
    """Note d'un nutriment individuel sur la grille CHUV 2025."""
    nom: str
    valeur_produit: float
    unite: str = "%"
    seuil_min: Optional[float] = None
    seuil_max: Optional[float] = None
    points: float  # 0 à 25
    statut: str  # ok | below_min | above_max | non_renseigne

class ScoreProduit(BaseModel):
    """Score global basé sur la grille d'évaluation CHUV 2025."""
    total: float = 0.0  # /100
    grade: str = ""     # A (≥90), B (≥75), C (≥60), D (≥40), E (<40)
    details: List[NoteNutriment] = Field(default_factory=list)

class Recommandation(BaseModel):
    nom_produit: str
    image_produit: str
    est_adapte: bool
    resume: str
    conseil: str
    alertes: List[str] = Field(default_factory=list)
    alternatives: List[Alternative] = Field(default_factory=list)
    score: Optional[ScoreProduit] = None
