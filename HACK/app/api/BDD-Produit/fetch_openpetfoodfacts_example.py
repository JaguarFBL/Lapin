import requests

USER_AGENT = "AppLapin/0.1 (contact@example.com)"

SOURCES = [
    "https://world.openpetfoodfacts.org/api/v2/product/{barcode}.json",
    "https://world.openfoodfacts.org/api/v2/product/{barcode}.json?product_type=all",
]

def fetch_product_by_barcode(barcode: str) -> dict | None:
    headers = {"User-Agent": USER_AGENT}
    for template in SOURCES:
        url = template.format(barcode=barcode)
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 404:
            continue
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") == 1 and payload.get("product"):
            payload["_source_url"] = url
            return payload
    return None

def extract_basic_product(payload: dict) -> dict:
    product = payload.get("product", {})
    return {
        "barcode": product.get("code") or payload.get("code"),
        "brand": product.get("brands"),
        "name": product.get("product_name") or product.get("product_name_fr") or product.get("product_name_en"),
        "categories": product.get("categories_tags", []),
        "ingredients_text": product.get("ingredients_text") or product.get("ingredients_text_fr") or product.get("ingredients_text_en"),
        "nutriments": product.get("nutriments", {}),
        "image_front_url": product.get("image_front_url"),
        "image_ingredients_url": product.get("image_ingredients_url"),
        "image_nutrition_url": product.get("image_nutrition_url"),
        "raw_payload": product,
    }

if __name__ == "__main__":
    test_barcode = "YOUR_BARCODE_HERE"
    result = fetch_product_by_barcode(test_barcode)
    print(extract_basic_product(result) if result else "not_found")
