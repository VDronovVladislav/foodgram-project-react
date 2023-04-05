from django.contrib import admin

from .models import (Ingredient, Tag, Recipe, IngredientInRecipe, Subscribe,
                     Favorite, ShoppingList)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'author', 'number_of_additions')
    list_filter = ('name', 'author', 'tags')

    def number_of_additions(self, obj):
        favorites = Favorite.objects.filter(recipe=obj).count()
        return favorites


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
