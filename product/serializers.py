from decimal import Decimal

from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Category, Product, RegistrationCode, Review


User = get_user_model()


class RegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "Этот адрес электронной почты уже используется."
            )
        return value

    def validate(self, attrs):
        user = User(username=attrs["username"], email=attrs["email"])
        try:
            password_validation.validate_password(attrs["password"], user=user)
        except ValidationError as error:
            raise serializers.ValidationError({"password": error.messages}) from error
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data["username"],
                email=validated_data["email"],
                password=validated_data["password"],
                is_active=False,
            )
            registration_code = RegistrationCode.objects.create(user=user)
            send_mail(
                subject="Подтверждение регистрации",
                message=(
                    f"Ваш код подтверждения: {registration_code.code}\n"
                    "Введите его в запросе подтверждения регистрации."
                ),
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )
        return user


class ConfirmRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.RegexField(regex=r"^\d{6}$", max_length=6, min_length=6)

    def validate(self, attrs):
        try:
            attrs["user"] = User.objects.get(
                email__iexact=attrs["email"],
                is_active=False,
                registration_code__code=attrs["code"],
            )
        except User.DoesNotExist as error:
            raise serializers.ValidationError(
                {"code": "Неверный код или пользователь уже подтверждён."}
            ) from error
        return attrs


class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
        extra_kwargs = {
            "price": {"min_value": Decimal("0.01")},
        }


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
