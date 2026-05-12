import pytest
from rest_framework.test import APIClient
from apps.products.models import Product, Category


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_product():
    def _create(name='Test Product', price=100, category='test', **kwargs):
        cat, _ = Category.objects.get_or_create(name=category)
        return Product.objects.create(name=name, price=price, category=cat, **kwargs)
    return _create
