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

Откройте `http://127.0.0.1:8000/api/`. Админка доступна по адресу `http://127.0.0.1:8000/admin/`; для входа создайте администратора командой `python manage.py createsuperuser`.

## API

- `GET /api/categories/` — список категорий; `GET /api/categories/<id>/` — категория.
- `GET /api/products/` — список товаров; `GET /api/products/<id>/` — товар.
- `GET /api/reviews/` — список отзывов; `GET /api/reviews/<id>/` — отзыв.
