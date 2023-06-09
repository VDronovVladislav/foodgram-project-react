import django_filters


class TagsFilter(django_filters.FilterSet):
    """Фильтрация рецептов по тегам."""
    tags = django_filters.CharFilter(
        field_name='tags__slug',
    )
