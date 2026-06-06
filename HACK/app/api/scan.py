import asyncio
from fastapi import APIRouter, HTTPException

from ..models import ScanRequest, Recommandation
from ..agents import BesoinsAgent, PersonnelAgent, ProduitAgent, ComparateurAgent

router = APIRouter()

@router.post("/scan", response_model=Recommandation)
async def scan_produit(request: ScanRequest) -> Recommandation:
    barcode = request.barcode
    lapin_id = request.rabbit_id or "lapin_healthy"

    besoins_agent = BesoinsAgent()
    personnel_agent = PersonnelAgent()
    produit_agent = ProduitAgent()
    comparateur = ComparateurAgent()

    try:
        besoins_task = besoins_agent.run()
        personnel_task = personnel_agent.run(lapin_id)
        produit_task = produit_agent.run(barcode)

        besoins, personnel, produit = await asyncio.gather(
            besoins_task, personnel_task, produit_task
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur : {str(exc)}")

    return await comparateur.comparer(besoins, personnel, produit)
