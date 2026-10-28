from rest_framework import serializers

from .models import Category, Product, Review


class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = "__all__"


class ProductReviewSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source="comment", read_only=True)

    class Meta:
        model = Review
        fields = ("id", "author", "text", "stars", "created_at")


class ProductReviewsSerializer(serializers.ModelSerializer):
    reviews = ProductReviewSerializer(many=True, read_only=True)
    rating = serializers.FloatField(read_only=True, allow_null=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "price",
            "stock",
            "is_available",
            "created_at",
            "category",
            "reviews",
            "rating",
        )
