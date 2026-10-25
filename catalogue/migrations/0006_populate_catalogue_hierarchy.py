from django.db import migrations
from django.utils.text import slugify


def populate_hierarchy(apps, schema_editor):
    Category = apps.get_model(
        "catalogue",
        "Category",
    )

    ProductModel = apps.get_model(
        "catalogue",
        "ProductModel",
    )

    Product = apps.get_model(
        "catalogue",
        "Product",
    )

    categories = {
        "phones": Category.objects.get_or_create(
            slug="phones",
            defaults={
                "name": "Phones",
                "icon": "📱",
                "description": "Smartphones and mobile devices",
                "sort_order": 1,
                "is_active": True,
            },
        )[0],

        "accessories": Category.objects.get_or_create(
            slug="accessories",
            defaults={
                "name": "Accessories",
                "icon": "🎧",
                "description": (
                    "Headphones, earbuds, watches "
                    "and mobile accessories"
                ),
                "sort_order": 2,
                "is_active": True,
            },
        )[0],

        "televisions": Category.objects.get_or_create(
            slug="televisions",
            defaults={
                "name": "Televisions",
                "icon": "📺",
                "description": "Televisions and displays",
                "sort_order": 3,
                "is_active": True,
            },
        )[0],
    }

    for product in Product.objects.select_related(
        "brand"
    ).all():

        old_category = (
            product.category or ""
        ).lower()

        if (
            "tv" in old_category
            or "television" in old_category
        ):
            category = categories["televisions"]

        elif (
            "headphone" in old_category
            or "earbud" in old_category
            or "audio" in old_category
            or "watch" in old_category
            or "accessor" in old_category
        ):
            category = categories["accessories"]

        else:
            category = categories["phones"]

        model_slug = (
            slugify(product.model)
            or f"model-{product.pk}"
        )

        product_model, created = (
            ProductModel.objects.get_or_create(
                brand=product.brand,
                slug=model_slug,
                defaults={
                    "category": category,
                    "name": product.model,
                    "description": product.description,
                    "colours": product.colours,
                    "specifications": (
                        product.specifications
                    ),
                    "is_active": True,
                },
            )
        )

        product.product_model = product_model

        product.save(
            update_fields=["product_model"]
        )


def reverse_hierarchy(apps, schema_editor):
    Product = apps.get_model(
        "catalogue",
        "Product",
    )

    Product.objects.update(
        product_model=None
    )


class Migration(migrations.Migration):

    dependencies = [
        (
            "catalogue",
            "0005_category_alter_product_selling_price_productmodel_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            populate_hierarchy,
            reverse_hierarchy,
        ),
    ]