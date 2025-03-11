import sqlite3

def init_database():
    try:
        conn = sqlite3.connect('shopping_assistant.sqlite')
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            price REAL,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        sample_products = [
            ('Chanel No. 5', 'Classic floral aldehyde fragrance', 135.00, 'Fragrance'),
            ('Dior Sauvage', 'Fresh and bold masculine fragrance', 155.00, 'Fragrance'),
            ('Jo Malone London', 'English Pear & Freesia Cologne', 142.00, 'Fragrance'),
            ('Tom Ford Black Orchid', 'Luxurious and sophisticated unisex fragrance', 180.00, 'Fragrance'),
            ('Versace Bright Crystal', 'Fresh and floral feminine fragrance', 96.00, 'Fragrance'),
            ('iPhone 14', 'Latest Apple smartphone', 999.00, 'Electronics'),
            ('Nike Air Max', 'Comfortable running shoes', 129.99, 'Footwear'),
            ('Essence Mascara', 'Lash Princess False Lash Effect Mascara', 4.99, 'Beauty'),
            ('Samsung TV', '55-inch 4K Smart TV', 699.99, 'Electronics'),
            ('Cotton T-Shirt', 'Basic crew neck t-shirt', 19.99, 'Clothing')
        ]
    
        cursor.execute('SELECT COUNT(*) FROM products')
        count = cursor.fetchone()[0]
    
        if count == 0:
            cursor.executemany('INSERT INTO products (title, description, price, category) VALUES (?, ?, ?, ?)', sample_products)
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

if __name__ == '__main__':
    init_database()
