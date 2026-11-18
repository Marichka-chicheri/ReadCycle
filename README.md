# ReadCycle

ReadCycle — вебсайт для обміну паперовими книгами між студентами Українського католицького університету. Користувач розміщує прочитані книги на власній полиці, додає бажані до списку побажань, а система підбирає можливі обміни. Реєстрація доступна лише з адрес електронної пошти домену `ucu.edu.ua`.

Розгорнута версія: https://d1my76p49bey2o.cloudfront.net

## Зміст

1. [Функціональність](#1-функціональність)
2. [Архітектура](#2-архітектура)
3. [Структура репозиторію](#3-структура-репозиторію)
4. [Локальний запуск](#4-локальний-запуск)
5. [Розгортання в новому акаунті AWS](#5-розгортання-в-новому-акаунті-aws)
6. [Безперервна інтеграція та доставка](#6-безперервна-інтеграція-та-доставка)
7. [Автентифікація через Google](#7-автентифікація-через-google)
8. [Параметри Terraform](#8-параметри-terraform)
9. [Перевірка після розгортання](#9-перевірка-після-розгортання)
10. [Ухвалені рішення та припущення](#10-ухвалені-рішення-та-припущення)
11. [Орієнтовна вартість](#11-орієнтовна-вартість)

## 1. Функціональність

- Реєстрація за поштою УКУ з підтвердженням кодом або через обліковий запис Google; відновлення пароля.
- Особиста полиця та список побажань; обкладинки книг (пошук або власне зображення).
- Каталог усіх книг із фільтрами за жанром, мовою та типом пропозиції («Обміняю» / «Віддам»).
- Підбір обміну: пошук користувачів, які мають бажане та потребують наявного.
- Публічні профілі; контактні дані доступні лише за наявності збігу; блокування користувачів.
- Скарги та сторінка модератора; блокування облікових записів.
- Telegram-бот: сповіщення про появу в каталозі книги зі списку побажань.

## 2. Архітектура

```
Браузер ──HTTPS──► CloudFront ──► S3 (React, приватний бакет)
   │
   ├──► Cognito (пошта УКУ або Google) ──► Pre Sign-up Lambda: допускає лише @ucu.edu.ua
   │
   └──► API Gateway (JWT Cognito) ──► Lambda (Python) ──► DynamoDB, S3 (фото)
```

| Шар | Технології |
|---|---|
| Frontend | React, Vite, `amazon-cognito-identity-js` |
| Backend | Python 3.12, AWS Lambda, API Gateway HTTP API, pytest, ruff |
| Дані | DynamoDB (режим on-demand), S3 для зображень |
| Інфраструктура | Terraform, регіон `eu-central-1`, віддалений state у S3 |
| CI/CD | GitHub Actions з автентифікацією OIDC (без довготривалих ключів AWS) |

## 3. Структура репозиторію

```
backend/    src/handlers (один файл — один маршрут), src/domain, src/repositories, tests/
frontend/   src/pages, src/components
infra/      main.tf, modules/{frontend_hosting,auth,api,data}, bootstrap/, deploy.sh
.github/workflows/deploy.yml
```

## 4. Локальний запуск

Backend (тести та перевірка стилю; доступ до AWS не потрібен):

```bash
cd backend
pip install -r requirements.txt
ruff check . && pytest
```

Frontend (працює з розгорнутими API та Cognito):

```bash
cd frontend
npm install
cp public/config.example.json public/config.json   # заповнити значеннями з: terraform -chdir=../infra output
npm run dev                                         # http://localhost:5173
```

## 5. Розгортання в новому акаунті AWS

Вимоги: Terraform ≥ 1.6, AWS CLI v2, Node.js 22+, bash, адміністративний доступ до акаунта (не користувач root).

1. **Початкове налаштування (виконується один раз).** Створює бакет для state, таблицю блокувань і роль OIDC для GitHub.
   ```bash
   terraform -chdir=infra/bootstrap init
   terraform -chdir=infra/bootstrap apply -var github_repo=<owner>/<repo>
   ```
2. **Розгортання однією командою.**
   ```bash
   cp .env.example .env     # вказати TF_STATE_BUCKET (вивід bootstrap: state_bucket)
   bash infra/deploy.sh
   ```
   Скрипт виконує `terraform apply`, збирає frontend, формує `config.json`, синхронізує файли з S3 та інвалідує кеш CloudFront. Після завершення виводить `site_url`, `api_url`, `user_pool_id`, `user_pool_client_id`. Перший запуск триває близько п'яти хвилин.
3. **Видалення ресурсів:** `terraform -chdir=infra destroy`. Ресурси bootstrap захищені параметром `prevent_destroy`.

## 6. Безперервна інтеграція та доставка

Кожен пуш у гілку `main` запускає `.github/workflows/deploy.yml`:

- **test** — ruff, pytest, збірка frontend, `terraform validate`;
- **deploy** — `infra/deploy.sh` від імені ролі OIDC.

Параметри задаються в GitHub: **Settings → Secrets and variables → Actions**.

| Назва | Тип | Обов'язкова | Призначення |
|---|---|---|---|
| `AWS_ROLE_ARN` | Variable | так | вивід bootstrap: `github_deploy_role_arn` |
| `TF_STATE_BUCKET` | Variable | так | вивід bootstrap: `state_bucket` |
| `MODERATOR_EMAILS` | Variable | ні | адреси модераторів через кому |
| `GOOGLE_CLIENT_ID` | Variable | ні | автентифікація через Google |
| `GOOGLE_CLIENT_SECRET` | Secret | ні | автентифікація через Google |
| `GOOGLE_BOOKS_API_KEY` | Secret | ні | пошук обкладинок (без ключа використовується лише Open Library) |
| `TELEGRAM_BOT_TOKEN` | Secret | ні | токен бота від @BotFather; порожнє значення вимикає бота |

## 7. Автентифікація через Google

Функція необов'язкова. Доки `GOOGLE_CLIENT_ID` не задано, кнопка входу через Google не відображається.

1. У [Google Cloud Console](https://console.cloud.google.com) створити проєкт, відкрити **Google Auth Platform** і налаштувати екран згоди: аудиторія **Internal** (для організації УКУ) або **External** із публікацією застосунку; області доступу `openid`, `email`, `profile`.
2. У розділі **Clients** створити клієнт типу **Web application** з URI перенаправлення:
   `https://readcycle-<account_id>.auth.eu-central-1.amazoncognito.com/oauth2/idpresponse`
3. Додати `GOOGLE_CLIENT_ID` і `GOOGLE_CLIENT_SECRET` у GitHub та запустити розгортання.

Вимога до домену пошти зберігається і для Google. Вхід через Google зв'язується з наявним обліковим записом, створеним за паролем, тому один користувач має один профіль.

## 8. Параметри Terraform

Визначені в `infra/variables.tf`.

| Змінна | Значення за замовчуванням | Призначення |
|---|---|---|
| `allowed_email_domain` | `ucu.edu.ua` | домен пошти, дозволений для реєстрації |
| `domain_name`, `route53_zone_id` | порожньо | власний домен (інакше використовується `*.cloudfront.net`) |
| `extra_cors_origins` | `["http://localhost:5173"]` | додаткові джерела для CORS |

## 9. Перевірка після розгортання

- [ ] Сайт відкривається за протоколом HTTPS.
- [ ] Реєстрація з адресою `@ucu.edu.ua` завершується успішно, код підтвердження надходить на пошту.
- [ ] Реєстрація з адресою іншого домену відхиляється.
- [ ] Запит `GET /me` без токена повертає `401`, з токеном — `200`.

## 10. Ухвалені рішення та припущення

- Усі Lambda-функції розгортаються одним архівом (`archive_file` з `backend/src`): бібліотека boto3 входить до складу середовища виконання, окремий етап збірки не потрібен. Додавання кінцевої точки потребує файлу в `handlers/` та рядка в `local.api_routes` файлу `infra/main.tf`.
- API приймає ID-токен (він містить адресу пошти). Помилки власних Lambda-функцій мають формат `{"error": {"code", "message"}}`.
- CORS дозволено лише для домену сайту та, для розробки, `localhost`.
- Конфігурація frontend не зберігається в коді: `infra/deploy.sh` формує `config.json` із вихідних значень Terraform.
- GitHub додає числові ідентифікатори репозиторію до поля `sub` токена OIDC, тому політика довіри ролі приймає обидва формати.
- State модуля bootstrap зберігається локально (поза репозиторієм); його створює адміністратор один раз.
- Доступ співробітників до AWS організовано через IAM Identity Center (SSO) без довготривалих ключів.
- Листи з кодами підтвердження надсилає Cognito (приблизно 50 на добу). Перед запуском для всіх студентів слід перейти на Amazon SES.

## 11. Орієнтовна вартість

Для сотень користувачів вартість становить приблизно 0–1 USD на місяць у межах безкоштовного рівня (CloudFront, Lambda, API Gateway, DynamoDB on-demand, Cognito Lite до 10 тис. активних користувачів).
