from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CustomSetPasswordView, DownloadView, FavoriteView,
                    IngredientViewSet, RecipeViewSet, ShoppingCartView,
                    SubscribeView, SubscriptionViewSet, TagViewSet,
                    delete_jwt_token, get_jwt_token)

app_name = 'api'

router = DefaultRouter()

router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipe')
router.register(
    'users/subscriptions', SubscriptionViewSet, basename='subscriptions'
)


urlpatterns = [
    path('auth/token/login/', get_jwt_token, name='login'),
    path('auth/token/logout/', delete_jwt_token, name='logout'),
    path('auth/users/set_password/', CustomSetPasswordView.as_view(),
         name='change_password'),
    path('users/<int:pk>/subscribe/', SubscribeView.as_view(),
         name='subscribe'),
    path('recipes/download_shopping_cart/', DownloadView.as_view(),
         name='download'),
    path('recipes/<int:id>/favorite/', FavoriteView.as_view(),
         name='favorite'),
    path('recipes/<int:id>/shopping_cart/', ShoppingCartView.as_view(),
         name='shopping_cart'),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
]
