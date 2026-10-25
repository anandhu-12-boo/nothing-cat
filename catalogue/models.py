from django.core.validators import FileExtensionValidator
from django.db import models

class Category(models.Model):
    name = models.CharField(
        max_length=80,
        unique=True,
    )

    slug = models.SlugField(
        max_length=90,
        unique=True,
    )

    icon = models.CharField(
        max_length=30,
        blank=True,
        help_text="Example: 📱, 🎧 or 📺",
    )

    description = models.CharField(
        max_length=250,
        blank=True,
    )

    sort_order = models.PositiveIntegerField(
        default=0,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = [
            "sort_order",
            "name",
        ]

        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True)
    logo_text = models.CharField(max_length=30, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

class ProductModel(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="product_models",
    )

    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="product_models",
    )

    name = models.CharField(
        max_length=120,
    )

    slug = models.SlugField(
        max_length=140,
    )

    description = models.CharField(
        max_length=300,
        blank=True,
    )

    colours = models.CharField(
        max_length=220,
        blank=True,
    )

    specifications = models.JSONField(
        default=dict,
        blank=True,
    )

    sort_order = models.PositiveIntegerField(
        default=0,
    )

    is_active = models.BooleanField(
        default=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "category__sort_order",
            "brand__sort_order",
            "sort_order",
            "name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["brand", "slug"],
                name="unique_brand_product_model_slug",
            )
        ]

    def __str__(self):
        return f"{self.brand.name} {self.name}"

class ProductModelImage(models.Model):
    product_model = models.ForeignKey(
        ProductModel,
        on_delete=models.CASCADE,
        related_name="images",
    )

    colour = models.CharField(
        max_length=100,
        blank=True,
        help_text=(
            "Enter the colour exactly as shown in the model's "
            "colour list, for example: Black"
        ),
    )

    image = models.ImageField(
        upload_to="products/models/",
    )

    is_primary = models.BooleanField(
        default=False,
        help_text=(
            "Use as the main image for this colour."
        ),
    )

    sort_order = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = [
            "sort_order",
            "-is_primary",
            "id",
        ]

    def __str__(self):
        colour = self.colour or "General"

        return (
            f"{self.product_model.name} - "
            f"{colour}"
        )

class Product(models.Model):
    product_model = models.ForeignKey(
        ProductModel,
        on_delete=models.PROTECT,
        related_name="variants",
        null=True,
        blank=True,
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="products",
    )
    model = models.CharField(max_length=120)
    variant = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=240)
    selling_price = models.DecimalField(
        "MOP",
        max_digits=12,
        decimal_places=2,
    )
    mrp = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    category = models.CharField(
        max_length=80,
        default="Phones",
    )
    colours = models.CharField(
        max_length=220,
        blank=True,
    )
    specifications = models.JSONField(
        default=dict,
        blank=True,
    )
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "brand__sort_order",
            "selling_price",
            "model",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["brand", "model", "variant"],
                name="unique_brand_model_variant",
            )
        ]

    def save(self, *args, **kwargs):
        if self.product_model_id:
            self.brand = self.product_model.brand
            self.model = self.product_model.name
            self.category = self.product_model.category.name

            if not self.description:
                self.description = (
                    self.product_model.description
                )

        super().save(*args, **kwargs)

    def __str__(self):
        if self.product_model:
            model_name = self.product_model.name
            brand_name = self.product_model.brand.name
        else:
            model_name = self.model
            brand_name = self.brand.name

        return (
            f"{brand_name} "
            f"{model_name} "
            f"{self.variant}"
        ).strip()

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    colour = models.CharField(
        max_length=50,
        blank=True,
        help_text="Example: Black, White or Blue",
    )
    image = models.ImageField(
        upload_to="products/",
    )
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = [
            "-is_primary",
            "sort_order",
            "id",
        ]

    def __str__(self):
        colour_text = (
            f" - {self.colour}"
            if self.colour
            else ""
        )
        return f"{self.product}{colour_text}"

class BrandDocument(models.Model):
    DOCUMENT_TYPES = [
        ("affordability", "Affordability offers"),
        ("catalogue", "Product catalogue"),
    ]

    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPES,
    )

    title = models.CharField(max_length=150)

    file = models.FileField(
        upload_to="brand_documents/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf"]
            )
        ],
    )

    version = models.CharField(
        max_length=50,
        blank=True,
    )

    valid_from = models.DateField(
        null=True,
        blank=True,
    )

    valid_until = models.DateField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "-valid_from",
            "-uploaded_at",
        ]

    def __str__(self):
        return f"{self.brand.name} - {self.title}"