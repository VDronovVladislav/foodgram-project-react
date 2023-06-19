### Курсовой проект foodgram-project-react:
## инcтрукция по запуску:

  
Клонировать репозиторий и перейти в него в командной строке:
  
```
git@github.com:VDronovVladislav/foodgram-project-react.git
```

Отредактировать .env файл. Шаблон наполнения:
```
DB_ENGINE=django.db.backends.postgresql # указываем, что работаем с postgresql

DB_NAME=postgres # имя базы данных

POSTGRES_USER=postgres # логин для подключения к базе данных

POSTGRES_PASSWORD=password # пароль для подключения к БД (установите свой)

DB_HOST=db # название сервиса (контейнера)

DB_PORT=5432 # порт для подключения к БД
```
  
Запустить docker-compose командой:
```
docker-compose up -d
```

Выполнить миграции приложений в backend-контейнере:
  
```
docker-compose exec backend python manage.py makemigrations
```
```
docker-compose exec backend python manage.py migrate
```

Создать суперпользователя:
```
docker-compose exec backend python manage.py createsuperuser
```
Собрать статику:
```
docker-compose exec web python manage.py collectstatic --no-input
```

Адреса для проверки проекта:
```
http://foodgramvladproject.ddns.net/api/
http://foodgramvladproject.ddns.net/admin/
http://foodgramvladproject.ddns.net/api/docs/
http://foodgramvladproject.ddns.net/recipes
```

Учетные данные админки для проверки проекта:
```
Логин: vdron
Пароль: vdron717
```

Для заполнения базы данными поочередно и в таком порядке выполнить команды:
```
docker-compose exec web python manage.py load_tags_data
docker-compose exec web python manage.py load_ingredients_data
```

Остановить контейнеры можно командой:
```
docker-compose down -v
```

Лиценция:
```
MIT License
```

Workflow:
> ![workflow](https://github.com/VDronovVladislav/foodgram-project-react/actions/workflows/main.yml/badge.svg)

# Об авторе:
Привет. Меня зовут Дронов Владислав. Студент 19+ когорты направления Python-разработки. Это мой курсовой проект!