import base64

from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from recipe.models import (Ingredient, Tag, Recipe, Subscribe, Favorite,
                           ShoppingList)
from users.models import User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super.to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    ingredients = IngredientSerializer(read_only=True, many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        fields = ('id', 'tags', 'author', 'ingredients', 'name', 'text',
                  'cooking_time', 'is_favorited', 'is_in_shopping_cart',
                  'image')
        model = Recipe

    def get_is_favorited(self, obj):
        request_user = self.context['request'].user
        return obj.favorite.filter(user=request_user.id).exists()

    def get_is_in_shopping_cart(self, obj):
        request_user = self.context['request'].user
        return obj.shopping_list.filter(user=request_user.id).exists()


class RecipeForSubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipe


class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  )
        model = User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('email', 'username', 'first_name', 'last_name', 'password')
        model = User
        lookup_field = 'username'

    def validate(self, data):
        if data.get('username') == 'me':
            raise serializers.ValidationError(
                'Использовать имя me в качестве username запрещено'
            )
        return data


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    class Meta:
        model = User
        fields = ('email', 'password')


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор вьюсета SubscribeViewSet."""
    author = UserReadSerializer(read_only=True)
    recipes = RecipeForSubscribeSerializer(read_only=True, many=True)

    def validate(self, data):
        follower = self.context['request'].user
        author_id = self.context['view'].kwargs.get('user_id')
        author = get_object_or_404(User, id=author_id)
        if self.context['request'].method == 'POST':
            if Subscribe.objects.filter(author=author, follower=follower).exists():
                raise serializers.ValidationError(
                    'Вы уже подписались на данного пользователя!'
                )
        return data

    class Meta:
        model = Subscribe
        fields = ('author', 'follower', 'recipes')
