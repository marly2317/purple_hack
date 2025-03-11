import sqlite3
from typing import List, Dict, Optional
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from datetime import datetime, timedelta

db = "shopping_assistant.sqlite"

@tool
def fetch_product_by_title(title: str) -> List[Dict]:
    """Fetches up to 10 products by title."""
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
    """Fetches up to 10 products by category."""
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
    """Fetches up to 10 products by brand."""
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
    """Fetches information on a limited number of available products."""
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        query = """
        SELECT id, title, description, price, discountPercentage, rating, brand, category, thumbnail 
        FROM products
        LIMIT ?
        """
        cursor.execute(query, (10,))
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
    """Fetches all unique product categories from the database."""
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
    """Fetch similar products based on content-based filtering (category and brand)."""
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
    """Adds an item to the user's cart and provides a confirmation message."""
    try:
        user_id = config.get("configurable", {}).get("thread_id", None)
        if not user_id:
            raise ValueError("No user_id configured.")
        
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        # Check if the product exists
        cursor.execute("SELECT id FROM products WHERE id = ?", (product_id,))
        product_result = cursor.fetchone()
        if not product_result:
            return {"message": "Product not found."}

        # Check if the item is already in the cart
        cursor.execute("SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
        result = cursor.fetchone()

        if result:
            # Update quantity if the item is already in the cart
            new_quantity = result[0] + quantity
            cursor.execute("UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?", (new_quantity, user_id, product_id))
            action = "updated"
        else:
            # Add new item to the cart
            cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, quantity))
            action = "added"

        conn.commit()

        # Fetch the updated cart for confirmation
        cursor.execute("SELECT product_id, quantity FROM cart WHERE user_id = ?", (user_id,))
        cart_items = cursor.fetchall()

    except Exception as e:
        return {"message": f"An error occurred: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

    return {
        "message": f"Item has been {action} in your cart.",
        "cart": [{"product_id": item[0], "quantity": item[1]} for item in cart_items]
    }


@tool
def remove_from_cart(config: RunnableConfig, product_id: int) -> Dict:
    """Removes an item from the user's cart and provides a final message."""
    try:
        configuration = config.get("configurable", {})
        user_id = configuration.get("thread_id", None)
        if not user_id:
            raise ValueError("No user_id configured.")
        
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        # Check if the item exists in the cart
        cursor.execute("SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
        result = cursor.fetchone()

        if not result:
            # If item not in cart, return a message
            return {"message": "Item not found in your cart."}

        # Remove the item from the cart
        cursor.execute("DELETE FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
        conn.commit()

        # Fetch the updated cart for confirmation
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
    """Provides a summary of items in the cart for the given user, including total price for checkout."""
    try:
        configuration = config.get("configurable", {})
        user_id = configuration.get("thread_id", None)
        if not user_id:
            raise ValueError("No user_id configured.")

        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        # Fetch cart items for the given user_id and join with products to get prices and titles
        cursor.execute("""
            SELECT p.id as product_id, p.title, p.price, c.quantity 
            FROM cart c 
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        """, (user_id,))
        cart_items = cursor.fetchall()

        # Calculate total price and format items for the response
        total_price = sum(item[2] * item[3] for item in cart_items)  # item[2] is price, item[3] is quantity
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
    """Provides a generic estimated delivery time for an order."""
    
    # Calculate an estimated delivery time, e.g., 5-7 business days from now
    estimated_delivery = datetime.now() + timedelta(days=5)
    
    return {
        "message": "Estimated delivery time:",
        "delivery_estimate": estimated_delivery.strftime('%Y-%m-%d')
    }
    

@tool
def get_payment_options() -> Dict:
    """Provides available payment options for the user."""
    
    # Static list of payment methods
    payment_methods = ["Credit Card", "Debit Card", "PayPal", "Gift Card"]
    
    return {
        "message": "Available payment options:",
        "payment_options": payment_methods
    }