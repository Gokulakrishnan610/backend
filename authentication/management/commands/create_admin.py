from django.core.management.base import BaseCommand
from authentication.models import User
from django.db import transaction

class Command(BaseCommand):
    help = 'Creates a superuser for the application'

    def handle(self, *args, **options):
        self.stdout.write('Creating admin user...')
        
        admin_email = 'admin@university.com'
        admin_password = 'admin123'
        
        try:
            with transaction.atomic():
                # Check if the user already exists
                if User.objects.filter(email=admin_email).exists():
                    self.stdout.write(self.style.WARNING(f'Admin user {admin_email} already exists'))
                    return
                
                # Create the superuser
                User.objects.create_superuser(
                    email=admin_email,
                    password=admin_password,
                    first_name='Admin',
                    last_name='User',
                    is_active=True,
                    phone_number='',
                    gender='M',
                    user_type='admin'
                )
                
                self.stdout.write(self.style.SUCCESS(f'Successfully created admin user: {admin_email}'))
                self.stdout.write(self.style.SUCCESS(f'Password: {admin_password}'))
                self.stdout.write(self.style.WARNING('Please change this password after first login!'))
                
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error creating admin user: {str(e)}')) 