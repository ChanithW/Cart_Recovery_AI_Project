from database import DatabaseManager
from config import Config

def add_sample_products():
    # Initialize database
    db = DatabaseManager(
        host=Config.DB_HOST,
        user=Config.DB_USER, 
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )

    if db.connect():
        cursor = db.connection.cursor()
        
        # Check if products exist
        cursor.execute('SELECT COUNT(*) FROM products')
        count = cursor.fetchone()[0]
        print(f'Current products in database: {count}')
        
        if count == 0:
            print('Adding sample products...')
            sample_products = [
                ('Premium Laptop', 'High-performance laptop for professionals', 1299.99, 'https://via.placeholder.com/400x300?text=Laptop', 15, 'Electronics'),
                ('Wireless Headphones', 'Noise-canceling wireless headphones', 199.99, 'https://via.placeholder.com/400x300?text=Headphones', 25, 'Electronics'),
                ('Smart Watch', 'Fitness tracking smartwatch', 299.99, 'https://via.placeholder.com/400x300?text=Watch', 30, 'Electronics'),
                ('Coffee Maker', 'Programmable coffee maker', 89.99, 'https://via.placeholder.com/400x300?text=Coffee', 20, 'Appliances'),
                ('Running Shoes', 'Comfortable athletic shoes', 129.99, 'https://via.placeholder.com/400x300?text=Shoes', 40, 'Sports'),
                ('Backpack', 'Durable travel backpack', 79.99, 'https://via.placeholder.com/400x300?text=Backpack', 35, 'Travel')
            ]
            
            for product in sample_products:
                cursor.execute('''
                    INSERT INTO products (name, description, price, image_url, stock_quantity, category)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', product)
            
            print('✅ Sample products added!')
        
        # Show current products
        cursor.execute('SELECT id, name, price, stock_quantity FROM products LIMIT 5')
        products = cursor.fetchall()
        print('Sample products:')
        for product in products:
            print(f'  - {product[1]}: ${product[2]} (Stock: {product[3]})')
        
        cursor.close()
        return True
    else:
        print('❌ Database connection failed!')
        return False

if __name__ == "__main__":
    add_sample_products()
