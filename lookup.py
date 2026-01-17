import requests

def get_nutrition(upc):
    url = f"https://world.openfoodfacts.org/api/v0/product/{upc}.json"
    response = requests.get(url)

    if response.status_code != 200:
        print("Failed to fetch data")
        return

    data = response.json()

    if data.get("status") != 1:
        print("Product not found")
        return

    product = data["product"]

    print("\n--- PRODUCT INFO ---")
    print("Name:", product.get("product_name"))
    print("Brand:", product.get("brands"))
    print("Serving Size:", product.get("serving_size"))

    nutriments = product.get("nutriments", {})

    print("\n--- NUTRITION (per 100g) ---")
    print("Calories:", nutriments.get("energy-kcal_100g"))
    print("Fat:", nutriments.get("fat_100g"))
    print("Carbs:", nutriments.get("carbohydrates_100g"))
    print("Protein:", nutriments.get("proteins_100g"))
    print("Sugar:", nutriments.get("sugars_100g"))
    print("Sodium:", nutriments.get("sodium_100g"))

if __name__ == "__main__":
    upc = input("Enter UPC barcode: ")
    get_nutrition(upc)
