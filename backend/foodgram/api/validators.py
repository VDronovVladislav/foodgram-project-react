from rest_framework.exceptions import APIException


class CustomValidationException(APIException):
    status_code = 400
    default_detail = 'Кастомная ошибка валидации.'
