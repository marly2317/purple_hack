import sqlite3
from typing import List, Dict, Optional
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from datetime import datetime, timedelta


@tool
def fetch_product_info(title: Optional[str] = None, category: Optional[str] = None) -> List[Dict]:
    """Fetches product details based on title, category, and price range filters."""
    
    if title == "":
        title = None
    if category == "":
        category = None

    # Return an empty list if no filters are provided
    if not title and not category:
        return []
    
    db = "shopping_assistant.sqlite"
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Base query
    query = """
    SELECT id, title, description, price, discountPercentage, rating, stock, brand, category, thumbnail 
    FROM products
    """
    params = []
    filters = []

    # Add filters only if provided
    if title:
        filters.append("title LIKE ?")
        params.append(f"%{title}%")
    if category:
        filters.append("category = ?")
        params.append(category)

    # Append WHERE clause only if filters are present
    if filters:
        query += " WHERE " + " AND ".join(filters)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    
    # Format results as a list of dictionaries
    results = [dict(zip(column_names, row)) for row in rows]

    cursor.close()
    conn.close()

    return results


@tool
def fetch_recommendations(product_id: int) -> List[Dict]:
    """Fetch similar products based on content-based filtering (category and brand)."""
    
    db = "shopping_assistant.sqlite"
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Get the category and brand of the current product
    cursor.execute("SELECT category, brand FROM products WHERE id = ?", (product_id,))
    result = cursor.fetchone()
    if not result:
        # If the product doesn't exist, return an empty list
        return []
    category, brand = result

    # Query for similar products in the same category and brand, excluding the current product
    query = """
    SELECT id, title, description, price, discountPercentage, rating, stock, brand, category, thumbnail 
    FROM products
    WHERE (category = ? OR brand = ?) AND id != ?
    LIMIT 5
    """
    cursor.execute(query, (category, brand, product_id))
    rows = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]

    # Format results as a list of dictionaries
    recommendations = [dict(zip(column_names, row)) for row in rows]

    cursor.close()
    conn.close()

    return recommendations


@tool
def add_to_cart(config: RunnableConfig, product_id: int, quantity: int = 1) -> Dict:
    """Adds an item to the user's cart, asks for confirmation, and provides a final message."""
    
    configuration = config.get("configurable", {})
    user_id = configuration.get("thread_id", None)
    if not user_id:
        raise ValueError("No user_id configured.")
    
    db = "shopping_assistant.sqlite"
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    
    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

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
    conn.close()

    # Confirmation message with updated cart
    return {
        "message": f"Item has been {action} in your cart.",
        "cart": [{"product_id": item[0], "quantity": item[1]} for item in cart_items]
    }


@tool
def remove_from_cart(config: RunnableConfig, product_id: int) -> Dict:
    """Removes an item from the user's cart, asks for confirmation, and provides a final message."""
    
    configuration = config.get("configurable", {})
    user_id = configuration.get("thread_id", None)
    if not user_id:
        raise ValueError("No user_id configured.")
    
    db = "shopping_assistant.sqlite"
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    
    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Check if the item exists in the cart
    cursor.execute("SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    result = cursor.fetchone()

    if not result:
        # If item not in cart, return a message
        conn.close()
        return {"message": "Item not found in your cart."}

    # Remove the item from the cart
    cursor.execute("DELETE FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    conn.commit()

    # Fetch the updated cart for confirmation
    cursor.execute("SELECT product_id, quantity FROM cart WHERE user_id = ?", (user_id,))
    cart_items = cursor.fetchall()
    conn.close()

    # Confirmation message with updated cart
    return {
        "message": "Item has been removed from your cart.",
        "cart": [{"product_id": item[0], "quantity": item[1]} for item in cart_items]
    }
    
    
@tool
def view_checkout_info(config: RunnableConfig) -> Dict:
    """Provides a summary of items in the cart for the given user, including total price for checkout."""
    
    db = "shopping_assistant.sqlite"
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    
    configuration = config.get("configurable", {})
    user_id = configuration.get("thread_id", None)
    if not user_id:
        raise ValueError("No user_id configured.")

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

    conn.close()
    
    # Format the checkout information
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



