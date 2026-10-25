from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from .models import Brand, Category, Product, ProductImage, ProductModel

MAX_UPLOAD_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


class ProductAdminForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=True,
        empty_label="Choose a category",
        label="Category",
    )
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.filter(is_active=True),
        required=True,
        empty_label="Choose a brand",
        label="Brand",
    )
    product_model = forms.ModelChoiceField(
        queryset=ProductModel.objects.select_related("brand", "category").all(),
        required=False,
        empty_label="Create standalone product",
        label="Linked model",
    )

    class Meta:
        model = Product
        fields = [
            "product_model",
            "brand",
            "category",
            "model",
            "variant",
            "description",
            "selling_price",
            "mrp",
            "colours",
            "specifications",
            "stock",
            "is_active",
        ]
        widgets = {
            "model": forms.TextInput(attrs={"placeholder": "Phone 3"}),
            "variant": forms.TextInput(attrs={"placeholder": "12GB + 256GB"}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "colours": forms.TextInput(attrs={"placeholder": "Black / White / Blue"}),
            "specifications": forms.Textarea(attrs={"rows": 8}),
        }

    def clean(self):
        cleaned_data = super().clean()
        product_model = cleaned_data.get("product_model")
        brand = cleaned_data.get("brand")
        category = cleaned_data.get("category")
        selling_price = cleaned_data.get("selling_price")
        mrp = cleaned_data.get("mrp")

        if product_model and brand and product_model.brand_id != brand.id:
            raise ValidationError(
                "The selected linked model belongs to a different brand."
            )

        if product_model and category and product_model.category_id != category.id:
            raise ValidationError(
                "The selected linked model belongs to a different category."
            )

        if selling_price is not None and mrp is not None and selling_price > mrp:
            raise ValidationError("Selling price cannot be higher than MRP.")

        if brand and category:
            cleaned_data["brand"] = brand
            cleaned_data["category"] = category

        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)
        category = self.cleaned_data.get("category")
        if category:
            product.category = category.name

        if commit:
            product.save()
        return product


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ["colour", "image", "is_primary", "sort_order"]
        widgets = {
            "colour": forms.TextInput(attrs={"placeholder": "Black"}),
        }

    def clean_image(self):
        uploaded_image = self.cleaned_data.get("image")

        if uploaded_image is None:
            return uploaded_image

        file_extension = uploaded_image.name.rsplit(".", 1)[-1].lower()
        if file_extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError(
                "Only JPG, JPEG, PNG and WebP images are supported."
            )

        if uploaded_image.size > MAX_UPLOAD_SIZE:
            raise ValidationError("Image file must be 5MB or smaller.")

        return uploaded_image


ProductImageFormSet = inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    extra=3,
    can_delete=True,
    fields=["colour", "image", "is_primary", "sort_order"],
)
