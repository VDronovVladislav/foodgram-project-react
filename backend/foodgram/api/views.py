from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from users.models import User
from recipe.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                           ShoppingList, Subscribe, Tag)
from .filters import RecipeFilter
from .permissions import AuthorOrReadOnly, ReadOnly
from .serializers import (AddFavoriteSerializer, AddShoppingCartSerializer,
                          AddSubscriptionSerializer, AuthTokenSerializer,
                          IngredientSerializer, RecipePostSerializer,
                          RecipeReadSerializer, ShortRecipeSerializer,
                          SubscribeSerializer, TagSerializer,
                          UserReadSerializer, UserSerializer)
from .utils import add_item, remove_item


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет просмотра тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (ReadOnly,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет рецептов."""
    queryset = Recipe.objects.all()
    permission_classes = (AuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipePostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = Recipe.objects
        user = self.request.user
        queryset = queryset.add_user_annotation(user.pk)
        if self.request.query_params.get('is_favorited'):
            queryset = queryset.filter(is_favorited=True)
        if self.request.query_params.get('is_in_shopping_cart'):
            queryset = queryset.filter(is_in_shopping_cart=True)
        return queryset


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет просмотра ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (ReadOnly,)
    pagination_class = None


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет пользователя."""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(
        detail=False,
        methods=['get', 'post'],
    )
    def me(self, request):
        user = request.user
        if request.method == 'POST':
            serializer = UserSerializer(
                user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = UserReadSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def get_jwt_token(request):
    """Получение токена."""
    serializer = AuthTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(
        User,
        email=serializer.validated_data['email'],
        password=serializer.validated_data['password']
    )
    if user:
        token = AccessToken.for_user(user)
        token = Token.objects.get_or_create(user=user)
        return Response({'auth_token': f'{token[0]}'},
                        status=status.HTTP_201_CREATED)
    return Response(
        {'message': 'Пользователь не обнаружен'},
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
def delete_jwt_token(request):
    """Удаление токена."""
    request.user.auth_token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class CustomSetPasswordView(APIView):
    """Вью смены пароля."""
    def post(self, request, *args, **kwargs):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response(
                {'error': 'Вы забыли ввести пароль или новый пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if current_password == new_password:
            return Response(
                {'error': 'Старый и новый пароли совпадают!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        if user.password != current_password:
            return Response(
                {'error': 'Неверный пароль!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.password = new_password
        user.save()

        return Response(
            {'message': 'Пароль обновлен!'},
            status=status.HTTP_200_OK
        )


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет просмотра подписок пользователя."""
    serializer_class = SubscribeSerializer

    def get_queryset(self):
        return User.objects.filter(follower=self.request.user.id)


class DownloadView(APIView):
    """Вью загрузки списка покупок."""
    def get(self, request):
        items = IngredientInRecipe.objects.select_related(
            'recipсe', 'ingredient'
        ).filter(recipe__shopping_list__user=request.user)
        items = items.values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            name=F('ingredient__name'),
            units=F('ingredient__measurement_unit'),
            total=Sum('amount'),
        ).order_by('-total')

        text = '\n'.join([
            f"{item['name']} ({item['units']}) - {item['total']}"
            for item in items
        ])
        filename = "foodgram_shopping_cart.txt"
        response = HttpResponse(text, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename{filename}'

        return response


class FavoriteView(APIView):
    """Вью добавления/удаления рецепта из избранного."""
    def post(self, request, id):
        id = id
        return add_item(
            request, id, AddFavoriteSerializer, ShortRecipeSerializer,
            Recipe, 'recipe', 'user'
        )

    def delete(self, request, id):
        id = id
        return remove_item(request, id, Favorite, Recipe, 'recipe', 'user')


class SubscribeView(APIView):
    """Вью подписки/отписки от пользователя"""
    def post(self, request, pk):
        id = pk
        return add_item(
            request, id, AddSubscriptionSerializer, SubscribeSerializer,
            User, 'author', 'follower'
        )

    def delete(self, request, pk):
        id = pk
        return remove_item(
            request, id, Subscribe, User, 'author', 'follower'
        )


class ShoppingCartView(APIView):
    """Вью добавления/удаления рецепта из списка покупок."""
    def post(self, request, id):
        id = id
        return add_item(
            request, id, AddShoppingCartSerializer, ShortRecipeSerializer,
            Recipe, 'recipe', 'user'
        )

    def delete(self, request, id):
        id = id
        return remove_item(
            request, id, ShoppingList, Recipe, 'recipe', 'user'
        )
