

from types import SimpleNamespace
from urllib.parse import quote, urlencode

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Count, Max, Prefetch, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from .forms import ProductAdminForm, ProductImageFormSet
from .models import (
    Brand,
    BrandDocument,
    Category,
    Product,
    ProductImage,
    ProductModel,
    ProductModelImage,
)


# Only Nothing products will appear in the application.
NOTHING_BRANDS = ("nothing",)


def _product_image_or_placeholder(product):
    first_image = product.images.first()
    if first_image and first_image.image:
        return first_image.image.url
    return ""


def _standalone_product_card(product):
    image = product.images.first() if hasattr(product, "images") else None
    category = SimpleNamespace(name=product.category or "Products")
    model = SimpleNamespace(
        pk=product.pk,
        name=product.model,
        category=category,
    )
    return {
        "model": model,
        "variant": product,
        "image": image,
        "variant_count": 1,
        "is_standalone": True,
    }


def dashboard_login(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_active:
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next") or reverse("dashboard")
            return redirect(next_url)

        messages.error(request, "Invalid email or password.")

    form_action = reverse("dashboard_login")
    next_url = request.GET.get("next", "")
    return render(
        request,
        "catalogue/dashboard_login.html",
        {"form_action": form_action, "next_url": next_url},
    )


@login_required
@staff_member_required
def dashboard_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("dashboard_login")


@login_required
@staff_member_required
def dashboard_home(request):
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    total_categories = Category.objects.filter(is_active=True).count()
    total_brands = Brand.objects.filter(is_active=True).count()
    recent_products = Product.objects.select_related("brand", "product_model").prefetch_related("images").order_by("-updated_at")[:5]

    return render(
        request,
        "catalogue/dashboard_home.html",
        {
            "total_products": total_products,
            "active_products": active_products,
            "total_categories": total_categories,
            "total_brands": total_brands,
            "recent_products": recent_products,
        },
    )


@login_required
@staff_member_required
def dashboard_products(request):
    queryset = (
        Product.objects.select_related("brand", "product_model", "product_model__category")
        .prefetch_related("images")
        .order_by("-updated_at", "-id")
    )

    search_term = request.GET.get("q", "").strip()
    brand_filter = request.GET.get("brand", "")
    category_filter = request.GET.get("category", "")
    status_filter = request.GET.get("status", "")

    if search_term:
        queryset = queryset.filter(
            Q(brand__name__icontains=search_term)
            | Q(model__icontains=search_term)
            | Q(product_model__name__icontains=search_term)
            | Q(variant__icontains=search_term)
            | Q(description__icontains=search_term)
            | Q(category__icontains=search_term)
        )

    if brand_filter:
        queryset = queryset.filter(brand_id=brand_filter)

    if category_filter:
        queryset = queryset.filter(product_model__category_id=category_filter)

    if status_filter in {"active", "inactive"}:
        queryset = queryset.filter(is_active=(status_filter == "active"))

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "catalogue/dashboard_products.html",
        {
            "page_obj": page_obj,
            "search_term": search_term,
            "brand_filter": brand_filter,
            "category_filter": category_filter,
            "status_filter": status_filter,
            "brands": Brand.objects.filter(is_active=True).order_by("name"),
            "categories": Category.objects.filter(is_active=True).order_by("name"),
        },
    )


@login_required
@staff_member_required
def dashboard_product_add(request):
    if request.method == "POST":
        form = ProductAdminForm(request.POST, request.FILES)
        has_image_form_data = any(
            key.startswith("form-") or key.startswith("image-")
            for key in request.POST.keys()
        )
        formset = ProductImageFormSet(request.POST, request.FILES, instance=Product())

        formset_is_valid = True
        if has_image_form_data:
            formset_is_valid = formset.is_valid()

        if form.is_valid() and formset_is_valid:
            product = form.save(commit=False)

            try:
                product.save()
            except IntegrityError:
                form.add_error(
                    None,
                    "A product with the same brand, model and variant already exists.",
                )
                return render(
                    request,
                    "catalogue/dashboard_product_add.html",
                    {"form": form, "formset": formset},
                )

            formset.instance = product
            formset.save()
            messages.success(
                request,
                f'Product "{product}" was created successfully.',
            )
            return redirect("dashboard_products")
    else:
        form = ProductAdminForm()
        formset = ProductImageFormSet(instance=Product())

    return render(
        request,
        "catalogue/dashboard_product_add.html",
        {"form": form, "formset": formset},
    )


@login_required
@staff_member_required
def dashboard_product_delete(request, pk):
    product = get_object_or_404(Product.objects.select_related("brand", "product_model"), pk=pk)

    if request.method == "POST":
        try:
            product.delete()
        except Exception:
            messages.error(request, "This product could not be deleted because it is still referenced by related records.")
            return redirect("dashboard_products")

        messages.success(request, f'Product "{product}" was deleted successfully.')
        return redirect("dashboard_products")

    return render(request, "catalogue/dashboard_product_delete.html", {"product": product})


def home(request):
    """
    Display every active category.

    Product/model counts include only active Nothing products.
    Empty categories are still displayed.
    """
    query = request.GET.get("q", "").strip()

    categories = list(
        Category.objects.filter(
            is_active=True,
        )
        .annotate(
            model_count=Count(
                "product_models",
                filter=Q(
                    product_models__is_active=True,
                    product_models__brand__is_active=True,
                    product_models__brand__slug__in=NOTHING_BRANDS,
                ),
                distinct=True,
            ),
            product_count=Count(
                "product_models__variants",
                filter=Q(
                    product_models__is_active=True,
                    product_models__variants__is_active=True,
                    product_models__brand__is_active=True,
                    product_models__brand__slug__in=NOTHING_BRANDS,
                ),
                distinct=True,
            ),
        )
        .order_by(
            "sort_order",
            "name",
        )
    )

    model_images = ProductModelImage.objects.order_by(
        "-is_primary",
        "sort_order",
        "id",
    )

    product_images = ProductImage.objects.order_by(
        "-is_primary",
        "sort_order",
        "id",
    )

    active_variants = (
        Product.objects.filter(is_active=True)
        .prefetch_related(
            Prefetch("images", queryset=product_images)
        )
        .order_by("selling_price", "variant", "id")
    )

    models = (
        ProductModel.objects.filter(
            is_active=True,
            brand__is_active=True,
            brand__slug__in=NOTHING_BRANDS,
            category__is_active=True,
            variants__is_active=True,
        )
        .select_related("brand", "category")
        .prefetch_related(
            Prefetch("images", queryset=model_images),
            Prefetch("variants", queryset=active_variants),
        )
        .distinct()
    )

    if query:
        models = models.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(colours__icontains=query)
            | Q(category__name__icontains=query)
            | Q(variants__variant__icontains=query)
            | Q(variants__description__icontains=query)
            | Q(variants__colours__icontains=query)
        ).distinct()

    models = list(models.order_by("-updated_at", "name")[:6])

    def model_card(product_model):
        variants = list(product_model.variants.all())
        first_variant = variants[0] if variants else None
        shared_images = list(product_model.images.all())
        image = shared_images[0] if shared_images else None

        if image is None and first_variant:
            variant_images = list(first_variant.images.all())
            image = variant_images[0] if variant_images else None

        return {
            "model": product_model,
            "variant": first_variant,
            "image": image,
            "variant_count": len(variants),
        }

    recent_models = [model_card(item) for item in models]

    standalone_products = (
        Product.objects.filter(
            is_active=True,
            product_model__isnull=True,
            brand__is_active=True,
            brand__slug__in=NOTHING_BRANDS,
        )
        .select_related("brand")
        .prefetch_related("images")
        .order_by("-updated_at", "model")
    )

    if query:
        standalone_products = standalone_products.filter(
            Q(model__icontains=query)
            | Q(description__icontains=query)
            | Q(variant__icontains=query)
            | Q(colours__icontains=query)
            | Q(category__icontains=query)
        )

    recent_models.extend(
        _standalone_product_card(product)
        for product in standalone_products[:6]
    )
    recent_models = sorted(
        recent_models,
        key=lambda item: getattr(item["variant"], "updated_at", item["model"].pk),
        reverse=True,
    )

    category_cards = []
    for category in categories:
        preview = next(
            (
                item
                for item in recent_models
                if not item.get("is_standalone")
                and getattr(item["model"], "category_id", None) == category.id
                and item["image"] is not None
            ),
            None,
        )

        if preview is None:
            preview_model = (
                ProductModel.objects.filter(
                    category=category,
                    is_active=True,
                    brand__is_active=True,
                    brand__slug__in=NOTHING_BRANDS,
                    variants__is_active=True,
                )
                .select_related("brand", "category")
                .prefetch_related(
                    Prefetch("images", queryset=model_images),
                    Prefetch("variants", queryset=active_variants),
                )
                .distinct()
                .order_by("sort_order", "name")
                .first()
            )
            preview = model_card(preview_model) if preview_model else None

        category_cards.append({
            "category": category,
            "image": preview["image"] if preview else None,
        })
    hero_image = (
        ProductModelImage.objects.filter(
            product_model__category__slug="phones",
            product_model__is_active=True,
            product_model__brand__is_active=True,
            product_model__brand__slug__in=NOTHING_BRANDS,
        )
        .select_related("product_model")
        .order_by(
            "-product_model__updated_at",
            "-is_primary",
            "sort_order",
            "id",
        )
        .first()
    )

    total_models = sum(category.model_count for category in categories)
    total_variants = sum(category.product_count for category in categories)
    latest_updated = Product.objects.filter(
        is_active=True,
        product_model__brand__slug__in=NOTHING_BRANDS,
    ).aggregate(latest=Max("updated_at"))["latest"]

    return render(
        request,
        "catalogue/index.html",
        {
            "categories": categories,
            "category_cards": category_cards,
            "total_models": total_models,
            "total_variants": total_variants,
            "recent_models": recent_models,
            "hero_image": hero_image,
            "latest_updated": latest_updated,
            "query": query,
        },
    )

def category_detail(request, category_slug):
    """
    Display active Nothing models in the selected category.

    The category page loads both:
    - shared ProductModel images
    - variant-specific Product images
    """
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_active=True,
    )

    query = request.GET.get(
        "q",
        "",
    ).strip()

    # Images shared by all variants of a model.
    shared_model_images = ProductModelImage.objects.order_by(
        "-is_primary",
        "sort_order",
        "id",
    )

    # Images belonging only to an individual variant.
    variant_images = ProductImage.objects.order_by(
        "-is_primary",
        "sort_order",
        "id",
    )

    variants = (
        Product.objects.filter(
            is_active=True,
            product_model__brand__slug__in=NOTHING_BRANDS,
        )
        .prefetch_related(
            Prefetch(
                "images",
                queryset=variant_images,
            )
        )
        .order_by(
            "selling_price",
            "variant",
            "id",
        )
    )

    product_models = (
        ProductModel.objects.filter(
            category=category,
            is_active=True,
            brand__is_active=True,
            brand__slug__in=NOTHING_BRANDS,
            variants__is_active=True,
        )
        .select_related(
            "brand",
            "category",
        )
        .prefetch_related(
            Prefetch(
                "images",
                queryset=shared_model_images,
            ),
            Prefetch(
                "variants",
                queryset=variants,
            ),
        )
        .distinct()
        .order_by(
            "sort_order",
            "name",
        )
    )

    if query:
        product_models = product_models.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(colours__icontains=query)
            | Q(variants__variant__icontains=query)
            | Q(variants__description__icontains=query)
            | Q(variants__colours__icontains=query)
        ).distinct()

    return render(
        request,
        "catalogue/category.html",
        {
            "category": category,
            "product_models": product_models,
            "query": query,
        },
    )

def model_detail(request, pk):
    """
    Display one Nothing product model.

    Variant-specific images are used when available.
    Otherwise, images shared by ProductModel are used.
    """
    shared_image_queryset = ProductModelImage.objects.order_by(
        "-is_primary",
        "sort_order",
        "id",
    )

    product_model = get_object_or_404(
        ProductModel.objects.select_related(
            "brand",
            "category",
        ).prefetch_related(
            Prefetch(
                "images",
                queryset=shared_image_queryset,
            )
        ),
        pk=pk,
        is_active=True,
        brand__is_active=True,
        brand__slug__in=NOTHING_BRANDS,
    )

    variant_image_queryset = ProductImage.objects.order_by(
        "-is_primary",
        "sort_order",
        "id",
    )

    variants = list(
        product_model.variants.filter(
            is_active=True,
        )
        .prefetch_related(
            Prefetch(
                "images",
                queryset=variant_image_queryset,
            )
        )
        .order_by(
            "selling_price",
            "variant",
            "id",
        )
    )

    # --------------------------------------------------
    # Select the requested RAM/storage variant
    # --------------------------------------------------
    requested_variant_id = request.GET.get(
        "variant",
        "",
    ).strip()

    selected_variant = None

    if requested_variant_id:
        selected_variant = next(
            (
                variant
                for variant in variants
                if str(variant.pk) == requested_variant_id
            ),
            None,
        )

    if selected_variant is None and variants:
        selected_variant = variants[0]

    # --------------------------------------------------
    # Images shared by every variant
    # --------------------------------------------------
    shared_images = list(
        product_model.images.all()
    )

    default_shared_image = (
        shared_images[0]
        if shared_images
        else None
    )

    # --------------------------------------------------
    # Create RAM/storage variant options
    # --------------------------------------------------
    variant_options = []

    # Read the currently selected colour from the URL.
    requested_colour_for_variants = request.GET.get(
        "colour",
        "",
    ).strip()

    for variant in variants:
        specific_images = list(
            variant.images.all()
        )

        # Combine variant-specific and shared model images.
        candidate_images = specific_images + shared_images

        option_image = None

        # When a colour is selected, use that colour image
        # for every RAM/storage variant thumbnail.
        if requested_colour_for_variants:
            option_image = next(
                (
                    product_image
                    for product_image in candidate_images
                    if (
                               product_image.colour or ""
                       ).strip().lower()
                       == requested_colour_for_variants.lower()
                ),
                None,
            )

        # If no colour is selected or no matching image exists,
        # use the primary shared model image.
        if option_image is None:
            option_image = default_shared_image

        # Preserve the selected colour when changing variants.
        variant_parameters = {
            "variant": variant.pk,
        }

        if requested_colour_for_variants:
            variant_parameters["colour"] = (
                requested_colour_for_variants
            )

        variant_url = (
                reverse(
                    "model_detail",
                    kwargs={
                        "pk": product_model.pk,
                    },
                )
                + "?"
                + urlencode(variant_parameters)
        )
        variant_options.append({
            "product": variant,
            "image": option_image,
            "url": variant_url,
            "is_selected": (
                    selected_variant is not None
                    and selected_variant.pk == variant.pk
            ),
        })

    # --------------------------------------------------
    # Choose images for the selected variant
    # --------------------------------------------------
    # --------------------------------------------------
    # Choose images for the selected variant
    # --------------------------------------------------
    selected_variant_images = []

    if selected_variant:
        selected_variant_images = list(
            selected_variant.images.all()
        )

    # Combine variant-specific images and model-level images.
    # Model-level images contain the available colour images,
    # so they must not be removed when a variant has an image.
    available_images = []
    seen_image_names = set()

    for product_image in selected_variant_images + shared_images:
        if not product_image.image:
            continue

        image_name = product_image.image.name

        if image_name not in seen_image_names:
            available_images.append(product_image)
            seen_image_names.add(image_name)

    # --------------------------------------------------
    # Build available colour list
    # --------------------------------------------------
    colour_names = []

    def add_colour(colour):
        cleaned_colour = str(colour).strip()

        if not cleaned_colour:
            return

        already_exists = any(
            existing.lower() == cleaned_colour.lower()
            for existing in colour_names
        )

        if not already_exists:
            colour_names.append(cleaned_colour)

    # First use colours entered on the selected variant.
    if selected_variant and selected_variant.colours:
        normalised_colours = (
            selected_variant.colours
            .replace("|", ",")
            .replace("/", ",")
        )

        for colour in normalised_colours.split(","):
            add_colour(colour)

    # Otherwise, use colours shared by the model.
    if product_model.colours:
        normalised_model_colours = (
            product_model.colours
            .replace("|", ",")
            .replace("/", ",")
        )

        for colour in normalised_model_colours.split(","):
            add_colour(colour)

    # Also include colours assigned to images.
    for product_image in available_images:
        add_colour(product_image.colour)

    # Images without a colour still need to be displayed.
    if not colour_names and available_images:
        colour_names.append("Default")

    requested_colour = request.GET.get(
        "colour",
        "",
    ).strip()

    selected_colour = None

    if requested_colour:
        selected_colour = next(
            (
                colour
                for colour in colour_names
                if colour.lower()
                == requested_colour.lower()
            ),
            None,
        )

    if selected_colour is None and colour_names:
        selected_colour = colour_names[0]

    # --------------------------------------------------
    # Build clickable colour options
    # --------------------------------------------------
    colour_options = []

    for colour in colour_names:
        matching_images = []

        for product_image in available_images:
            image_colour = (
                product_image.colour or ""
            ).strip()

            if colour == "Default":
                matching_images.append(product_image)

            elif image_colour.lower() == colour.lower():
                matching_images.append(product_image)

        # If the image has no colour label, allow it to
        # represent all colours.
        if not matching_images:
            unlabelled_images = [
                product_image
                for product_image in available_images
                if not (
                    product_image.colour or ""
                ).strip()
            ]

            matching_images = unlabelled_images

        representative_image = (
            matching_images[0]
            if matching_images
            else default_shared_image
        )

        colour_url = (
            reverse(
                "model_detail",
                kwargs={
                    "pk": product_model.pk,
                },
            )
            + "?"
            + urlencode({
                "variant": (
                    selected_variant.pk
                    if selected_variant
                    else ""
                ),
                "colour": colour,
            })
        )

        colour_options.append({
            "name": colour,
            "image": representative_image,
            "url": colour_url,
            "is_selected": (
                selected_colour is not None
                and selected_colour.lower()
                == colour.lower()
            ),
        })

    # --------------------------------------------------
    # Images displayed in the main gallery
    # --------------------------------------------------
    selected_images = []

    if selected_colour:
        for product_image in available_images:
            image_colour = (
                product_image.colour or ""
            ).strip()

            if selected_colour == "Default":
                selected_images.append(product_image)

            elif image_colour.lower() == selected_colour.lower():
                selected_images.append(product_image)

    # When colour matching finds nothing, display all
    # available shared/variant images.
    if not selected_images:
        selected_images = available_images

    # --------------------------------------------------
    # Specifications and prices
    # --------------------------------------------------
    specifications = dict(
        product_model.specifications or {}
    )

    if selected_variant:
        specifications.update(
            dict(
                selected_variant.specifications or {}
            )
        )

    savings = 0
    discount_percentage = 0

    if selected_variant:
        savings = max(
            selected_variant.mrp
            - selected_variant.selling_price,
            0,
        )

        if selected_variant.mrp:
            discount_percentage = round(
                savings
                / selected_variant.mrp
                * 100
            )

    # --------------------------------------------------
    # Documents
    # --------------------------------------------------
    documents = BrandDocument.objects.filter(
        brand=product_model.brand,
        is_active=True,
    ).order_by(
        "-uploaded_at",
    )

    # --------------------------------------------------
    # WhatsApp link
    # --------------------------------------------------
    share_url = request.build_absolute_uri()

    message_parts = [
        f"{product_model.brand.name} "
        f"{product_model.name}",
    ]

    if selected_variant:
        if selected_variant.variant:
            message_parts.append(
                f"Variant: {selected_variant.variant}"
            )

        if selected_colour:
            message_parts.append(
                f"Colour: {selected_colour}"
            )

        message_parts.append(
            f"MOP: "
            f"₹{selected_variant.selling_price:,.0f}"
        )

        message_parts.append(
            f"MRP: "
            f"₹{selected_variant.mrp:,.0f}"
        )

        if savings:
            message_parts.append(
                f"You save: ₹{savings:,.0f}"
            )

    message_parts.append(
        f"View complete details: {share_url}"
    )

    whatsapp_url = (
        "https://wa.me/?text="
        + quote("\n".join(message_parts))
    )

    return render(
        request,
        "catalogue/model_detail.html",
        {
            "product_model": product_model,
            "variants": variants,
            "variant_options": variant_options,
            "selected_variant": selected_variant,
            "colour_options": colour_options,
            "selected_colour": selected_colour,
            "images": selected_images,
            "specifications": specifications,
            "savings": savings,
            "discount_percentage": discount_percentage,
            "documents": documents,
            "whatsapp_url": whatsapp_url,
        },
    )

def legacy_product_detail(request, pk):
    """
    Redirect an old individual Product URL to the new
    ProductModel details page.

    Example:
    /products/18/ -> /models/5/?variant=18
    """
    product = get_object_or_404(
        Product.objects.select_related(
            "product_model",
            "product_model__brand",
        ),
        pk=pk,
        is_active=True,
        product_model__brand__slug__in=NOTHING_BRANDS,
    )

    if not product.product_model_id:
        return redirect("index")

    model_url = reverse(
        "model_detail",
        kwargs={
            "pk": product.product_model_id,
        },
    )

    return redirect(
        f"{model_url}?variant={product.pk}"
    )


def export_excel(request):
    """
    Export all active Nothing variants to an Excel file.
    """
    products = (
        Product.objects.filter(
            is_active=True,
            product_model__is_active=True,
            product_model__brand__is_active=True,
            product_model__brand__slug__in=NOTHING_BRANDS,
        )
        .select_related(
            "product_model",
            "product_model__brand",
            "product_model__category",
        )
        .order_by(
            "product_model__category__sort_order",
            "product_model__name",
            "selling_price",
            "variant",
        )
    )

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Nothing Catalogue"

    headers = [
        "Category",
        "Brand",
        "Model",
        "Variant",
        "Description",
        "Colours",
        "MOP",
        "MRP",
        "Savings",
        "Stock",
        "Last Updated",
    ]

    worksheet.append(headers)

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="111827",
    )

    header_font = Font(
        color="FFFFFF",
        bold=True,
    )

    for cell in worksheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    for product in products:
        product_model = product.product_model

        savings = max(
            product.mrp - product.selling_price,
            0,
        )

        description = (
            product.description
            or product_model.description
            or ""
        )

        colours = (
            product.colours
            or product_model.colours
            or ""
        )

        updated_at = ""

        if product.updated_at:
            updated_at = product.updated_at.strftime(
                "%d-%m-%Y %I:%M %p"
            )

        worksheet.append([
            product_model.category.name,
            product_model.brand.name,
            product_model.name,
            product.variant or "",
            description,
            colours,
            float(product.selling_price),
            float(product.mrp),
            float(savings),
            product.stock,
            updated_at,
        ])

    for column in ("G", "H", "I"):
        for cell in worksheet[column][1:]:
            cell.number_format = '₹#,##0.00'

    column_widths = {
        "A": 18,
        "B": 16,
        "C": 26,
        "D": 20,
        "E": 45,
        "F": 30,
        "G": 15,
        "H": 15,
        "I": 15,
        "J": 12,
        "K": 23,
    }

    for column, width in column_widths.items():
        worksheet.column_dimensions[column].width = width

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions

    response = HttpResponse(
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )

    response["Content-Disposition"] = (
        'attachment; filename="nothing_product_catalogue.xlsx"'
    )

    workbook.save(response)

    return response


def manifest(request):
    """
    Return the installable PWA manifest.
    """
    data = {
        "name": "Nothing Product Catalogue",
        "short_name": "Nothing",
        "description": (
            "Nothing phones, audio products, accessories, "
            "prices and specifications."
        ),
        "id": "/",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait-primary",
        "background_color": "#ffffff",
        "theme_color": "#111111",
        "lang": "en-IN",
        "icons": [
            {
                "src": "/static/icons/icon.svg",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any",
            }
        ],
    }

    return JsonResponse(
        data,
        content_type="application/manifest+json",
    )


def service_worker(request):
    """
    Return the JavaScript service worker used by the PWA.
    """
    javascript = """
const CACHE_NAME = "nothing-catalogue-v6";

const STATIC_FILES = [
    "/",
    "/manifest.json",
    "/static/css/app.css",
    "/static/icons/icon.svg"
];

self.addEventListener("install", function (event) {
    event.waitUntil(
        caches.open(CACHE_NAME).then(function (cache) {
            return cache.addAll(STATIC_FILES);
        })
    );

    self.skipWaiting();
});

self.addEventListener("activate", function (event) {
    event.waitUntil(
        caches.keys().then(function (cacheNames) {
            return Promise.all(
                cacheNames
                    .filter(function (cacheName) {
                        return cacheName !== CACHE_NAME;
                    })
                    .map(function (cacheName) {
                        return caches.delete(cacheName);
                    })
            );
        })
    );

    self.clients.claim();
});

self.addEventListener("fetch", function (event) {
    if (event.request.method !== "GET") {
        return;
    }

    const requestUrl = new URL(event.request.url);

    if (
        requestUrl.origin !== self.location.origin ||
        requestUrl.pathname.startsWith("/admin/") ||
        requestUrl.pathname.startsWith("/media/") ||
        requestUrl.pathname.startsWith("/export/")
    ) {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then(function (networkResponse) {
                if (!networkResponse || !networkResponse.ok) {
                    return networkResponse;
                }

                const responseCopy = networkResponse.clone();

                caches.open(CACHE_NAME).then(function (cache) {
                    cache.put(event.request, responseCopy);
                });

                return networkResponse;
            })
            .catch(function () {
                return caches.match(event.request).then(
                    function (cachedResponse) {
                        if (cachedResponse) {
                            return cachedResponse;
                        }

                        if (
                            event.request.mode === "navigate"
                        ) {
                            return caches.match("/");
                        }

                        return new Response(
                            "Offline",
                            {
                                status: 503,
                                statusText: "Offline",
                            }
                        );
                    }
                );
            })
    );
});
"""

    response = HttpResponse(
        javascript,
        content_type="application/javascript",
    )

    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = (
        "no-cache, no-store, must-revalidate"
    )

    return response
