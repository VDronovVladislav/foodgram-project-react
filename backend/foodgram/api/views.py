from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.decorators import action, api_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from users.models import User
from recipe.models import (Ingredient, Tag, Recipe, Subscribe, Favorite,
                           ShoppingList, IngredientInRecipe)
from .serializers import (TagSerializer, RecipeReadSerializer,
                          IngredientSerializer, UserReadSerializer,
                          AuthTokenSerializer, UserSerializer,
                          SubscribeSerializer, AddSubscriptionSerializer,
                          AddFavoriteSerializer, ShortRecipeSerializer,
                          SubscriptionSerializer, AddShoppingCartSerializer,
                          RecipePostSerializer,)
from .permissions import AuthorOrReadOnly, ReadOnly


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
    filterset_fields = ('tags',)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipePostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)


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
        Token.objects.get_or_create(user=user, key=token)
        return Response({'token': f'{token}'}, status=status.HTTP_200_OK)
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


class SubscribeView(APIView):
    """Вью подписки/отписки от пользователя"""
    def post(self, request, pk):
        follower = request.user
        data = {
            'follower': follower.id,
            'author': pk
        }
        context = {'request': request}
        serializer = AddSubscriptionSerializer(data=data, context=context)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        author = User.objects.get(id=pk)
        serializer = SubscribeSerializer(author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        follower = request.user
        author = get_object_or_404(User, pk=pk)
        Subscribe.objects.filter(follower=follower, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет просмотра подписок пользователя."""
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return self.request.user.follower.all()


class FavoriteView(APIView):
    """Вью добавления/удаления рецепта из избранного."""
    def post(self, request, id):
        user = request.user
        data = {
            'user': user.id,
            'recipe': id
        }
        context = {'request': request}
        serializer = AddFavoriteSerializer(data=data, context=context)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        recipe = Recipe.objects.get(id=id)
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=id)
        Favorite.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartView(APIView):
    """Вью добавления/удаления рецепта из списка покупок."""
    def post(self, request, id):
        user = request.user
        data = {
            'user': user.id,
            'recipe': id
        }
        context = {'request': request}
        serializer = AddShoppingCartSerializer(data=data, context=context)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        recipe = Recipe.objects.get(id=id)
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=id)
        ShoppingList.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DownloadView(APIView):
    """Вью загрузки списка покупок."""
    def get(self, request):
        items = IngredientInRecipe.objects.select_related(
            'recipe', 'ingredient'
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
