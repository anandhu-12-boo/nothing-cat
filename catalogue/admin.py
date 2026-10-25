from django.contrib import admin

from .models import (
    Brand,
    BrandDocument,
    Category,
    Product,
    ProductImage,
    ProductModel,
    ProductModelImage,
)


# --------------------------------------------------
# Inline: Documents belonging to a brand
# --------------------------------------------------
class BrandDocumentInline(admin.TabularInline):
    model = BrandDocument
    extra = 0

    fields = (
        "document_type",
        "title",
        "file",
        "version",
        "valid_from",
        "valid_until",
        "is_active",
    )


# --------------------------------------------------
# Inline: Images shared by every variant of a model
# --------------------------------------------------
class ProductModelImageInline(admin.TabularInline):
    model = ProductModelImage
    extra = 1

    fields = (
        "image",
        "colour",
        "is_primary",
        "sort_order",
    )

    verbose_name = "Shared model image"
    verbose_name_plural = "Shared model images"


# --------------------------------------------------
# Inline: RAM/storage variants belonging to a model
# --------------------------------------------------
class ProductVariantInline(admin.TabularInline):
    model = Product
    extra = 1

    fields = (
        "variant",
        "selling_price",
        "mrp",
        "stock",
        "colours",
        "is_active",
    )

    verbose_name = "Product variant"
    verbose_name_plural = "Product variants"


# --------------------------------------------------
# Inline: Images specific to one variant
# --------------------------------------------------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

    fields = (
        "image",
        "colour",
        "is_primary",
        "sort_order",
    )

    verbose_name = "Variant-specific image"
    verbose_name_plural = "Variant-specific images"


# --------------------------------------------------
# Category Admin
# --------------------------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "sort_order",
        "is_active",
    )

    list_editable = (
        "sort_order",
        "is_active",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    search_fields = (
        "name",
        "description",
    )

    ordering = (
        "sort_order",
        "name",
    )


# --------------------------------------------------
# Brand Admin
# --------------------------------------------------
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "sort_order",
        "is_active",
    )

    list_editable = (
        "sort_order",
        "is_active",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    search_fields = (
        "name",
    )

    ordering = (
        "sort_order",
        "name",
    )

    inlines = (
        BrandDocumentInline,
    )


# --------------------------------------------------
# Product Model Admin
# Example: Nothing Phone (3)
# --------------------------------------------------
@admin.register(ProductModel)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "brand",
        "category",
        "variant_count",
        "sort_order",
        "is_active",
        "updated_at",
    )

    list_filter = (
        "category",
        "brand",
        "is_active",
    )

    list_editable = (
        "sort_order",
        "is_active",
    )

    search_fields = (
        "name",
        "brand__name",
        "category__name",
        "description",
        "colours",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    ordering = (
        "category",
        "sort_order",
        "name",
    )

    fieldsets = (
        (
            "Basic information",
            {
                "fields": (
                    "category",
                    "brand",
                    "name",
                    "slug",
                    "description",
                )
            },
        ),
        (
            "Shared product information",
            {
                "description": (
                    "These colours and specifications apply to "
                    "the complete product model."
                ),
                "fields": (
                    "colours",
                    "specifications",
                ),
            },
        ),
        (
            "Display settings",
            {
                "fields": (
                    "sort_order",
                    "is_active",
                )
            },
        ),
    )

    # Shared images appear first, followed by variants.
    inlines = (
        ProductModelImageInline,
        ProductVariantInline,
    )

    @admin.display(
        description="Variants",
    )
    def variant_count(self, obj):
        return obj.variants.count()


# --------------------------------------------------
# Product Variant Admin
# Example: 12GB + 256GB
# --------------------------------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "display_model",
        "variant",
        "selling_price",
        "mrp",
        "stock",
        "is_active",
        "updated_at",
    )

    list_filter = (
        "product_model__category",
        "product_model__brand",
        "is_active",
    )

    search_fields = (
        "product_model__name",
        "product_model__brand__name",
        "variant",
        "description",
        "colours",
    )

    list_editable = (
        "selling_price",
        "mrp",
        "stock",
        "is_active",
    )

    ordering = (
        "product_model__name",
        "selling_price",
        "variant",
    )

    fieldsets = (
        (
            "Variant information",
            {
                "fields": (
                    "product_model",
                    "variant",
                    "description",
                    "colours",
                )
            },
        ),
        (
            "Price and availability",
            {
                "fields": (
                    "selling_price",
                    "mrp",
                    "stock",
                    "is_active",
                )
            },
        ),
        (
            "Variant specifications",
            {
                "description": (
                    "Add specifications that are different for "
                    "this RAM/storage variant."
                ),
                "fields": (
                    "specifications",
                ),
            },
        ),
    )

    inlines = (
        ProductImageInline,
    )

    @admin.display(
        description="Product model",
        ordering="product_model__name",
    )
    def display_model(self, obj):
        if obj.product_model:
            return obj.product_model

        return f"{obj.brand.name} {obj.model}"


# --------------------------------------------------
# Shared Product Model Image Admin
# --------------------------------------------------
@admin.register(ProductModelImage)
class ProductModelImageAdmin(admin.ModelAdmin):
    list_display = (
        "product_model",
        "colour",
        "is_primary",
        "sort_order",
    )

    list_filter = (
        "product_model__brand",
        "product_model__category",
        "colour",
        "is_primary",
    )

    search_fields = (
        "product_model__name",
        "product_model__brand__name",
        "colour",
    )

    list_editable = (
        "is_primary",
        "sort_order",
    )

    ordering = (
        "product_model",
        "sort_order",
        "-is_primary",
    )


# --------------------------------------------------
# Variant-specific Product Image Admin
# --------------------------------------------------
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "colour",
        "is_primary",
        "sort_order",
    )

    list_filter = (
        "product__product_model__brand",
        "product__product_model__category",
        "colour",
        "is_primary",
    )

    search_fields = (
        "product__product_model__name",
        "product__variant",
        "colour",
    )

    list_editable = (
        "is_primary",
        "sort_order",
    )

    ordering = (
        "product",
        "sort_order",
        "-is_primary",
    )


# --------------------------------------------------
# Brand Document Admin
# --------------------------------------------------
@admin.register(BrandDocument)
class BrandDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "brand",
        "document_type",
        "version",
        "valid_from",
        "valid_until",
        "is_active",
    )

    list_filter = (
        "brand",
        "document_type",
        "is_active",
    )

    search_fields = (
        "title",
        "brand__name",
        "version",
    )

    list_editable = (
        "is_active",
    )

    ordering = (
        "-uploaded_at",
    )