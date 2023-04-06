from django.shortcuts import get_object_or_404
from rest_framework import serializers
from recipe.models import (Ingredient, Tag, Recipe, Subscribe, Favorite,
                           ShoppingList)
from users.models import User


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)

    class Meta:
        fields = ('id', 'tags', 'author', 'ingredients', 'name', 'text',
                  'cooking_time')
        model = Recipe