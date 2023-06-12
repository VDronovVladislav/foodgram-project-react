import django_filters

from recipe.models import Recipe
from users.models import User


class RecipeFilter(django_filters.FilterSet):
    """Фильтрация рецептов по тегам."""
    author = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    tags = django_filters.AllValuesMultipleFilter(
        field_name='tags__slug',
    )

    is_favorited = django_filters.BooleanFilter(
        method='get_is_favorited',
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='get_is_in_shopping_cart',
    )

    def get_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(user_favourites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(user_list__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')
