from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response


def add_item(
        request,
        id,
        post_serializer,
        read_serializer,
        model_to_read,
        field_name,
        user_field
):
    """Функция создания модели для View-классов."""
    user = request.user
    item_id = id
    data = {
        user_field: user.id,
        field_name: item_id
    }
    context = {'request': request}
    serializer = post_serializer(data=data, context=context)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    item = model_to_read.objects.get(id=item_id)
    serializer = read_serializer(item)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def remove_item(
        request,
        id,
        model_class,
        model_to_read,
        field_name,
        user_field
):
    """Функция удаления модели для View-классов."""
    user = request.user
    item = get_object_or_404(model_to_read, id=id)
    model_class.objects.filter(
        **{user_field: user}, **{field_name: item}).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
