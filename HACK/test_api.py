from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test(barcode: str, lapin_id: str, attendu: bool, description: str):
    print(f"\n{'='*50}")
    print(f"TEST : {description}")
    print(f"{'='*50}")
    resp = client.post("/scan", json={"barcode": barcode, "rabbit_id": lapin_id})
    data = resp.json()
    print(f"Produit : {data['nom_produit']}")
    print(f"Adapte   : {data['est_adapte']}")
    print(f"Resume   : {data['resume']}")
    print(f"Conseil  : {data['conseil']}")
    if data['alertes']:
        for a in data['alertes']:
            print(f"  ! {a}")
    if data['alternatives']:
        for alt in data['alternatives']:
            print(f"  -> {alt['nom']} : {alt['raison']}")
    assert data['est_adapte'] == attendu, f"ECHEC: attendu {attendu}, recu {data['est_adapte']}"
    print("RESULTAT : OK")
    return data

if __name__ == "__main__":
    # 1. Lapin sain + Foin Timothy -> adapte
    test("301123", "lapin_healthy", True, "Panpan (sain) + Foin Timothy -> adapte")

    # 2. Lapin calculs + Luzerne -> deconseille (calcium)
    test("301124", "lapin_stones", False, "Gribouille (calculs) + Luzerne -> calcium trop eleve")

    # 3. Lapin allergique + Friandises carotte -> interdit
    test("301126", "lapin_allergic", False, "Cacahuete (allergique) + Friandises carotte -> interdit")

    # 4. Jeune lapin + Luzerne -> adapte (besoin calcium)
    test("301124", "lapin_young", True, "Junior (jeune) + Luzerne -> calcium utile, adapte")

    # 5. Melange cereales + lapin sain -> deconseille
    test("301125", "lapin_healthy", False, "Panpan (sain) + Cereales -> deconseille")

    # 6. Friandises + lapin sain -> deconseille (sucre critique)
    test("301126", "lapin_healthy", False, "Panpan (sain) + Friandises -> sucre critique")

    # 7. Foin + lapin calculs -> adapte (alternative)
    test("301123", "lapin_stones", True, "Gribouille (calculs) + Foin Timothy -> calcium bas, adapte")

    print(f"\n{'='*50}")
    print("TOUS LES TESTS PASSENT")
