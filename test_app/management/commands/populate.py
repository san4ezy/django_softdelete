from django.core.management.base import BaseCommand

from test_app.models import Shop, Product, Category

SHOP = {
    'Mari': {
        'products': [
            dict(product_number='0001', name='Small Box', price=100),
            dict(product_number='0002', name='Middle Box', price=200),
            dict(product_number='0003', name='Big Box', price=500),
        ]
    },
    'Juana': {
        'products': [
            dict(product_number='0004', name='Small Box', price=110),
            dict(product_number='0005', name='Middle Box', price=250),
            dict(product_number='0006', name='Big Box', price=600),
        ]
    },
}


class Command(BaseCommand):
    def handle(self, *args, **options):

        category, _ = Category.objects.get_or_create(name='Gifts')

        for name, kw in SHOP.items():
            products = kw['products']
            shop, c = Shop.objects.get_or_create(name=name)
            if c:
                for product in products:
                    product_number = product.pop('product_number', '')
                    product['category'] = category
                    p, c = Product.objects.get_or_create(
                        product_number=product_number,
                        shop=shop,
                        defaults=product,
                    )

        self.stdout.write(
            self.style.SUCCESS(f'Success!')
        )

