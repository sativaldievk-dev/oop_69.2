from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Category, Product, Review


class ProductApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
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
