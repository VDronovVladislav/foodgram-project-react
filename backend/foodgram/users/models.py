from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """Класс пользователя."""
    username = models.CharField(
        max_length=150,
        verbose_name='Логин',
        unique=True,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+$',
            message='Имя пользователя содержит недопустимый символ'
        )]
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя пользователя',
        blank=True
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
        blank=True
    )
    email = models.EmailField(
        max_length=254,
        verbose_name='Email',
        unique=True
    )
    password = models.CharField(
        max_length=150,
        verbose_name='Пароль',
        blank=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
