from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (TagViewSet, RecipeViewSet, IngredientViewSet, Logout,
                    get_jwt_token, SubscribeViewSet)


app_name = 'api'

router = DefaultRouter()

# router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipe')
router.register(
    r'users/(?P<user_id>\d+)/subscribe',
    SubscribeViewSet, basename='subscribe'
)

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/token/login/', get_jwt_token, name='login'),
    path('auth/token/logout/', Logout.as_view(), name='logout'),
    # path('users/<int:pk>/subscribe', SubscribeView.as_view(),
    #      name='subscribe')
]
