from django.db.models import Avg, Count
from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import Category, Product, Review
from .serializers import (
    CategorySerializer,
    ProductReviewsSerializer,
    ProductSerializer,
    ReviewSerializer,
)


class CategoryListView(ListAPIView):
    queryset = Category.objects.annotate(products_count=Count("products"))
    serializer_class = CategorySerializer


class CategoryDetailView(RetrieveAPIView):
    queryset = Category.objects.annotate(products_count=Count("products"))
    serializer_class = CategorySerializer


class ProductListView(ListAPIView):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer


class ProductDetailView(RetrieveAPIView):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer


class ProductReviewsListView(ListAPIView):
    queryset = Product.objects.annotate(rating=Avg("reviews__stars")).prefetch_related(
        "reviews"
    )
    serializer_class = ProductReviewsSerializer


class ReviewListView(ListAPIView):
    queryset = Review.objects.select_related("product").all()
    serializer_class = ReviewSerializer


class ReviewDetailView(RetrieveAPIView):
    queryset = Review.objects.select_related("product").all()
    serializer_class = ReviewSerializer
