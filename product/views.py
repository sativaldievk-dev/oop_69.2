from django.db import transaction
from django.db.models import Avg, Count
from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Product, Review
from .serializers import (
    CategorySerializer,
    ConfirmRegistrationSerializer,
    ProductReviewsSerializer,
    ProductSerializer,
    RegistrationSerializer,
    ReviewSerializer,
)


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "username": user.username,
                "email": user.email,
                "detail": "Код подтверждения отправлен на электронную почту.",
            },
            status=status.HTTP_201_CREATED,
        )


class ConfirmRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ConfirmRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        with transaction.atomic():
            user.is_active = True
            user.save(update_fields=["is_active"])
            user.registration_code.delete()
        return Response({"detail": "Аккаунт подтверждён."}, status=status.HTTP_200_OK)


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
