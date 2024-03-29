from django.contrib import admin

from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ('pk', 'username', 'email')
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')
    empty_value_display = '-пусто-'


admin.site.register(User, UserAdmin)
