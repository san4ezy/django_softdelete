from django.db import models

from django_softdelete.models import SoftDeleteModel


class Shop(SoftDeleteModel):
    name = models.CharField(max_length=32)
    is_active = models.BooleanField(default=True)


class Category(SoftDeleteModel):
    name = models.CharField(max_length=32)


class ProductImage(SoftDeleteModel):
    name = models.CharField(max_length=32)


class ProductLanding(SoftDeleteModel):
    text = models.TextField()


class ProductAbstract(SoftDeleteModel):
    product_number = models.CharField(max_length=8)
    name = models.CharField(max_length=32)
    price = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True)

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)

    images = models.ManyToManyField(ProductImage)

    landing = models.OneToOneField(ProductLanding, on_delete=models.CASCADE, null=True)

    class Meta:
        abstract = True


class Product(ProductAbstract):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)


class ProductRestrictedCategory(ProductAbstract):
    category = models.ForeignKey(Category, on_delete=models.RESTRICT)


class Option(SoftDeleteModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)


class Color(SoftDeleteModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)


class Order(SoftDeleteModel):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    name = models.CharField(max_length=32)


class Lead(SoftDeleteModel):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=32)


class ProductNotSoftRelations(ProductAbstract):
    pass  # related to NotSoftRelatedModel with a revers relation


class NotSoftRelatedModel(models.Model):
    product = models.ForeignKey(
        ProductNotSoftRelations, on_delete=models.CASCADE, null=True
    )
