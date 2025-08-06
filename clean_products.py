#!/usr/bin/env python3
"""
Script for cleaning product data - extract product_id from URLs and add review statistics
"""

import json
import re
from datetime import datetime
from collections import defaultdict


def extract_product_id(product_url):
    """
    Extrae el product_id de la URL de Canadian Tire
    Ejemplo: https://www.canadiantire.ca/en/pdp/supercycle-reaction-hardtail-mountain-bike-for-all-ages-26-in-black-0710110p.html
    Resultado: 0710110p
    """
    if not product_url:
        return None

    # Buscar el patrón de números seguidos de 'p' antes de '.html'
    pattern = r'(\d+p)\.html'
    match = re.search(pattern, product_url)

    if match:
        return match.group(1)

    return None


def extract_brand_from_title(title):
    """
    Extrae la marca del título del producto
    """
    if not title:
        return "Unknown"

    # Lista de marcas conocidas
    brands = ["Supercycle", "Raleigh", "Stratus", "Marvel", "Hot Wheels"]

    for brand in brands:
        if brand.lower() in title.lower():
            return brand

    return "Unknown"


def clean_price(price_str):
    """
    Limpia el string de precio para extraer el precio actual
    """
    if not price_str:
        return None

    # Si hay múltiples precios (precio actual y precio anterior)
    lines = price_str.split('\n')
    first_line = lines[0].strip()

    # Extraer solo el primer precio usando regex
    price_match = re.search(r'\$(\d+(?:\.\d{2})?)', first_line)
    if price_match:
        return float(price_match.group(1))

    return None


def extract_category_from_title(title):
    """
    Extrae la categoría basada en el título
    """
    if not title:
        return "general"

    title_lower = title.lower()

    if any(word in title_lower for word in ["kids'", "children", "youth"]):
        return "kids_bikes"
    elif any(word in title_lower for word in ["mountain", "dual-suspension", "hardtail"]):
        return "mountain_bikes"
    elif any(word in title_lower for word in ["comfort", "cruiser", "women's"]):
        return "comfort_bikes"
    elif any(word in title_lower for word in ["road", "hybrid"]):
        return "road_bikes"
    else:
        return "bikes"


def extract_discount_info(raw_price):
    """
    Extrae información de descuento del string de precio
    """
    discount_info = {
        'discount_percentage': None,
        'discount_amount': None,
        'original_price': None,
        'ends_date': None,
        'has_discount': False
    }

    if not raw_price:
        return discount_info

    # Buscar patrón de descuento: "Save 29% ($80.00)"
    save_match = re.search(r'Save\s+(\d+)%\s+\(\$?([\d,]+\.?\d*)\)', raw_price)
    if save_match:
        discount_info['has_discount'] = True
        discount_info['discount_percentage'] = int(save_match.group(1))
        discount_info['discount_amount'] = float(
            save_match.group(2).replace(',', ''))

    # Buscar precio original: "price was $279.99"
    price_was_match = re.search(r'price was \$?([\d,]+\.?\d*)', raw_price)
    if price_was_match:
        discount_info['has_discount'] = True
        discount_info['original_price'] = float(
            price_was_match.group(1).replace(',', ''))

    # Buscar fecha de fin: "Ends August 07, 2025"
    ends_match = re.search(r'Ends\s+([^\n]+)', raw_price)
    if ends_match:
        discount_info['ends_date'] = ends_match.group(1).strip()

    return discount_info


def load_product_ratings_summary(filename="product_ratings_summary.json"):
    """
    Load product ratings summary from the file created by review scraper
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ {filename} not found. Rating data will be set to null.")
        return {}
    except json.JSONDecodeError:
        print(f"❌ Error parsing {filename}")
        return {}


def extract_rating_info_for_product(product_url, ratings_data):
    """
    Extract rating information for a specific product using its URL
    """
    rating_info = {
        'average_rating': None,
        'total_reviews': None,
        'has_rating_data': False
    }

    if product_url in ratings_data:
        product_rating = ratings_data[product_url]
        rating_info['average_rating'] = product_rating.get('average_rating')
        rating_info['total_reviews'] = product_rating.get('total_reviews')
        rating_info['has_rating_data'] = True

    return rating_info


def clean_products_json():
    """
    Función principal para limpiar el JSON de productos
    """
    print("🧹 Starting product JSON cleaning process...")

    # Cargar el JSON original
    try:
        with open("productos_scraped_v0.json", "r", encoding="utf-8") as f:
            products = json.load(f)
        print(
            f"✅ Loaded {len(products)} products from productos_scraped_v0.json")
    except FileNotFoundError:
        print("❌ productos_scraped_v0.json not found")
        return
    except json.JSONDecodeError:
        print("❌ Error parsing JSON file")
        return

    # Load product ratings summary
    ratings_data = load_product_ratings_summary()
    print(f"✅ Loaded rating data for {len(ratings_data)} products")

    # Procesar cada producto
    cleaned_products = []
    success_count = 0
    error_count = 0

    print("\n🔄 Processing products...")

    for i, product in enumerate(products):
        try:
            # Extraer product_id de la URL
            product_id = extract_product_id(product.get('product_url', ''))

            if not product_id:
                print(
                    f"⚠️  Product {i+1}: Could not extract product_id from URL: {product.get('product_url', '')}")
                error_count += 1
                continue

            # Extraer información de descuento
            discount_info = extract_discount_info(product.get('price', ''))

            # Extract rating information
            rating_info = extract_rating_info_for_product(
                product.get('product_url', ''), ratings_data)

            # Crear producto limpio
            cleaned_product = {
                "product_id": product_id,
                "title": product.get('title', '').strip(),
                "brand": extract_brand_from_title(product.get('title', '')),
                "category": extract_category_from_title(product.get('title', '')),
                "product_url": product.get('product_url', ''),
                "price": clean_price(product.get('price', '')),
                "raw_price": product.get('price', ''),
                "discount": discount_info if discount_info['has_discount'] else None,
                "average_rating": rating_info['average_rating'],
                "total_reviews": rating_info['total_reviews'],
                "description": product.get('description', '').strip(),
                "sku": product.get('sku', '').strip(),
                "search_url": product.get('search_url', ''),
                "detailed_title": product.get('detailed_title', '').strip(),
                "detailed_price": product.get('detailed_price', ''),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            cleaned_products.append(cleaned_product)
            success_count += 1

            # Mostrar progreso cada 5 productos
            if (i + 1) % 5 == 0:
                print(f"   Processed {i + 1}/{len(products)} products...")

        except Exception as e:
            print(f"❌ Error processing product {i+1}: {e}")
            error_count += 1
            continue

    # Guardar el JSON limpio
    try:
        with open("productos_cleaned.json", "w", encoding="utf-8") as f:
            json.dump(cleaned_products, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Cleaned products saved to productos_cleaned.json")
    except Exception as e:
        print(f"❌ Error saving cleaned products: {e}")
        return

    # Estadísticas finales
    print(f"\n📊 CLEANING SUMMARY:")
    print(f"   Total products processed: {len(products)}")
    print(f"   Successfully cleaned: {success_count}")
    print(f"   Errors: {error_count}")
    print(f"   Success rate: {(success_count/len(products)*100):.1f}%")

    # Mostrar ejemplos de product_ids extraídos
    print(f"\n🔍 SAMPLE PRODUCT IDs EXTRACTED:")
    for i, product in enumerate(cleaned_products[:5]):
        print(f"   {i+1}. {product['title'][:50]}...")
        print(f"      Product ID: {product['product_id']}")
        print(f"      Brand: {product['brand']}")
        print(f"      Category: {product['category']}")
        print(f"      Price: ${product['price']}")
        if product.get('discount'):
            discount = product['discount']
            print(
                f"      Discount: {discount.get('discount_percentage', 'N/A')}% (${discount.get('discount_amount', 'N/A')})")
            if discount.get('original_price'):
                print(f"      Original Price: ${discount['original_price']}")
        else:
            print(f"      Discount: None")
        # Show rating information
        if product.get('average_rating') is not None:
            print(
                f"      Rating: {product['average_rating']} stars ({product.get('total_reviews', 0)} reviews)")
        else:
            print(f"      Rating: No rating data available")
        print()

    # Verificar duplicados
    product_ids = [p['product_id'] for p in cleaned_products]
    unique_ids = set(product_ids)

    if len(product_ids) != len(unique_ids):
        duplicates = len(product_ids) - len(unique_ids)
        print(f"⚠️  WARNING: Found {duplicates} duplicate product_ids")
    else:
        print(f"✅ All product_ids are unique")


def show_extraction_examples():
    """
    Muestra ejemplos de extracción de product_id para verificar el patrón
    """
    print("\n🔍 TESTING PRODUCT_ID EXTRACTION:")

    test_urls = [
        "https://www.canadiantire.ca/en/pdp/supercycle-reaction-hardtail-mountain-bike-for-all-ages-26-in-black-0710110p.html?rq=bikes",
        "https://www.canadiantire.ca/en/pdp/raleigh-cafe-comfort-bike-26-in-wheel-silver-0711959p.html?rq=bikes",
        "https://www.canadiantire.ca/en/pdp/supercycle-nitrous-dual-suspension-bike-24-in-wheel-black-purple-0711906p.html?rq=bikes"
    ]

    for url in test_urls:
        product_id = extract_product_id(url)
        print(f"   URL: {url}")
        print(f"   Extracted ID: {product_id}")
        print()


if __name__ == "__main__":
    # Mostrar ejemplos primero
    show_extraction_examples()

    # Ejecutar limpieza
    clean_products_json()

    print("\n🎉 Product cleaning complete!")
