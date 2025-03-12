import sqlite3

def init_database():
    try:
        conn = sqlite3.connect('shopping_assistant.sqlite')
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS cart")
        
        cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            price REAL,
            discountPercentage REAL DEFAULT 0.0,
            rating REAL DEFAULT 0.0,
            stock INTEGER DEFAULT 0,
            brand TEXT,
            category TEXT,
            thumbnail TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            user_id TEXT,
            product_id INTEGER,
            quantity INTEGER,
            PRIMARY KEY (user_id, product_id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
        ''')

        # Убраны русские описания (последний элемент в каждом кортеже)
        sample_products = [
    # Одежда
    ('Evening Dress', 'Elegant evening dress with deep neckline', 250.00, 15.0, 4.8, 20, 'Gucci', 'Clothing', 'evening_dress.jpg'),
    ('Business Suit', 'Tailored business suit for men', 350.00, 10.0, 4.6, 30, 'Armani', 'Clothing', 'business_suit.jpg'),
    ('Casual T-Shirt', 'Comfortable cotton t-shirt', 25.00, 5.0, 4.2, 100, 'Nike', 'Clothing', 'casual_tshirt.jpg'),
    ('Denim Jeans', 'Slim-fit denim jeans', 60.00, 10.0, 4.3, 80, 'Levi\'s', 'Clothing', 'denim_jeans.jpg'),
    ('Wool Coat', 'Warm wool coat for winter', 200.00, 15.0, 4.5, 25, 'Burberry', 'Clothing', 'wool_coat.jpg'),
    ('Cocktail Dress', 'Chic cocktail dress for parties', 180.00, 10.0, 4.7, 20, 'Versace', 'Clothing', 'cocktail_dress.jpg'),
    ('Sports Jacket', 'Waterproof sports jacket', 90.00, 10.0, 4.4, 50, 'The North Face', 'Clothing', 'sports_jacket.jpg'),
    ('Blazer', 'Structured blazer for women', 120.00, 10.0, 4.5, 35, 'Zara', 'Clothing', 'blazer.jpg'),
    ('Knit Sweater', 'Cozy knit sweater', 45.00, 5.0, 4.3, 60, 'H&M', 'Clothing', 'knit_sweater.jpg'),
    ('Summer Skirt', 'Flowy summer skirt', 35.00, 5.0, 4.2, 70, 'Mango', 'Clothing', 'summer_skirt.jpg'),

    # Обувь
    ('Running Shoes', 'Lightweight running shoes with cushioning', 80.00, 10.0, 4.5, 60, 'Adidas', 'Footwear', 'running_shoes.jpg'),
    ('Leather Boots', 'Stylish leather boots for winter', 120.00, 15.0, 4.7, 40, 'Timberland', 'Footwear', 'leather_boots.jpg'),
    ('High Heels', 'Elegant high heels for formal events', 90.00, 10.0, 4.4, 50, 'Jimmy Choo', 'Footwear', 'high_heels.jpg'),
    ('Casual Sneakers', 'Versatile white sneakers', 55.00, 5.0, 4.3, 90, 'Converse', 'Footwear', 'casual_sneakers.jpg'),
    ('Sandals', 'Comfortable flat sandals', 40.00, 5.0, 4.2, 80, 'Birkenstock', 'Footwear', 'sandals.jpg'),
    ('Ankle Boots', 'Chic ankle boots with low heel', 100.00, 10.0, 4.6, 45, 'Clarks', 'Footwear', 'ankle_boots.jpg'),
    ('Loafers', 'Classic leather loafers', 85.00, 10.0, 4.4, 50, 'Tod\'s', 'Footwear', 'loafers.jpg'),

    # Аксессуары
    ('Leather Handbag', 'Classic leather handbag', 150.00, 10.0, 4.6, 30, 'Louis Vuitton', 'Accessories', 'leather_handbag.jpg'),
    ('Silk Scarf', 'Luxurious silk scarf', 70.00, 10.0, 4.3, 40, 'Hermes', 'Accessories', 'silk_scarf.jpg'),
    ('Sunglasses', 'Stylish sunglasses with UV protection', 50.00, 10.0, 4.2, 100, 'Ray-Ban', 'Accessories', 'sunglasses.jpg'),
    ('Leather Belt', 'Classic leather belt', 40.00, 10.0, 4.3, 70, 'Calvin Klein', 'Accessories', 'leather_belt.jpg'),
    ('Wristwatch', 'Elegant wristwatch with leather strap', 120.00, 10.0, 4.6, 30, 'Rolex', 'Accessories', 'wristwatch.jpg'),
    ('Statement Necklace', 'Bold statement necklace', 60.00, 10.0, 4.4, 25, 'Swarovski', 'Accessories', 'statement_necklace.jpg'),
    ('Tote Bag', 'Spacious tote bag', 80.00, 10.0, 4.5, 40, 'Michael Kors', 'Accessories', 'tote_bag.jpg'),
    ('Fedora Hat', 'Stylish fedora hat', 45.00, 5.0, 4.3, 50, 'Brixton', 'Accessories', 'fedora_hat.jpg')
]
        
        cursor.execute('SELECT COUNT(*) FROM products')
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.executemany(''' 
                INSERT INTO products (title, description, price, discountPercentage, rating, stock, brand, category, thumbnail) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) 
            ''', sample_products)
        
        conn.commit()
        conn.close()
        print("База данных успешно инициализирована!")
        return True
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        return False

if __name__ == '__main__':
    init_database()