from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from services.email_notifications import EmailNotificationService
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Test email verification functionality'
    
    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("TESTING EMAIL VERIFICATION FUNCTIONALITY")
        self.stdout.write("=" * 60)
        
        # Create test user
        test_email = f"test_verify_{uuid.uuid4().hex[:8]}@gmail.com"
        self.stdout.write(f"Creating test user: {test_email}")
        
        try:
            user = User.objects.create_user(
                email=test_email,
                name='Test',
                first_name='Verification',
                password='testpass123'
            )
            self.stdout.write(f"✅ User created: {user.email}")
            self.stdout.write(f"   User ID: {user.id}")
            self.stdout.write(f"   Active: {user.is_active}")
            self.stdout.write(f"   Verified: {user.is_verified}")
            self.stdout.write(f"   Token: {user.verification_token}")
            
        except Exception as e:
            self.stdout.write(f"❌ User creation failed: {e}")
            return
        
        # Test email sending
        self.stdout.write("\n" + "-" * 40)
        self.stdout.write("Testing EmailNotificationService")
        self.stdout.write("-" * 40)
        
        try:
            verification_url = f"http://127.0.0.1:8000/accounts/verify/{user.verification_token}/"
            self.stdout.write(f"Verification URL: {verification_url}")
            
            result = EmailNotificationService.send_verification_email(user, verification_url)
            self.stdout.write(f"✅ Email sent successfully!")
            self.stdout.write(f"   Result: {result}")
            
        except Exception as e:
            self.stdout.write(f"❌ Email sending failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test the old function
        self.stdout.write("\n" + "-" * 40)
        self.stdout.write("Testing accounts.views.send_verification_email")
        self.stdout.write("-" * 40)
        
        try:
            from accounts.views import send_verification_email
            send_verification_email(user)
            self.stdout.write("✅ Old email function works!")
            
        except Exception as e:
            self.stdout.write(f"❌ Old email function failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Cleanup
        self.stdout.write("\n" + "-" * 40)
        self.stdout.write("Cleaning up")
        self.stdout.write("-" * 40)
        
        try:
            user.delete()
            self.stdout.write("✅ Test user deleted")
        except Exception as e:
            self.stdout.write(f"❌ Cleanup failed: {e}")
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("EMAIL VERIFICATION TEST COMPLETED")
        self.stdout.write("=" * 60)
