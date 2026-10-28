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
