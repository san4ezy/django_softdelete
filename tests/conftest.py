from contextlib import contextmanager
from unittest.mock import MagicMock, Mock

import pytest
import random
import string

from django.contrib.admin import AdminSite
from django.db.models.signals import pre_delete
from django.test import RequestFactory

from test_app.models import *


@pytest.fixture
def name():
    l: int = 5
    return ''.join(
        [random.choice(string.ascii_letters) for _ in range(l)]
    ).capitalize()


@pytest.fixture
def price():
    return random.randint(10, 99) * 10


@pytest.fixture
def shop(name):
    return Shop.objects.create(name=name)


@pytest.fixture
def category(name):
    return Category.objects.create(name=name)


@pytest.fixture
def product(name, shop, category, price):
    return Product.objects.create(
        name=name,
        shop=shop,
        category=category,
        price=price,
    )


@pytest.fixture
def another_product(name, shop, category, price):
    return Product.objects.create(
        name=name,
        shop=shop,
        category=category,
        price=price,
    )


@pytest.fixture
def employee(name):
    return Employee.objects.create(name=name)


@pytest.fixture
def product_restricted_category(name, shop, category, price):
    return ProductRestrictedCategory.objects.create(
        name=name,
        shop=shop,
        category=category,
        price=price,
    )


@pytest.fixture
def product_not_soft_relation(name, shop, price):
    return ProductNotSoftRelations.objects.create(
        name=name,
        shop=shop,
        price=price,
    )


@pytest.fixture
def not_soft_related_model(name, product_not_soft_relation):
    return NotSoftRelatedModel.objects.create(
        product=product_not_soft_relation
    )


@pytest.fixture
def option(name, product):
    return Option.objects.create(name=name, product=product)


@pytest.fixture
def another_option(name, another_product):
    return Option.objects.create(name=name, product=another_product)


@pytest.fixture
def color(name, product):
    return Color.objects.create(name=name, product=product)


@pytest.fixture
def order(name, product):
    return Order.objects.create(name=name, product=product)


@pytest.fixture
def lead(name, product):
    return Lead.objects.create(name=name, product=product)


@pytest.fixture
def product_image(name, product):
    return ProductImage.objects.create(name=name)


@pytest.fixture
def product_landing(name):
    return ProductLanding.objects.create(text=name)


@pytest.fixture
def product_factory(shop, category):
    def create_product(name=None, price=None, option=None, landing=None):
        if name is None:
            name = ''.join(random.choices(string.ascii_uppercase, k=10))
        if price is None:
            price = random.randint(10, 99) * 10
        kw = dict(name=name, shop=shop, category=category, price=price)
        if landing:
            kw['landing'] = landing
        product = Product.objects.create(**kw)
        if option:
            option.product = product
            option.save()
        return product
    return create_product


@pytest.fixture
def option_factory():
    def create_option(name=None):
        if name is None:
            name = ''.join(random.choices(string.ascii_uppercase, k=10))
        return Option.objects.create(name=name)
    return create_option


@pytest.fixture
def product_image_factory():
    def create_product_image(name=None):
        if name is None:
            name = ''.join(random.choices(string.ascii_uppercase, k=10))
        return ProductImage.objects.create(name=name)
    return create_product_image


@pytest.fixture
def signal_mock():
    @contextmanager
    def _mock(signal, sender):
        m = MagicMock()
        signal.connect(m, sender=sender)
        try:
            yield m
        finally:
            signal.disconnect(m, sender=sender)
    return _mock


@pytest.fixture
def admin_site():
    """Create a test admin site"""
    return AdminSite()


@pytest.fixture
def request_factory():
    """Create a request factory"""
    return RequestFactory()


@pytest.fixture
def admin_request(request_factory):
    """Create a mock admin request with user"""
    request = request_factory.get('/admin/')
    request.user = Mock()
    request.user.is_authenticated = True
    request.user.is_staff = True
    request.user.is_superuser = True
    return request
