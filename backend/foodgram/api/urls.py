from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (TagViewSet, RecipeViewSet, IngredientViewSet, Logout,
                    get_jwt_token, SubscribeView, FavoriteView,
                    SubscriptionViewSet, ShoppingCartView, DownloadView)

app_name = 'api'

router = DefaultRouter()

# router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipe')
router.register(
    'users/subscriptions', SubscriptionViewSet, basename='subscriptions'
)


urlpatterns = [
    path('', include('djoser.urls')),
    path('auth/token/login/', get_jwt_token, name='login'),
    path('auth/token/logout/', Logout.as_view(), name='logout'),
    path('users/<int:pk>/subscribe/', SubscribeView.as_view(),
         name='subscribe'),
    path('recipes/download_shopping_cart/', DownloadView.as_view(),
         name='download'),
    path('recipes/<int:id>/favorite/', FavoriteView.as_view(),
         name='favorite'),
    path('recipes/<int:id>/shopping_cart/', ShoppingCartView.as_view(),
         name='shopping_cart'),
    path('', include(router.urls)),
]
