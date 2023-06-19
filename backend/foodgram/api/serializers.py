import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipe.models import (Ingredient, Tag, Recipe, Subscribe, Favorite,
                           ShoppingList, IngredientInRecipe)
from users.models import User
from .validators import CustomValidationException


class Base64ImageField(serializers.ImageField):
    """Сериализатор сохранения картинок."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор чтения ингердиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    """Сериалзиатор создания ингредиентов в рецептах."""
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = IngredientInRecipe
        fields = ('recipe', 'id', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Сериазизатор тегов."""
    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""
    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class UserReadSerializer(serializers.ModelSerializer):
    """Сериализатор просмотра пользователей."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')
        model = User

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscribe.objects.filter(follower=request.user,
                                        author=obj).exists()


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор просмотра рецептов."""
    tags = TagSerializer(read_only=True, many=True)
    ingredients = IngredientInRecipeSerializer(many=True, source='recipe')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = UserReadSerializer()
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


class RecipePostSerializer(serializers.ModelSerializer):
    """Сериализатор созданя рецептов."""
    image = Base64ImageField()
    ingredients = IngredientInRecipeCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    author = serializers.CurrentUserDefault()

    class Meta:
        fields = ('ingredients', 'tags', 'name', 'text', 'cooking_time',
                  'image')
        model = Recipe

        validators = [
            UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=('name',),
                message='Вы уже опубликовали этот рецепт!'
            )
        ]

    def validate_ingredients(self, data):
        ingredients = self.initial_data.get('ingredients')
        if 'ingredients' not in self.initial_data:
            raise CustomValidationException('Добавьте ингредиенты!')
        ingredient_list = []
        for ingredient in ingredients:
            if ingredient in ingredient_list:
                raise CustomValidationException(
                    'Ингредиенты не должны повторяться!'
                )
            ingredient_list.append(ingredient)
        if int(ingredient['amount']) < 1:
            raise CustomValidationException(
                'Ингредиент не может быть нулевым или отрицательным!'
            )
        return data

    def validate_cooking_time(self, data):
        cooking_time = self.initial_data.get('cooking_time')
        if int(cooking_time) <= 0:
            raise CustomValidationException(
                'Время приготовления не может быть нулевым или отрицательным!'
            )
        return data

    def ingredient_creation(self, recipe, ingredients):
        creation = [
            IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ]
        IngredientInRecipe.objects.bulk_create(creation)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.ingredient_creation(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        if tags is not None:
            instance.tags.set(tags)
        if ingredients is not None:
            instance.ingredients.clear()
        self.ingredient_creation(instance, ingredients)
        return super().update(instance, validated_data)


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Мини-сериализатор просмотра рецептов."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class AddFavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор добавления рецепта в избранное."""

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


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор создания пользователя."""
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
    """Сериализатор получения токена."""
    email = serializers.EmailField()
    password = serializers.CharField()

    class Meta:
        model = User
        fields = ('email', 'password')


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор подписки пользователя."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = ShortRecipeSerializer(read_only=True, many=True)
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

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


class AddShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор добавления рецепта в список покупок."""
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
