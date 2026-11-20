# Digital Agency — этап 1: проектирование

Документ фиксирует решения до написания кода. Всё demo-содержимое в проекте
будет помечено как пример.

## 1. Sitemap

### Публичная часть

```text
/
├── /services
│   └── /services/<slug>
├── /portfolio
│   └── /portfolio/<slug>
├── /about
└── /contacts
    └── /contacts/success
```

Служебные страницы: 404, 500.

### Административная часть (`/admin`)

```text
/admin
├── /login
├── /logout
├── /
├── /services
│   ├── /new
│   └── /<id>/edit
├── /projects
│   ├── /new
│   └── /<id>/edit
├── /testimonials
│   ├── /new
│   └── /<id>/edit
└── /leads
    └── /<id>
```

## 2. Маршруты

### Публичные (`app/routes/public.py`, blueprint `public`)

| Метод | URL | Назначение |
|---|---|---|
| GET | `/` | Главная: hero, услуги, избранные кейсы, отзывы, CTA |
| GET | `/services` | Список опубликованных услуг по `sort_order` |
| GET | `/services/<slug>` | Детальная услуга + форма заявки с предвыбранной услугой |
| GET | `/portfolio` | Сетка кейсов, фильтр `?category=` |
| GET | `/portfolio/<slug>` | Кейс: задача / решение / результат |
| GET | `/about` | О студии, ценности, команда (demo-профили) |
| GET | `/contacts` | Контакты + форма заявки |
| POST | `/contacts` | Сохранение заявки, редирект на успех |
| GET | `/contacts/success` | Страница успешной отправки |
| GET | `/media/<path>` | Отдача загруженных изображений кейсов |

Опубликованные сущности фильтруются `is_published=True`. Неопубликованный или
несуществующий slug → 404.

### Административные (`app/routes/admin.py`, blueprint `admin`, prefix `/admin`)

| Метод | URL | Назначение |
|---|---|---|
| GET, POST | `/login` | Вход администратора |
| POST | `/logout` | Выход |
| GET | `/` | Дашборд: счётчики услуг/кейсов/заявок |
| GET | `/services` | Список услуг |
| GET, POST | `/services/new` | Создание |
| GET, POST | `/services/<id>/edit` | Редактирование |
| POST | `/services/<id>/delete` | Удаление |
| POST | `/services/<id>/toggle` | Публикация / скрытие |
| GET | `/projects` | Список кейсов |
| GET, POST | `/projects/new` | Создание |
| GET, POST | `/projects/<id>/edit` | Редактирование |
| POST | `/projects/<id>/delete` | Удаление |
| POST | `/projects/<id>/toggle` | Публикация / скрытие |
| POST | `/projects/<id>/feature` | Избранный кейс |
| GET | `/testimonials` | Список отзывов |
| GET, POST | `/testimonials/new` | Создание |
| GET, POST | `/testimonials/<id>/edit` | Редактирование |
| POST | `/testimonials/<id>/delete` | Удаление |
| POST | `/testimonials/<id>/toggle` | Публикация / скрытие |
| GET | `/leads` | Входящие заявки |
| GET | `/leads/<id>` | Карточка заявки |
| POST | `/leads/<id>/status` | Смена статуса |

Все маршруты, кроме `/login`, закрыты `@login_required`. Изменяющие запросы —
только POST и с CSRF-токеном. После действия — flash-сообщение и редирект
(PRG-паттерн).

## 3. Модели и связи

Общие правила:

- `created_at` — `UTC`, `datetime.now(timezone.utc)`.
- Все строковые поля ограничены по длине на уровне БД.
- Slug: `unique`, латиница, нижний регистр, только `a-z0-9-`.

### Service

| Поле | Тип | Ограничения |
|---|---|---|
| id | Integer | PK |
| title | String(120) | not null |
| slug | String(140) | unique, index, not null |
| short_description | String(300) | |
| description | Text | |
| icon_name | String(50) | имя иконки из набора |
| is_published | Boolean | default True |
| sort_order | Integer | default 0 |

### Project

| Поле | Тип | Ограничения |
|---|---|---|
| id | Integer | PK |
| title | String(160) | not null |
| slug | String(160) | unique, index, not null |
| category | String(80) | фильтр портфолио |
| summary | String(300) | |
| challenge | Text | задача |
| solution | Text | решение |
| outcome | Text | результат |
| image_path | String(255) | nullable, файл в `instance/uploads` |
| is_featured | Boolean | default False |
| is_published | Boolean | default True |
| created_at | DateTime | default now(UTC) |

### Testimonial

| Поле | Тип | Ограничения |
|---|---|---|
| id | Integer | PK |
| author_name | String(120) | not null |
| company_label | String(120) | |
| text | Text | not null |
| is_published | Boolean | default True |
| sort_order | Integer | default 0 |

### Lead

| Поле | Тип | Ограничения |
|---|---|---|
| id | Integer | PK |
| name | String(120) | not null |
| contact | String(160) | not null (телефон/telegram/email) |
| service_id | FK → service.id | nullable, `ON DELETE SET NULL` |
| message | Text | not null, ≤ 2000 символов |
| created_at | DateTime | default now(UTC) |
| status | String(20) | default `new` |

Статусы: `new`, `in_progress`, `done`, `rejected`.

### AdminUser

| Поле | Тип | Ограничения |
|---|---|---|
| id | Integer | PK |
| username | String(80) | unique, not null |
| password_hash | String(255) | not null |

Наследует `UserMixin` (Flask-Login). Пароль — только хеш
(`generate_password_hash`), исходный пароль не хранится.

### Связи

- `Service.leads` ↔ `Lead.service` — one-to-many, `ondelete="SET NULL"`.
- Остальные сущности независимы.

### Slug

- Генерируется из `title`, если поле пустое.
- Кириллица транслитерируется (свой словарь).
- Коллизия решается суффиксом `-2`, `-3`, … при генерации.
- При ручном вводе дубликата — ошибка валидации формы, а не 500.
- Дополнительно ловится `IntegrityError` на случай гонки.

## 4. Дизайн-система

### Характер

Светлая, «журнальная» подача: крупная типографика, много воздуха, тонкие
линии, один яркий акцент. Никаких тяжёлых теней и градиентного шума.

### Токены (`static/css/tokens.css`)

```css
:root {
  /* color */
  --c-bg: #f6f5f2;
  --c-surface: #ffffff;
  --c-ink: #121214;
  --c-ink-muted: #62626d;
  --c-line: #e2e0da;
  --c-accent: #ff4d2e;
  --c-accent-strong: #c93a1b;
  --c-success: #1f7a4d;
  --c-warning: #a86a00;
  --c-danger: #b3261e;

  /* spacing, база 4px */
  --s-1: 4px;  --s-2: 8px;   --s-3: 12px;  --s-4: 16px;
  --s-6: 24px; --s-8: 32px;  --s-12: 48px; --s-16: 64px;
  --s-24: 96px; --s-32: 128px;

  /* typography */
  --font-sans: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  --fs-display: clamp(2.75rem, 6vw, 5rem);
  --fs-h2: clamp(2rem, 4vw, 3rem);
  --fs-h3: clamp(1.25rem, 2vw, 1.5rem);
  --fs-body: 1rem;
  --fs-small: 0.875rem;

  /* radii */
  --r-sm: 4px; --r-md: 8px; --r-lg: 16px; --r-pill: 999px;

  /* motion */
  --t-fast: 160ms ease;
  --t-base: 240ms ease;

  /* layout */
  --container: 1200px;
  --gutter: clamp(16px, 4vw, 48px);
}
```

### Сетка и адаптив

- Контейнер `max-width: 1200px`, боковые отступы `--gutter`.
- Брейкпоинты: 480 / 768 / 1024 / 1280.
- Мобильная навигация — burger с доступным `aria-expanded`.
- Сетки: услуги 3→2→1, портфолио 3→2→1, команда 4→2→1.

### Типографика

- Заголовки: плотный трекинг (`-0.02em`), `text-wrap: balance`.
- Основной текст: `line-height: 1.6`, `max-width: 68ch`.
- Один шрифт (Inter) + системный фолбэк, без внешних зависимостей.

### Компоненты

- **Кнопки:** primary (accent), secondary (ink outline), ghost; состояния
  `hover`, `active`, `focus-visible` (2px accent outline + offset).
- **Карточки:** услуга, кейс, отзыв; hover — подъём на 2px и линия акцента.
- **Формы:** подпись над полем, ошибка под полем, `aria-invalid`,
  `aria-describedby`; состояния focus.
- **Flash-сообщения:** success / warning / danger.
- **Empty state:** заглушка с пояснением вместо пустой сетки.
- **Админ-таблицы:** адаптив через горизонтальный скролл, действия в строке.

### Доступность

- Видимый `:focus-visible` у всех интерактивных элементов.
- Контраст текста ≥ 4.5:1; accent для крупного текста и UI, темнее — для
  мелкого.
- `prefers-reduced-motion: reduce` отключает transition/анимации.
- Семантическая разметка, `lang="ru"`, alt у изображений, skip-link.
- Формы доступны с клавиатуры, ошибки связаны с полями.

## 5. Структура шаблонов

```text
app/templates/
├── base.html                 # каркас публичной части
├── partials/
│   ├── header.html
│   ├── footer.html
│   ├── flash.html
│   └── form_field.html       # макрос поля формы
├── public/
│   ├── index.html
│   ├── services.html
│   ├── service_detail.html
│   ├── portfolio.html
│   ├── project_detail.html
│   ├── about.html
│   ├── contacts.html
│   └── success.html
├── admin/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── services.html
│   ├── service_form.html
│   ├── projects.html
│   ├── project_form.html
│   ├── testimonials.html
│   ├── testimonial_form.html
│   ├── leads.html
│   ├── lead_detail.html
│   └── partials/
│       └── table.html
└── errors/
    ├── 404.html
    └── 500.html
```

## 6. Структура приложения (этапы 2–5)

```text
app/
├── __init__.py          # create_app(config), регистрация расширений и blueprint'ов
├── extensions.py        # db, login_manager, csrf
├── models.py
├── forms/
│   ├── public.py        # LeadForm
│   └── admin.py         # LoginForm, ServiceForm, ProjectForm, TestimonialForm
├── routes/
│   ├── public.py
│   └── admin.py
├── services/            # вспомогательная логика
│   ├── slugs.py         # транслитерация и уникализация slug
│   └── seed.py          # demo-данные
├── templates/
└── static/
    ├── css/
    │   ├── tokens.css
    │   ├── main.css
    │   └── admin.css
    ├── js/
    │   └── main.js      # burger, фильтры, мелкие улучшения
    └── img/
config.py                # Config / TestConfig из env
run.py
tests/
├── conftest.py
├── test_public.py
├── test_forms.py
└── test_admin.py
```

## 7. Принятые решения

- **Авторизация:** Flask-Login, сессия, один администратор; учётка создаётся
  из `ADMIN_USERNAME` / `ADMIN_PASSWORD` при первом запуске (или CLI-командой).
- **Заявки:** без отправки email; сохраняются в БД, видны в админке.
- **Изображения кейсов:** загрузка файла с белым списком
  `jpg/jpeg/png/webp`, лимит 2 МБ, хранение в `instance/uploads`, отдача через
  `/media/<path>`; исполняемые расширения запрещены.
- **Slug:** латиница, транслитерация кириллицы.
- **Язык интерфейса:** русский.
- **Время:** в БД UTC, отображение в локальном формате.

## 8. Критерии готовности этапа

- Sitemap и маршруты согласованы.
- Модели покрывают все поля из ТЗ и связи описаны.
- Дизайн-токены и компоненты зафиксированы.
- Структура шаблонов и файлов готова к этапу 2.
