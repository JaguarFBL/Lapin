"""
Rabbit Scan — Version lite pour développeur
=============================================
Insère ton code-barres ci-dessous, lance le script, récupère la réponse JSON.

Usage:
    python scan.py

Sortie : JSON brut avec les 4 agents + recommandation finale
"""

import sys
import json
import os

# ── CONFIGURATION : insère ton code-barres ici ──────────────────────────
BARCODE = "3229820019307"   # Flocons d'avoine (fibres=11, sucre=1.7)
LAPIN_ID = "lapin_healthy"  # lapin_healthy | lapin_stones | lapin_allergic | lapin_young
# ─────────────────────────────────────────────────────────────────────────

# Le dossier hugo/ contient tout le nécessaire (app/ + données BDD-Besoins)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.debug import DebugScanner


async def main():
    print("[1/4] Agent Besoins...")
    import time; t0 = time.time()
    scanner = DebugScanner()
    result = await scanner.run(BARCODE, LAPIN_ID)
    print(f"[OK] Scan termine en {time.time()-t0:.0f}s")

    output = {
        "barcode": BARCODE,
        "lapin_id": LAPIN_ID,
        "recommandation": result.recommandation.model_dump(),
        "traces": [t.model_dump() for t in result.traces],
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))
    return result


if __name__ == "__main__":
    import asyncio

    # Évite les conflits d'event loop sous Windows + LibreOffice Python
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        loop.create_task(main())
    else:
        asyncio.run(main())
