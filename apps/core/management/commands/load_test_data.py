import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.categories.models import Category, SubCategory, PackagingType
from apps.products.models import Product
from apps.accounts.models import DeliveryZone


class Command(BaseCommand):
    help = 'Load test data from test_data.json'

    def handle(self, *args, **options):
        # Load test data
        test_data_path = os.path.join(settings.BASE_DIR, 'test_data.json')

        if not os.path.exists(test_data_path):
            self.stdout.write(self.style.ERROR('test_data.json not found'))
            return

        with open(test_data_path, 'r') as f:
            data = json.load(f)

        # Load delivery zones
        self.stdout.write('Loading delivery zones...')
        for zone_data in data['delivery_zones']:
            DeliveryZone.objects.get_or_create(
                name=zone_data['name'],
                defaults=zone_data
            )
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(data["delivery_zones"])} delivery zones'))

        # Load categories
        self.stdout.write('Loading categories...')
        for cat_data in data['categories']:
            Category.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(data["categories"])} categories'))

        # Load packaging types
        self.stdout.write('Loading packaging types...')
        for pack_data in data['packaging_types']:
            PackagingType.objects.get_or_create(
                packaging_type=pack_data['packaging_type'],
                defaults=pack_data
            )
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(data["packaging_types"])} packaging types'))

        # Load subcategories
        self.stdout.write('Loading subcategories...')
        for sub_data in data['subcategories']:
            category = Category.objects.get(name=sub_data['category'])
            SubCategory.objects.get_or_create(
                name=sub_data['name'],
                category=category,
                defaults={'status': sub_data['status']}
            )
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(data["subcategories"])} subcategories'))

        # Load products
        self.stdout.write('Loading products...')
        for prod_data in data['products']:
            category = Category.objects.get(name=prod_data['category'])
            subcategory = SubCategory.objects.get(name=prod_data['subcategory'])
            Product.objects.get_or_create(
                name=prod_data['name'],
                defaults={
                    'description': prod_data['description'],
                    'price': prod_data['price'],
                    'category': category,
                    'subcategory': subcategory,
                    'status': prod_data['status'],
                    'image': prod_data['image']
                }
            )
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(data["products"])} products'))

        self.stdout.write(self.style.SUCCESS('Test data loaded successfully! 🎉'))