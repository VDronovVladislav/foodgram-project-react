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


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class AddFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('recipe', 'user')

        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('recipe', 'user'),
                message='Вы уже добавили этот рецепт!'
            )
        ]


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
    # recipes = RecipeForSubscribeSerializer(read_only=True, many=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = ShortRecipeSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscribe.objects.filter(follower=request.user,
                                        author=obj).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class AddSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления подписки."""
    class Meta:
        model = Subscribe
        fields = ('author', 'follower')

        validators = [ 
            UniqueTogetherValidator(
                queryset=Subscribe.objects.all(),
                fields=('follower', 'author'),
                message='Вы уже подписались на данного пользователя!'
            )
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    author = SubscribeSerializer()

    class Meta:
        model = Subscribe
        fields = ('author',)


class AddShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingList
        fields = ('user', 'recipe')

        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingList.objects.all(),
                fields=('recipe', 'user'),
                message='Вы уже добавили этот рецепт в список покупок!'
            )
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingList
        fields = ('recipe', 'user')