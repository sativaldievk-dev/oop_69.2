from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Category, Product, RegistrationCode, Review


User = get_user_model()


class ProductApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="product-tester",
            password="SecureTestPass!2026",
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(
            name="Категория",
            slug="test-category",
        )
        self.empty_category = Category.objects.create(
            name="Пустая категория",
            slug="empty-category",
        )
        self.product = Product.objects.create(
            category=self.category,
            name="Товар с отзывами",
            slug="product-with-reviews",
            price="100.00",
        )
        self.product_without_reviews = Product.objects.create(
            category=self.category,
            name="Товар без отзывов",
            slug="product-without-reviews",
            price="50.00",
        )
        Review.objects.create(
            product=self.product,
            author="Автор 1",
            rating=5,
            stars=4,
            comment="Хороший товар",
        )
        Review.objects.create(
            product=self.product,
            author="Автор 2",
            rating=5,
            stars=2,
            comment="Средний товар",
        )

    def test_models_keep_category_product_review_relations(self):
        self.assertEqual(self.product.category, self.category)
        self.assertEqual(self.category.products.count(), 2)
        self.assertEqual(self.product.reviews.count(), 2)
        self.assertEqual(
            set(self.product.reviews.values_list("comment", flat=True)),
            {"Хороший товар", "Средний товар"},
        )

    def test_review_stars_is_an_integer_from_one_through_five(self):
        field = Review._meta.get_field("stars")
        self.assertEqual(field.get_internal_type(), "IntegerField")

        for stars in range(1, 6):
            with self.subTest(stars=stars):
                review = Review(
                    product=self.product,
                    author="Проверка",
                    rating=3,
                    stars=stars,
                )
                review.full_clean()

        for stars in (0, 6):
            with self.subTest(stars=stars):
                review = Review(
                    product=self.product,
                    author="Проверка",
                    rating=3,
                    stars=stars,
                )
                with self.assertRaises(ValidationError):
                    review.full_clean()

    def test_products_reviews_endpoint_returns_nested_reviews_and_average(self):
        response = self.client.get("/api/v1/products/reviews/")

        self.assertEqual(response.status_code, 200)
        products = {item["slug"]: item for item in response.data}
        product = products["product-with-reviews"]
        self.assertEqual(product["rating"], 3.0)
        self.assertEqual(
            {review["text"] for review in product["reviews"]},
            {"Хороший товар", "Средний товар"},
        )
        self.assertEqual(
            {review["stars"] for review in product["reviews"]},
            {2, 4},
        )

    def test_product_without_reviews_has_null_rating_and_empty_reviews(self):
        response = self.client.get("/api/v1/products/reviews/")

        self.assertEqual(response.status_code, 200)
        product = next(
            item
            for item in response.data
            if item["slug"] == self.product_without_reviews.slug
        )
        self.assertIsNone(product["rating"])
        self.assertEqual(product["reviews"], [])

    def test_categories_endpoint_returns_product_counts(self):
        response = self.client.get("/api/v1/categories/")

        self.assertEqual(response.status_code, 200)
        categories = {item["slug"]: item for item in response.data}
        self.assertEqual(categories[self.category.slug]["products_count"], 2)
        self.assertEqual(categories[self.empty_category.slug]["products_count"], 0)

    def test_category_detail_still_returns_product_count(self):
        response = self.client.get(f"/api/v1/categories/{self.category.pk}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.category.pk)
        self.assertEqual(response.data["products_count"], 2)

    def test_category_crud_endpoints(self):
        response = self.client.post(
            "/api/v1/categories/",
            {
                "name": "Новая категория",
                "slug": "new-category",
                "description": "Описание категории",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        category_id = response.data["id"]
        self.assertTrue(
            any(
                item["id"] == category_id
                for item in self.client.get("/api/v1/categories/").data
            )
        )
        detail_url = f"/api/v1/categories/{category_id}/"
        self.assertEqual(self.client.get(detail_url).status_code, 200)

        response = self.client.put(
            detail_url,
            {
                "name": "Обновлённая категория",
                "slug": "updated-category",
                "description": "Новое описание",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Обновлённая категория")

        response = self.client.patch(
            detail_url,
            {"description": "Частично обновлённое описание"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["description"], "Частично обновлённое описание"
        )

        self.assertEqual(self.client.delete(detail_url).status_code, 204)
        self.assertEqual(self.client.get(detail_url).status_code, 404)

    def test_product_crud_endpoints(self):
        response = self.client.post(
            "/api/v1/products/",
            {
                "category": self.category.pk,
                "name": "Новый товар",
                "slug": "new-product",
                "description": "Описание товара",
                "price": "125.50",
                "stock": 7,
                "is_available": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        product_id = response.data["id"]
        self.assertTrue(
            any(
                item["id"] == product_id
                for item in self.client.get("/api/v1/products/").data
            )
        )
        detail_url = f"/api/v1/products/{product_id}/"
        self.assertEqual(self.client.get(detail_url).status_code, 200)

        response = self.client.put(
            detail_url,
            {
                "category": self.category.pk,
                "name": "Обновлённый товар",
                "slug": "updated-product",
                "description": "Новое описание",
                "price": "150.00",
                "stock": 9,
                "is_available": False,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Обновлённый товар")
        self.assertEqual(response.data["price"], "150.00")

        response = self.client.patch(
            detail_url,
            {"stock": 12},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["stock"], 12)

        self.assertEqual(self.client.delete(detail_url).status_code, 204)
        self.assertEqual(self.client.get(detail_url).status_code, 404)

    def test_review_crud_endpoints(self):
        response = self.client.post(
            "/api/v1/reviews/",
            {
                "product": self.product.pk,
                "author": "Новый автор",
                "rating": 4,
                "stars": 4,
                "comment": "Новый отзыв",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        review_id = response.data["id"]
        self.assertTrue(
            any(
                item["id"] == review_id
                for item in self.client.get("/api/v1/reviews/").data
            )
        )
        detail_url = f"/api/v1/reviews/{review_id}/"
        self.assertEqual(self.client.get(detail_url).status_code, 200)

        response = self.client.put(
            detail_url,
            {
                "product": self.product.pk,
                "author": "Обновлённый автор",
                "rating": 5,
                "stars": 5,
                "comment": "Обновлённый отзыв",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["author"], "Обновлённый автор")
        self.assertEqual(response.data["stars"], 5)

        response = self.client.patch(
            detail_url,
            {"comment": "Частично обновлённый отзыв"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["comment"], "Частично обновлённый отзыв")

        self.assertEqual(self.client.delete(detail_url).status_code, 204)
        self.assertEqual(self.client.get(detail_url).status_code, 404)

    def test_category_api_rejects_invalid_fields_and_duplicate_slugs(self):
        invalid_payloads = [
            {"name": "", "slug": "new-category"},
            {"name": "Категория", "slug": "not a valid slug"},
            {"name": "Категория", "slug": self.category.slug},
            {"name": ["не", "строка"], "slug": "new-category"},
        ]

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post(
                    "/api/v1/categories/", payload, format="json"
                )
                self.assertEqual(response.status_code, 400)

        self.assertEqual(Category.objects.count(), 2)

    def test_product_api_validates_field_types_values_and_category(self):
        valid_payload = {
            "category": self.category.pk,
            "name": "Проверяемый товар",
            "slug": "validated-product",
            "description": "Описание",
            "price": "10.00",
            "stock": 3,
            "is_available": True,
        }
        invalid_fields = [
            {"category": 999999},
            {"category": "не-id"},
            {"price": "0"},
            {"price": "-1.00"},
            {"price": "не цена"},
            {"stock": "много"},
            {"stock": -1},
            {"is_available": "неизвестно"},
        ]

        for invalid_field in invalid_fields:
            with self.subTest(invalid_field=invalid_field):
                payload = {**valid_payload, **invalid_field}
                response = self.client.post(
                    "/api/v1/products/", payload, format="json"
                )
                self.assertEqual(response.status_code, 400)

        self.assertEqual(Product.objects.count(), 2)

    def test_product_patch_rejects_invalid_values_without_changing_product(self):
        url = f"/api/v1/products/{self.product.pk}/"
        invalid_payloads = [
            {"price": "0"},
            {"stock": "не число"},
            {"category": 999999},
        ]

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.patch(url, payload, format="json")
                self.assertEqual(response.status_code, 400)

        self.product.refresh_from_db()
        self.assertEqual(str(self.product.price), "100.00")
        self.assertEqual(self.product.stock, 0)
        self.assertEqual(self.product.category, self.category)

    def test_review_api_validates_integer_ratings_and_product_relation(self):
        valid_payload = {
            "product": self.product.pk,
            "author": "Проверяющий",
            "rating": 4,
            "stars": 4,
            "comment": "Отзыв",
        }
        invalid_fields = [
            {"product": 999999},
            {"product": "не-id"},
            {"stars": 0},
            {"stars": 6},
            {"stars": "не число"},
            {"rating": 0},
            {"rating": 6},
            {"rating": "не число"},
            {"author": "   "},
        ]

        for invalid_field in invalid_fields:
            with self.subTest(invalid_field=invalid_field):
                payload = {**valid_payload, **invalid_field}
                response = self.client.post(
                    "/api/v1/reviews/", payload, format="json"
                )
                self.assertEqual(response.status_code, 400)

        self.assertEqual(Review.objects.count(), 2)


class UserAuthApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.registration_payload = {
            "username": "new-user",
            "email": "new-user@example.com",
            "password": "SecurePass!2026",
        }

    def register_user(self):
        return self.client.post(
            "/api/v1/users/register/",
            self.registration_payload,
            format="json",
        )

    def test_registration_creates_inactive_user_and_six_digit_code(self):
        response = self.register_user()

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="new-user")
        self.assertFalse(user.is_active)
        registration_code = RegistrationCode.objects.get(user=user)
        self.assertRegex(registration_code.code, r"^\d{6}$")
        self.assertEqual(response.data["email"], user.email)

    def test_confirmation_activates_user_and_rejects_invalid_code(self):
        self.register_user()
        user = User.objects.get(username="new-user")
        code = user.registration_code.code

        invalid_response = self.client.post(
            "/api/v1/users/confirm/",
            {
                "email": user.email,
                "code": "000000" if code != "000000" else "000001",
            },
            format="json",
        )
        self.assertEqual(invalid_response.status_code, 400)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

        response = self.client.post(
            "/api/v1/users/confirm/",
            {"email": user.email, "code": code},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertFalse(RegistrationCode.objects.filter(user=user).exists())
        repeated_response = self.client.post(
            "/api/v1/users/confirm/",
            {"email": user.email, "code": code},
            format="json",
        )
        self.assertEqual(repeated_response.status_code, 400)

    def test_jwt_login_is_blocked_until_user_is_confirmed(self):
        self.register_user()
        user = User.objects.get(username="new-user")
        login_payload = {
            "username": self.registration_payload["username"],
            "password": self.registration_payload["password"],
        }

        response = self.client.post("/api/v1/token/", login_payload, format="json")
        self.assertEqual(response.status_code, 401)

        self.client.post(
            "/api/v1/users/confirm/",
            {"email": user.email, "code": user.registration_code.code},
            format="json",
        )
        response = self.client.post("/api/v1/token/", login_payload, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )
        protected_response = self.client.get("/api/v1/categories/")
        self.assertEqual(protected_response.status_code, 200)

    def test_jwt_refresh_returns_a_new_access_token(self):
        user = User.objects.create_user(
            username="active-user",
            password="SecureTestPass!2026",
        )
        token_response = self.client.post(
            "/api/v1/token/",
            {"username": user.username, "password": "SecureTestPass!2026"},
            format="json",
        )

        self.assertEqual(token_response.status_code, 200)
        refresh_response = self.client.post(
            "/api/v1/token/refresh/",
            {"refresh": token_response.data["refresh"]},
            format="json",
        )

        self.assertEqual(refresh_response.status_code, 200)
        self.assertIn("access", refresh_response.data)

    def test_shop_api_requires_jwt_authentication(self):
        response = self.client.get("/api/v1/categories/")

        self.assertEqual(response.status_code, 401)
