from django.test import TestCase
from django.urls import reverse

from apps.categories.models import Category, SubCategory
from apps.products.models import Product


class ProductListFilterTests(TestCase):
    def setUp(self):
        self.cat_fish = Category.objects.create(name='Fish')
        self.cat_meat = Category.objects.create(name='Meat')
        self.sub_salmon = SubCategory.objects.create(category=self.cat_fish, name='Salmon')

        Product.objects.create(name='Fish A', category=self.cat_fish, price=1.00)
        Product.objects.create(name='Fish Salmon', category=self.cat_fish, subcategory=self.sub_salmon, price=2.00)
        Product.objects.create(name='Meat Salmon', category=self.cat_meat, subcategory=self.sub_salmon, price=3.00)

    def test_category_id_matches_category_or_subcategory(self):
        response = self.client.get('/api/products/list/', {'category_id': self.cat_fish.id})
        self.assertEqual(response.status_code, 200)
        data = response.json().get('data', [])
        product_names = {item['name'] for item in data}

        self.assertIn('Fish A', product_names)
        self.assertIn('Fish Salmon', product_names)
        self.assertNotIn('Meat Salmon', product_names)

    def test_subcategory_id_filters_subcategory_only(self):
        response = self.client.get('/api/products/list/', {'subcategory_id': self.sub_salmon.id})
        self.assertEqual(response.status_code, 200)
        data = response.json().get('data', [])
        product_names = {item['name'] for item in data}

        self.assertIn('Fish Salmon', product_names)
        self.assertIn('Meat Salmon', product_names)
        self.assertNotIn('Fish A', product_names)
