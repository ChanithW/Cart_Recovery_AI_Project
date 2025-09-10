import mysql.connector
from config import Config

def apply_enhanced_schema():
    """Apply the enhanced database schema"""
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = conn.cursor()

        # Read and execute the enhanced schema
        with open('enhanced_schema.sql', 'r') as f:
            schema_sql = f.read()

        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        for statement in statements:
            try:
                cursor.execute(statement)
                print(f'✅ Executed: {statement[:50]}...')
            except Exception as e:
                print(f'❌ Error: {e}')

        conn.commit()
        cursor.close()
        conn.close()
        print('\n🎉 Enhanced database schema applied successfully!')
        
    except Exception as e:
        print(f"Database connection error: {e}")

if __name__ == "__main__":
    apply_enhanced_schema()
