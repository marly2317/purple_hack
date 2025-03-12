import sqlite3
import json

def init_database():
    try:
        # Чтение данных из JSON-файла
        with open(r'C:\Users\Huawei\Shopping-Assistant-with-LangGraph\flipkart_fashion_products_dataset.json', 'r', encoding='utf-8') as f:
            products_data = json.load(f)

        # Подготовка данных для вставки
        formatted_products = []
        for product in products_data:
            try:
                # Преобразование цены (удаляем запятые и преобразуем в float)
                price = float(product.get('selling_price', '0').replace(',', ''))
                
                # Извлечение процента скидки
                discount_str = product.get('discount', '0%').replace('% off', '').strip()
                discount = float(discount_str) if discount_str else 0.0
                
                # Преобразование рейтинга
                rating = float(product.get('average_rating', 0))
                
                # Определение наличия на складе (10 - пример значения для "в наличии")
                stock = 0 if product.get('out_of_stock', True) else 10
                
                # Получение первой картинки
                thumbnail = product.get('images', [''])[0]

                formatted_products.append((
                    product.get('title', ''),
                    product.get('description', ''),
                    price,
                    discount,
                    rating,
                    stock,
                    product.get('brand', ''),
                    product.get('category', ''),
                    thumbnail
                ))
            except Exception as e:
                print(f"Ошибка обработки продукта {product.get('pid')}: {e}")

        # Создание базы данных
        conn = sqlite3.connect('shopping_assistant.sqlite')
        cursor = conn.cursor()
        
        # Удаление старых таблиц
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS cart")
        
        # Создание новых таблиц
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
        
        # Вставка данных
        cursor.executemany(''' 
            INSERT INTO products 
            (title, description, price, discountPercentage, rating, stock, brand, category, thumbnail) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) 
        ''', formatted_products)
        
        conn.commit()
        conn.close()
        print(f"База данных успешно инициализирована! Загружено {len(formatted_products)} записей.")
        return True
    
    except Exception as e:
        print(f"Критическая ошибка при инициализации базы данных: {e}")
        return False

if __name__ == '__main__':
    init_database()