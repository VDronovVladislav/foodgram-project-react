from django.db.models import F, Sum
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets, generics
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.views import APIView
from rest_framework.decorators import action, api_view
from rest_framework.pagination import PageNumberPagination
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
                          RecipePostSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipePostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class UserViewSet(viewsets.ModelViewSet):
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
                user, data=request.data,
                partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = UserReadSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# class CustomAuthToken(ObtainAuthToken):
#     def post(self, request, *args, **kwargs):
#         serializer = AuthTokenSerializer(data=request.data, context={'request': request})
#         serializer.is_valid(raise_exception=True)
#         user = serializer.validated_data['user']
#         token, created = Token.objects.get_or_create(user=user)
#         return Response(
#             {'auth_token': str(token)},
#             status=status.HTTP_200_OK
#         )

@api_view(['POST'])
def get_jwt_token(request):
    """Получение токена."""
    serializer = AuthTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(
        User, email=serializer.validated_data['email'],
        password=serializer.validated_data['password'])
    if user:
        token = AccessToken.for_user(user)
        Token.objects.get_or_create(user=user, key=token)
        return Response({'token': f'{token}'}, status=status.HTTP_200_OK)
    return Response(
        {'message': 'Пользователь не обнаружен'},
        status=status.HTTP_400_BAD_REQUEST
    )


class Logout(APIView):

    def post(self, request):
        request.user.auth_token.delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


# class SubscribeViewSet(viewsets.ModelViewSet):
#     serializer_class = SubscribeSerializer

#     def get_author(self):
#         return get_object_or_404(User, id=self.kwargs.get('user_id'))

#     def perform_create(self, serializer):
#         serializer.save(follower=self.request.user, author=self.get_author())

#     def get_queryset(self):
#         return Subscribe.objects.filter(follower=self.request.user, author=self.get_author())

#     def perform_destroy(self, instance):
#         instance.delete()

#     @action(detail=False, methods=['DELETE'], url_path='delete')
#     def my_custom_destroy(self, request, *args, **kwargs):
#         result = Subscribe.objects.filter(follower=self.request.user, author=self.get_author())
#         result.delete()


class SubscribeView(APIView):

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
    serializer_class = SubscriptionSerializer
    # serializer_class = SubscribeSerializer
    
    # def get_queryset(self):
    #     return User.objects.filter(follower__id=self.request.user.id)

    def get_queryset(self):
        return self.request.user.follower.all()


class FavoriteView(APIView):

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
