import sqlite3
from typing import List, Dict, Optional
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from datetime import datetime, timedelta

db = "shopping_assistant.sqlite"


from langchain_core.tools import tool
import sqlite3

db = "shopping_assistant.sqlite"

@tool
def recommend_cosmetics(skin_type: str, gender: str, max_price: float, category: str = None):
    """Рекомендует косметические товары с учетом типа кожи, пола, бюджета и категории."""
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    
    query = """
    SELECT product_name, brand, price_usd, category, skin_type
    FROM cosmetics 
    WHERE skin_type = ? AND gender_target = ? AND price_usd <= ?
    """
    params = [skin_type, gender, max_price]
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    query += " ORDER BY price_usd ASC LIMIT 3"
    cursor.execute(query, params)
    items = cursor.fetchall()
    
    conn.close()
    
    if not items:
        return {"error": "Нет подходящих косметических товаров"}
    
    return {
        "recommendations": [
            {"product_name": item[0], "brand": item[1], "price": item[2], "category": item[3], "skin_type": item[4]}
            for item in items
        ]
    }


# В файле tools.py модифицируйте инструмент:
@tool
def recommend_capsule_wardrobe(situation: str, gender: str, max_price: float) -> Dict:
    """Рекомендует капсульный гардероб с учетом пола, ситуации и бюджета."""
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        # Фильтрация для деловой встречи
        if situation.lower() == "деловая встреча":
            query = """
            SELECT title, price, description 
            FROM products 
            WHERE 
                (category = 'Business Clothing' OR 
                description LIKE '%formal%' OR 
                description LIKE '%business%' OR 
                description LIKE '%office%') AND
                price <= ?
            ORDER BY price ASC
            LIMIT 3
            """
            cursor.execute(query, (gender, max_price))
        else:
            return {"error": "Пока что поддерживаются только деловые встречи."}
        
        # Обработка результатов
        items = cursor.fetchall()
        if not items:
            return {"error": "Нет подходящих товаров для данной ситуации и бюджета."}
            
        return {
            "recommendations": [
                {
                    "title": item[0],
                    "price": item[1],
                    "description": item[2]
                } for item in items
            ],
            "total": sum(item[1] for item in items)
        }
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()
@tool
def recommend_style(situation: str) -> Dict:
    """Рекомендует капсульный гардероб для заданной ситуации с детальными объяснениями сочетания товаров."""
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        categories = ["Clothing", "Footwear", "Accessories"]
        recommendations = []
        
        for category in categories:
            query = """
            SELECT id, title, description, price, brand, category, situations 
            FROM products 
            WHERE situations LIKE ? AND category = ?
            LIMIT 1
            """
            cursor.execute(query, (f"%{situation}%", category))
            row = cursor.fetchone()
            if row:
                column_names = [desc[0] for desc in cursor.description]
                product = dict(zip(column_names, row))
                tags = product['situations'].split(', ')
                explanation = f"{product['title']} идеален для '{situation}', так как он помечен тегами: {', '.join(tags)}, а описание '{product['description']}' подчёркивает его уместность."
                product['explanation'] = explanation
                recommendations.append(product)
        
        if not recommendations:
            return {"message": f"Не найдено подходящих вещей для ситуации '{situation}'."}
        
        if len(recommendations) == 3:
            combination_explanation = f"Эти товары идеально подходят для '{situation}': "
            combination_explanation += f"{recommendations[0]['title']} (одежда) задаёт основу образа благодаря '{recommendations[0]['description']}', "
            combination_explanation += f"{recommendations[1]['title']} (обувь) гармонично дополняет его за счёт '{recommendations[1]['description']}', "
            combination_explanation += f"а {recommendations[2]['title']} (аксессуар) добавляет завершающий штрих благодаря '{recommendations[2]['description']}'."
        else:
            combination_explanation = f"Эти товары рекомендованы для '{situation}': "
            combination_explanation += " и ".join([f"{product['title']} ({product['category']}) с характеристикой '{product['description']}'" for product in recommendations]) + " вместе создают стильный образ."
        
    except Exception as e:
        return {"message": f"Произошла ошибка: {str(e)}"}
    finally:
        cursor.close()
        conn.close()
    
    return {
        "message": f"Капсульный гардероб для ситуации '{situation}':",
        "recommendations": recommendations,
        "combination_explanation": combination_explanation
    }

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