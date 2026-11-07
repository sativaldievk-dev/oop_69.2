# shop_api

Учебный API магазина на Django REST Framework. В проекте есть категории, товары и отзывы; для каждой модели доступны список и подробная карточка.

## Установка и запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Откройте `http://127.0.0.1:8000/api/v1/`. Админка доступна по адресу `http://127.0.0.1:8000/admin/`; для входа создайте администратора командой `python manage.py createsuperuser`.

## API

- `POST /api/v1/users/register/` — регистрация. Принимает `username`, `email`, `password`; создаёт неактивного пользователя и отправляет шестизначный код на email. В локальной конфигурации письмо с кодом выводится в консоль.
- `POST /api/v1/users/confirm/` — подтверждение. Принимает `email` и `code`.
- `POST /api/v1/token/` — вход по `username` и `password`, возвращает пару JWT-токенов. Неактивные пользователи войти не могут.
- `POST /api/v1/token/refresh/` — обновление access-токена по refresh-токену.
- `GET /api/v1/categories/` и остальные маршруты товаров и отзывов требуют заголовок `Authorization: Bearer <access>`.
- `GET /api/v1/categories/` — список категорий; `GET /api/v1/categories/<id>/` — категория.
- `GET /api/v1/products/` — список товаров; `GET /api/v1/products/<id>/` — товар.
- `GET /api/v1/reviews/` — список отзывов; `GET /api/v1/reviews/<id>/` — отзыв.

## Проверка

```bash
python manage.py test
```
