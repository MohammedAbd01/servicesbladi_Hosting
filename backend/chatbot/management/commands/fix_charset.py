from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Fix database charset for emoji support'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                self.stdout.write("🔧 Fixing database charset for emoji support...")
                
                # Fix the database charset
                cursor.execute("ALTER DATABASE servicesbladi CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;")
                self.stdout.write("✅ Database charset updated to utf8mb4")
                
                # Fix chatbot_chatsession table
                cursor.execute("""
                    ALTER TABLE chatbot_chatsession 
                    CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
                """)
                self.stdout.write("✅ chatbot_chatsession table charset fixed")
                
                # Fix chatbot_chatmessage table
                cursor.execute("""
                    ALTER TABLE chatbot_chatmessage 
                    CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
                """)
                self.stdout.write("✅ chatbot_chatmessage table charset fixed")
                
                # Fix specific content column
                cursor.execute("""
                    ALTER TABLE chatbot_chatmessage 
                    MODIFY content LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
                """)
                self.stdout.write("✅ content column charset fixed")
                
                self.stdout.write(self.style.SUCCESS("\n🎉 Database charset fix completed successfully!"))
                self.stdout.write("💬 Emojis and special characters should now work properly")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error fixing charset: {e}"))
                
                # If tables don't exist, let's check what tables we have
                cursor.execute("SHOW TABLES LIKE 'chatbot%';")
                tables = cursor.fetchall()
                self.stdout.write(f"Found chatbot tables: {tables}")
                
                if not tables:
                    self.stdout.write("📝 No chatbot tables found. Please run migrations first:")
                    self.stdout.write("python manage.py makemigrations chatbot")
                    self.stdout.write("python manage.py migrate")
