import sqlite3

def init_database():
    try:
        conn = sqlite3.connect('shopping_assistant.sqlite')
        cursor = conn.cursor()
        
        # Удаляем существующую таблицу products для применения новой схемы
        cursor.execute("DROP TABLE IF EXISTS products")
        
        # Создаем таблицу products с полями, соответствующими https://dummyjson.com/products
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

        # Создаем таблицу cart для хранения товаров в корзине
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            user_id TEXT,
            product_id INTEGER,
            quantity INTEGER,
            PRIMARY KEY (user_id, product_id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
        ''')

        # Тестовые данные для таблицы products
        sample_products = [
            # (title, description, price, discountPercentage, rating, stock, brand, category, thumbnail)
            ('Chanel No. 5', 'Classic floral aldehyde fragrance', 135.00, 10.0, 4.5, 50, 'Chanel', 'Fragrance', 'chanel_no5.jpg'),
            ('Dior Sauvage', 'Fresh and bold masculine fragrance', 155.00, 10.0, 4.7, 40, 'Dior', 'Fragrance', 'dior_sauvage.jpg'),
            ('Jo Malone London', 'English Pear & Freesia Cologne', 142.00, 10.0, 4.2, 30, 'Jo Malone', 'Fragrance', 'jo_malone.jpg'),
            ('Tom Ford Black Orchid', 'Luxurious and sophisticated unisex fragrance', 180.00, 10.0, 4.8, 20, 'Tom Ford', 'Fragrance', 'tom_ford_black_orchid.jpg'),
            ('Versace Bright Crystal', 'Fresh and floral feminine fragrance', 96.00, 10.0, 4.1, 60, 'Versace', 'Fragrance', 'versace_bright_crystal.jpg'),
            ('iPhone 14', 'Latest Apple smartphone', 999.00, 10.0, 4.3, 80, 'Apple', 'Electronics', 'iphone_14.jpg'),
            ('Nike Air Max', 'Comfortable running shoes', 129.99, 10.0, 4.6, 100, 'Nike', 'Footwear', 'nike_air_max.jpg'),
            ('Essence Mascara', 'Lash Princess False Lash Effect Mascara', 4.99, 10.0, 3.9, 150, 'Essence', 'Beauty', 'essence_mascara.jpg'),
            ('Samsung TV', '55-inch 4K Smart TV', 699.99, 10.0, 4.4, 25, 'Samsung', 'Electronics', 'samsung_tv.jpg'),
            ('Cotton T-Shirt', 'Basic crew neck t-shirt', 19.99, 10.0, 3.8, 200, 'Generic', 'Clothing', 'cotton_tshirt.jpg')
        ]
        
        # Проверяем, пуста ли таблица products, и добавляем данные, если она пуста
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