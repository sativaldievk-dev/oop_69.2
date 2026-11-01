from django.db.models import Avg, Count
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)

from .models import Category, Product, Review
from .serializers import (
    CategorySerializer,
    ProductReviewsSerializer,
    ProductSerializer,
    ReviewSerializer,
)


class CategoryListView(ListCreateAPIView):
    queryset = Category.objects.annotate(products_count=Count("products"))
    serializer_class = CategorySerializer


class CategoryDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.annotate(products_count=Count("products"))
    serializer_class = CategorySerializer


class ProductListView(ListCreateAPIView):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer


class ProductDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer


class ProductReviewsListView(ListAPIView):
    queryset = Product.objects.annotate(rating=Avg("reviews__stars")).prefetch_related(
        "reviews"
    )
    serializer_class = ProductReviewsSerializer


class ReviewListView(ListCreateAPIView):
    queryset = Review.objects.select_related("product").all()
    serializer_class = ReviewSerializer


class ReviewDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.select_related("product").all()
    serializer_class = ReviewSerializer
