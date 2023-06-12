from typing import Optional

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Exists, OuterRef

from users.models import User


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=7)
    slug = models.SlugField(
        unique=True,
        validators=[RegexValidator(
            regex=r'^[-a-zA-Z0-9_]+$',
            message='Поле содержит недопустимый символ'
        )]
    )

    def __str__(self):
        return self.name


class RecipeQuerySet(models.QuerySet):
    def add_user_annotation(self, user_id: Optional[int]):
        return self.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(
                    user_id=user_id, recipe__pk=OuterRef('pk')
                )
            ),
            is_in_shopping_cart=Exists(
                ShoppingList.objects.filter(
                    user_id=user_id, recipe__pk=OuterRef('pk')
                )
            ),
        )


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField(max_length=200)
    image = models.ImageField(
        upload_to='recipes/images/',
        default=None
    )
    text = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
    )
    cooking_time = models.IntegerField(validators=[MinValueValidator(1)])
    tags = models.ManyToManyField(Tag, related_name='recipes')
    objects = RecipeQuerySet.as_manager()

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]


class Subscribe(models.Model):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'author'], name='unique_subscribe'
            )
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='user_favourites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='favorite'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite'
            )
        ]


class ShoppingList(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='user_list'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='shopping_list'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_list'
            )
        ]
