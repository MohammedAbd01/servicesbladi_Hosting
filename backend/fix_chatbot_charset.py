#!/usr/bin/env python
import os
import sys
import django
from django.db import connection

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'servicesbladi.settings')
django.setup()

def fix_chatbot_charset():
    """Fix charset issues for chatbot tables to support emojis"""
    
    with connection.cursor() as cursor:
        try:
            print("🔧 Fixing database charset for emoji support...")
            
            # Fix the database charset
            cursor.execute("ALTER DATABASE servicesbladi CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;")
            print("✅ Database charset updated to utf8mb4")
            
            # Fix chatbot_chatsession table
            cursor.execute("""
                ALTER TABLE chatbot_chatsession 
                CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """)
            print("✅ chatbot_chatsession table charset fixed")
            
            # Fix chatbot_chatmessage table
            cursor.execute("""
                ALTER TABLE chatbot_chatmessage 
                CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """)
            print("✅ chatbot_chatmessage table charset fixed")
            
            # Fix specific content column
            cursor.execute("""
                ALTER TABLE chatbot_chatmessage 
                MODIFY content LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """)
            print("✅ content column charset fixed")
            
            print("\n🎉 Database charset fix completed successfully!")
            print("💬 Emojis and special characters should now work properly")
            
        except Exception as e:
            print(f"❌ Error fixing charset: {e}")
            
            # If tables don't exist, let's check what tables we have
            cursor.execute("SHOW TABLES LIKE 'chatbot%';")
            tables = cursor.fetchall()
            print(f"Found chatbot tables: {tables}")
            
            if not tables:
                print("📝 No chatbot tables found. Please run migrations first:")
                print("python manage.py makemigrations chatbot")
                print("python manage.py migrate")

if __name__ == '__main__':
    fix_chatbot_charset()
