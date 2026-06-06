from pathlib import Path
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ..models import ScanRequest
from ..debug import DebugScanner

logger = logging.getLogger("api.dashboard")

router = APIRouter()

HERE = Path(__file__).resolve().parent
HTML_FILE = HERE / "dashboard.html"


@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    logger.info("GET /dashboard")
    if not HTML_FILE.exists():
        return HTMLResponse("<h1>Dashboard introuvable</h1>", status_code=404)
    return HTMLResponse(HTML_FILE.read_text(encoding="utf-8"))


@router.post("/debug-scan")
async def debug_scan(request: ScanRequest):
    barcode = request.barcode
    lapin_id = request.rabbit_id or "lapin_healthy"
    logger.info("POST /debug-scan barcode=%s lapin_id=%s", barcode, lapin_id)
    scanner = DebugScanner()
    try:
        result = await scanner.run(barcode, lapin_id)
        logger.info("debug-scan OK: est_adapte=%s", result.recommandation.est_adapte)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("debug-scan ERREUR: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


class TestScenario(BaseModel):
    description: str
    barcode: str
    lapin_id: str
    attendu: bool


class TestResult(BaseModel):
    description: str
    barcode: str
    lapin_id: str
    attendu: bool
    est_adapte: bool
    nom_produit: str
    resume: str
    passe: bool


@router.post("/run-tests")
async def run_tests():
    logger.info("=== RUN TESTS (5 scénarios avec vrais barcodes OFF) ===")
    scenarios = [
        TestScenario(
            description="Panpan (sain) + Flocons d'avoine → fibre élevée, sucre bas, attendu adapté",
            barcode="3229820019307", lapin_id="lapin_healthy", attendu=True,
        ),
        TestScenario(
            description="Panpan (sain) + Cruesly noix → contient blé/avoine, sucre modéré",
            barcode="3168930010265", lapin_id="lapin_healthy", attendu=False,
        ),
        TestScenario(
            description="Cacahuète (allergique) + Flocons d'avoine → pas d'allergène déclaré",
            barcode="3229820019307", lapin_id="lapin_allergic", attendu=True,
        ),
        TestScenario(
            description="Junior (jeune) + Flocons d'avoine → aliment simple, sain",
            barcode="3229820019307", lapin_id="lapin_young", attendu=True,
        ),
        TestScenario(
            description="Gribouille (calculs) + Cruesly noix → calcium non renseigné sur OFF",
            barcode="3168930010265", lapin_id="lapin_stones", attendu=False,
        ),
    ]
    results = []
    for i, s in enumerate(scenarios, 1):
        logger.info("[Test %d/5] %s (barcode=%s)", i, s.description, s.barcode)
        scanner = DebugScanner()
        try:
            result = await scanner.run(s.barcode, s.lapin_id)
            tr = TestResult(
                description=s.description,
                barcode=s.barcode,
                lapin_id=s.lapin_id,
                attendu=s.attendu,
                est_adapte=result.recommandation.est_adapte,
                nom_produit=result.recommandation.nom_produit,
                resume=result.recommandation.resume,
                passe=result.recommandation.est_adapte == s.attendu,
            )
            logger.info("[Test %d] %s => est_adapte=%s attendu=%s %s",
                         i, tr.nom_produit, tr.est_adapte, tr.attendu, "OK" if tr.passe else "ÉCHEC")
        except Exception as exc:
            logger.error("[Test %d] ERREUR: %s", i, exc, exc_info=True)
            tr = TestResult(
                description=s.description,
                barcode=s.barcode,
                lapin_id=s.lapin_id,
                attendu=s.attendu,
                est_adapte=False,
                nom_produit="ERREUR",
                resume=str(exc),
                passe=False,
            )
        results.append(tr)

    total = len(results)
    reussis = sum(1 for r in results if r.passe)
    logger.info("=== TESTS TERMINÉS: %d/%d réussis ===", reussis, total)
    return {"total": total, "reussis": reussis, "echecs": total - reussis, "resultats": results}
