import sqlite3
from typing import List, Dict, Optional
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from datetime import datetime, timedelta

db = "shopping_assistant.sqlite"

# @tool
# def recommend_cosmetics(skin_type: str, gender: str, max_price: float, category: str = None):
#     """Рекомендует косметические товары с учетом типа кожи, пола, бюджета и категории."""
#     conn = sqlite3.connect(db)
#     cursor = conn.cursor()
    
#     query = """
#     SELECT product_name, brand, price_usd, category, skin_type
#     FROM cosmetics 
#     WHERE skin_type = ? AND gender_target = ? AND price_usd <= ?
#     """
#     params = [skin_type, gender, max_price]
    
#     if category:
#         query += " AND category = ?"
#         params.append(category)
    
#     query += " ORDER BY price_usd ASC LIMIT 3"
#     cursor.execute(query, params)
#     items = cursor.fetchall()
    
#     conn.close()
    
#     if not items:
#         return {"error": "Нет подходящих косметических товаров"}
    
#     return {
#         "recommendations": [
#             {"product_name": item[0], "brand": item[1], "price": item[2], "category": item[3], "skin_type": item[4]}
#             for item in items
#         ]
#     }


# В файле tools.py модифицируйте инструмент:

@tool
def recommend_capsule_wardrobe(situation: str, gender: str, max_price: float) -> Dict:
    """Рекомендует капсульный гардероб с учетом ситуации, пола и бюджета"""
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        # Определяем целевую категорию
        category_map = {
            "male": "Men's Clothing",
            "female": "Women's Clothing"
        }
        target_category = category_map.get(gender.lower(), "Clothing")

        query = """
        SELECT 
            id, title, description, price, brand, category, thumbnail
        FROM products 
        WHERE 
            category LIKE ? AND 
            price <= ? AND
            (description LIKE '%formal%' OR description LIKE '%business%')
        ORDER BY rating DESC
        LIMIT 5
        """
        
        # Параметры в правильном порядке: 1) категория, 2) цена
        cursor.execute(query, (f"%{target_category}%", max_price))
        
        items = cursor.fetchall()
        if not items:
            return {"error": "Нет подходящих вариантов в данном ценовом диапазоне"}

        return {
            "recommendations": [
                {
                    "title": item[1],
                    "price": item[3],
                    "brand": item[4],
                    "category": item[5],
                    "image": item[6]
                } for item in items
            ],
            "total_price": sum(item[3] for item in items)
        }

    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@tool
def recommend_style(situation: str) -> Dict:
    """Рекомендует капсульный гардероб на основе анализа описания и атрибутов"""
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        # Ключевые слова для ситуаций
        situation_keywords = {
            "деловая встреча": ["formal", "office", "business", "suit", "blazer", "wool", "cotton"],
            "повседневный стиль": ["casual", "comfort", "everyday", "relaxed"],
            "вечерний выход": ["party", "evening", "chic", "silk"]
        }

        keywords = situation_keywords.get(situation.lower(), [])
        if not keywords:
            return {"error": f"Неизвестная ситуация: {situation}"}

        # Поиск по описанию и атрибутам
        query = """
        SELECT 
            id, title, description, price, brand, category,
            product_details
        FROM products
        WHERE 
            (LOWER(description) REGEXP ? OR
            LOWER(product_details) REGEXP ?) AND
            category IN ('Clothing', 'Footwear', 'Accessories')
        LIMIT 3
        """
        
        pattern = "|".join(keywords)
        cursor.execute(query, (f".*({pattern}).*", f".*({pattern}).*"))
        
        recommendations = []
        for row in cursor.fetchall():
            product = {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "price": row[3],
                "brand": row[4],
                "category": row[5],
                "details": json.loads(row[6]) if row[6] else []
            }
            
            # Формирование объяснения
            explanation = f"{product['title']} подходит для {situation}: "
            matches = []
            
            if any(kw in product['description'].lower() for kw in keywords):
                matches.append("описание содержит ключевые слова")
                
            if any(any(kw in f"{k}:{v}".lower() for kw in keywords) 
                   for d in product['details'] for k, v in d.items()):
                matches.append("атрибуты соответствуют требованиям")
                
            explanation += " и ".join(matches)
            product['explanation'] = explanation
            recommendations.append(product)

        if not recommendations:
            return {"message": f"Не найдено рекомендаций для {situation}"}

        return {
            "message": f"Рекомендации для {situation}:",
            "recommendations": recommendations
        }

    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


@tool
def fetch_product_by_title(title: str) -> List[Dict]:
    """Ищет товары по названию и возвращает до 10 результатов."""
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        query = """
        SELECT id, title, description, price, discountPercentage, rating, brand, category, thumbnail 
        FROM products
        WHERE title LIKE ? LIMIT 10
        """
        
        cursor.execute(query, (f"%{title}%",))
        rows = cursor.fetchall()

        if not rows:
            return [{"message": "No products found with the specified title."}]
        
        column_names = [desc[0] for desc in cursor.description]
        results = [dict(zip(column_names, row)) for row in rows]
        
    except Exception as e:
        return [{"message": f"An error occurred: {str(e)}"}]
    finally:
        cursor.close()
        conn.close()
    
    return results

@tool
def fetch_product_by_category(category: str) -> List[Dict]:
    """Ищет товары по категории и возвращает до 10 результатов."""
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        query = """
        SELECT id, title, description, price, discountPercentage, rating, brand, category, thumbnail 
        FROM products
        WHERE category = ? LIMIT 10
        """
        
        cursor.execute(query, (category,))
        rows = cursor.fetchall()

        if not rows:
            return [{"message": "No products found in the specified category."}]
        
        column_names = [desc[0] for desc in cursor.description]
        results = [dict(zip(column_names, row)) for row in rows]

    except Exception as e:
        return [{"message": f"An error occurred: {str(e)}"}]
    finally:
        cursor.close()
        conn.close()
    
    return results

@tool
def fetch_product_by_brand(brand: str) -> List[Dict]:
    """Ищет товары по бренду и возвращает до 10 результатов."""
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        query = """
        SELECT id, title, description, price, discountPercentage, rating, brand, category, thumbnail 
        FROM products
        WHERE brand = ? LIMIT 10
        """
        
        cursor.execute(query, (brand,))
        rows = cursor.fetchall()

        if not rows:
            return [{"message": "No products found for the specified brand."}]
        
        column_names = [desc[0] for desc in cursor.description]
        results = [dict(zip(column_names, row)) for row in rows]

    except Exception as e:
        return [{"message": f"An error occurred: {str(e)}"}]
    finally:
        cursor.close()
        conn.close()
    
    return results

@tool
def initialize_fetch() -> List[Dict]:
    """Инициализирует загрузку и возвращает информацию о 10 доступных товарах."""
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        query = """
        SELECT id, title, description, price, discountPercentage, rating, brand, category, thumbnail 
        FROM products
        LIMIT 10
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        all_products = [dict(zip(column_names, row)) for row in rows]

    except Exception as e:
        return [{"message": f"An error occurred: {str(e)}"}]
    finally:
        cursor.close()
        conn.close()

    return all_products

@tool
def fetch_all_categories() -> List[str]:
    """Возвращает все уникальные категории товаров из базы данных."""
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        query = "SELECT DISTINCT category FROM products ORDER BY category"
        cursor.execute(query)
        rows = cursor.fetchall()
        categories = [row[0] for row in rows]

    except Exception as e:
        return [{"message": f"An error occurred: {str(e)}"}]
    finally:
        cursor.close()
        conn.close()

    return categories

@tool
def fetch_recommendations(product_id: int) -> List[Dict]:
    """Возвращает похожие товары на основе категории и бренда."""
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        cursor.execute("SELECT category, brand FROM products WHERE id = ?", (product_id,))
        result = cursor.fetchone()
        if not result:
            return [{"message": "Product not found."}]
        category, brand = result

        query = """
        SELECT id, title, description, price, discountPercentage, rating, brand, category, thumbnail 
        FROM products
        WHERE (category = ? OR brand = ?) AND id != ?
        LIMIT 5
        """
        cursor.execute(query, (category, brand, product_id))
        rows = cursor.fetchall()

        if not rows:
            return [{"message": "No related products found."}]
        
        column_names = [desc[0] for desc in cursor.description]
        recommendations = [dict(zip(column_names, row)) for row in rows]

    except Exception as e:
        return [{"message": f"An error occurred: {str(e)}"}]
    finally:
        cursor.close()
        conn.close()

    return recommendations

@tool
def add_to_cart(config: RunnableConfig, product_id: int, quantity: int = 1) -> Dict:
    """Добавляет товар в корзину пользователя и возвращает подтверждение."""
    try:
        user_id = config.get("configurable", {}).get("thread_id", None)
        if not user_id:
            raise ValueError("Не указан user_id.")
        
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        cursor.execute("SELECT id, stock FROM products WHERE id = ?", (product_id,))
        product_result = cursor.fetchone()
        if not product_result:
            return {"message": "Товар не найден."}
        
        stock = product_result[1]
        if stock < quantity:
            return {"message": f"Недостаточно товара на складе. Доступно только {stock} единиц."}

        cursor.execute("SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
        result = cursor.fetchone()

        if result:
            new_quantity = result[0] + quantity
            if stock < new_quantity:
                return {"message": f"Недостаточно товара на складе. Доступно только {stock} единиц."}
            cursor.execute("UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?", (new_quantity, user_id, product_id))
            action = "обновлен"
        else:
            cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, quantity))
            action = "добавлен"

        new_stock = stock - quantity
        cursor.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))

        conn.commit()

        cursor.execute("SELECT product_id, quantity FROM cart WHERE user_id = ?", (user_id,))
        cart_items = cursor.fetchall()

    except Exception as e:
        return {"message": f"Произошла ошибка: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

    return {
        "message": f"Товар {action} в вашей корзине.",
        "cart": [{"product_id": item[0], "quantity": item[1]} for item in cart_items]
    }

@tool
def remove_from_cart(config: RunnableConfig, product_id: int) -> Dict:
    """Удаляет товар из корзины пользователя и возвращает подтверждение."""
    try:
        configuration = config.get("configurable", {})
        user_id = configuration.get("thread_id", None)
        if not user_id:
            raise ValueError("No user_id configured.")
        
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        cursor.execute("SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
        result = cursor.fetchone()

        if not result:
            return {"message": "Item not found in your cart."}

        cursor.execute("DELETE FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
        conn.commit()

        cursor.execute("SELECT product_id, quantity FROM cart WHERE user_id = ?", (user_id,))
        cart_items = cursor.fetchall()

    except Exception as e:
        return {"message": f"An error occurred: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

    return {
        "message": "Item has been removed from your cart."
    }

@tool
def view_checkout_info(config: RunnableConfig) -> Dict:
    """Возвращает сводку о товарах в корзине пользователя, включая общую стоимость."""
    try:
        configuration = config.get("configurable", {})
        user_id = configuration.get("thread_id", None)
        if not user_id:
            raise ValueError("No user_id configured.")

        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.id as product_id, p.title, p.price, c.quantity 
            FROM cart c 
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        """, (user_id,))
        cart_items = cursor.fetchall()

        total_price = sum(item[2] * item[3] for item in cart_items)
        items = [{"product_id": item[0], "title": item[1], "price": item[2], "quantity": item[3]} for item in cart_items]

    except Exception as e:
        return {"message": f"An error occurred: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

    return {
        "message": "Checkout summary:",
        "total_price": total_price,
        "items": items
    }

@tool
def get_delivery_estimate() -> Dict:
    """Возвращает предполагаемое время доставки для заказа."""
    estimated_delivery = datetime.now() + timedelta(days=5)
    return {
        "message": "Estimated delivery time:",
        "delivery_estimate": estimated_delivery.strftime('%Y-%m-%d')
    }

@tool
def get_payment_options() -> Dict:
    """Возвращает доступные способы оплаты для пользователя."""
    payment_methods = ["Credit Card", "Debit Card", "PayPal", "Gift Card"]
    return {
        "message": "Available payment options:",
        "payment_options": payment_methods
    }