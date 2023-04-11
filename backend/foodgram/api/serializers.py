import base64

from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from rest_framework import serializers
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


class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  )
        model = User