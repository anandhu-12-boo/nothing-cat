import os
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import (
    Brand,
    Category,
    Product,
    ProductModel,
)


class CatalogueTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Test Phones",
            slug="test-phones",
            icon="📱",
            description="Nothing smartphones",
            sort_order=99,
            is_active=True,
        )

        self.brand = Brand.objects.create(
            name="Nothing",
            slug="nothing",
            logo_text="NOTHING",
            sort_order=99,
            is_active=True,
        )

        self.product_model = ProductModel.objects.create(
            category=self.category,
            brand=self.brand,
            name="Phone Test",
            slug="phone-test",
            description="Nothing test smartphone",
            colours="Black, White",
            specifications={
                "Display": "6.7-inch AMOLED",
                "Battery": "5000 mAh",
            },
            sort_order=1,
            is_active=True,
        )

        self.product = Product.objects.create(
            product_model=self.product_model,
            variant="8GB + 128GB",
            description="Nothing Phone Test 8GB/128GB",
            selling_price=Decimal("24999.00"),
            mrp=Decimal("27999.00"),
            colours="Black, White",
            specifications={
                "RAM": "8GB",
                "Storage": "128GB",
            },
            stock=10,
            is_active=True,
        )

    def test_home_page(self):
        response = self.client.get(
            reverse("index")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Phones",
        )

    def test_category_page_and_search(self):
        category_url = reverse(
            "category_detail",
            kwargs={
                "category_slug": self.category.slug,
            },
        )

        response = self.client.get(
            category_url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Phone Test",
        )

        search_response = self.client.get(
            category_url,
            {
                "q": "8GB",
            },
        )

        self.assertEqual(
            search_response.status_code,
            200,
        )

        self.assertContains(
            search_response,
            "Phone Test",
        )

    def test_model_detail_and_whatsapp(self):
        response = self.client.get(
            reverse(
                "model_detail",
                args=[self.product_model.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Phone Test",
        )

        self.assertContains(
            response,
            "8GB + 128GB",
        )

        self.assertContains(
            response,
            "Specifications",
        )

        self.assertContains(
            response,
            "Share on WhatsApp",
        )

        self.assertContains(
            response,
            "wa.me",
        )

    def test_old_product_url_redirects(self):
        response = self.client.get(
            reverse(
                "product_detail",
                args=[self.product.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            f"/models/{self.product_model.pk}/",
            response["Location"],
        )

        self.assertIn(
            f"variant={self.product.pk}",
            response["Location"],
        )

    def test_pwa_routes(self):
        manifest_response = self.client.get(
            reverse("manifest")
        )

        self.assertEqual(
            manifest_response.status_code,
            200,
        )

        self.assertEqual(
            manifest_response[
                "Content-Type"
            ],
            "application/manifest+json",
        )

        self.assertContains(
            manifest_response,
            "Nothing Product Catalogue",
        )

        service_worker_response = self.client.get(
            reverse("service_worker")
        )

        self.assertEqual(
            service_worker_response.status_code,
            200,
        )

        self.assertContains(
            service_worker_response,
            "CACHE_NAME",
        )

        self.assertContains(
            service_worker_response,
            "nothing-catalogue",
        )

    def test_excel_export(self):
        response = self.client.get(
            reverse("export_excel")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "spreadsheetml",
            response["Content-Type"],
        )

        self.assertIn(
            "attachment",
            response["Content-Disposition"],
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard/login/", response["Location"])

    def test_setup_admin_does_not_reset_password_unless_requested(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="heimglobal@gmail.com",
            email="heimglobal@gmail.com",
            password="ExistingPassword!123",
        )

        with patch.dict(os.environ, {"NOTHING_ADMIN_PASSWORD": "NewPassword!123"}):
            call_command("setup_admin", stdout=StringIO())

            user.refresh_from_db()
            self.assertTrue(user.check_password("ExistingPassword!123"))

            call_command(
                "setup_admin",
                "--reset-password",
                stdout=StringIO(),
            )

        user.refresh_from_db()
        self.assertTrue(user.check_password("NewPassword!123"))

    def test_dashboard_login_and_product_management(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="heimglobal@gmail.com",
            email="heimglobal@gmail.com",
            password="SecurePassword!123",
            is_staff=True,
            is_superuser=True,
        )
        self.assertTrue(user.is_staff)

        invalid = self.client.post(
            reverse("dashboard_login"),
            {
                "username": "heimglobal@gmail.com",
                "password": "wrong-password",
            },
            follow=True,
        )
        self.assertContains(invalid, "Invalid email or password")

        login_response = self.client.post(
            reverse("dashboard_login"),
            {
                "username": "heimglobal@gmail.com",
                "password": "SecurePassword!123",
            },
            follow=True,
        )
        self.assertRedirects(login_response, reverse("dashboard"))

        add_response = self.client.post(
            reverse("dashboard_product_add"),
            {
                "brand": self.brand.id,
                "category": self.category.id,
                "model": "Phone Pro",
                "variant": "12GB + 256GB",
                "description": "New flagship smartphone",
                "selling_price": "39999.00",
                "mrp": "42999.00",
                "colours": "Black / White",
                "stock": 8,
                "is_active": "on",
                "specifications": '{"RAM": "12GB", "Storage": "256GB"}',
            },
            follow=True,
        )
        self.assertContains(add_response, "was created successfully")

        public_response = self.client.get(reverse("index"))
        self.assertContains(public_response, "Phone Pro")

        product = Product.objects.get(model="Phone Pro", variant="12GB + 256GB")

        delete_response = self.client.post(
            reverse("dashboard_product_delete", args=[product.pk]),
            follow=True,
        )
        self.assertContains(delete_response, "was deleted successfully")
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())