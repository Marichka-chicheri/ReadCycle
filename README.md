# 📚 ReadCycle

**Сайт обміну паперовими книгами між студентами УКУ.** Постав прочитане на свою полицю, додай бажане у вішліст, і сайт підкаже, з ким можна помінятися. Вхід лише з пошти `@ucu.edu.ua`.

🌐 **Живий сайт:** https://d1my76p49bey2o.cloudfront.net

## ✨ Що вміє

- 🔐 Реєстрація з поштою УКУ (код підтвердження) або через Google, відновлення пароля
- 🗄️ «Моя полиця» і вішліст, обкладинки (пошук або власне фото)
- 🔎 Каталог усіх книг з фільтрами (жанр, мова, віддам / обміняю)
- 🤝 Підбір обміну: хто має те, що ти хочеш, і хоче те, що маєш ти
- 👤 Профілі й контакти (показуються лише при збігу), блокування користувачів
- 🛡️ Скарги й сторінка модератора, бани
- 🔔 Telegram-бот: сповіщення, коли книга з вішліста з'являється в каталозі

## 🏗️ Архітектура

```
Браузер ──HTTPS──► CloudFront ──► S3 (React, приватний бакет)
   │
   ├──► Cognito (вхід, пошта УКУ / Google) ──► Pre Sign-up Lambda: пускає лише @ucu.edu.ua
   │
   └──► API Gateway (JWT від Cognito) ──► Lambda (Python) ──► DynamoDB + S3 (фото)
```

| Шар | Технології |
|---|---|
| Frontend | React + Vite, `amazon-cognito-identity-js` |
| Backend | Python 3.12, AWS Lambda, API Gateway HTTP API, pytest, ruff |
| Дані | DynamoDB (on-demand), S3 для фото |
| Інфраструктура | Terraform (регіон `eu-central-1`), remote state в S3 |
| CI/CD | GitHub Actions + OIDC (без довгих ключів AWS) |

## 📁 Структура

```
backend/    src/handlers (один файл = один маршрут), src/domain, src/repositories, tests/
frontend/   src/pages, src/components
infra/      main.tf, modules/{frontend_hosting,auth,api,data}, bootstrap/, deploy.sh
.github/workflows/deploy.yml
```

## 💻 Локальний запуск

```bash
# бекенд: тести й lint (AWS не потрібен)
cd backend && pip install -r requirements.txt && ruff check . && pytest

# фронт: працює з уже розгорнутим API
cd frontend && npm install
cp public/config.example.json public/config.json   # впишіть значення з `terraform -chdir=../infra output`
npm run dev                                         # http://localhost:5173
```

## 🚀 Деплой у новий AWS-акаунт

Потрібні: Terraform ≥ 1.6, AWS CLI v2, Node 22+, bash, адмін-доступ до акаунта (не root).

1. **Bootstrap (один раз):** створює бакет для state, lock-таблицю та OIDC-роль для GitHub.
   ```bash
   terraform -chdir=infra/bootstrap init && terraform -chdir=infra/bootstrap apply \
     -var github_repo=<owner>/<repo>
   ```
2. **Деплой однією командою:**
   ```bash
   cp .env.example .env     # впишіть TF_STATE_BUCKET (output bootstrap: state_bucket)
   bash infra/deploy.sh
   ```
   Скрипт: `terraform apply` → збірка фронту → `config.json` → `aws s3 sync` → інвалідація CloudFront. Наприкінці друкує `site_url`, `api_url`, `user_pool_id`, `user_pool_client_id`. Перший запуск ~5 хв.
3. **Видалити все:** `terraform -chdir=infra destroy` (bootstrap захищений `prevent_destroy`).

## 🔄 CI/CD

Пуш у `main` запускає `.github/workflows/deploy.yml`:

- **test:** ruff, pytest, збірка фронту, `terraform validate`;
- **deploy:** `infra/deploy.sh` під OIDC-роллю.

Налаштування в GitHub (**Settings → Secrets and variables → Actions**):

| Назва | Тип | Обов'язкова | Що це |
|---|---|---|---|
| `AWS_ROLE_ARN` | Variable | так | output bootstrap: `github_deploy_role_arn` |
| `TF_STATE_BUCKET` | Variable | так | output bootstrap: `state_bucket` |
| `MODERATOR_EMAILS` | Variable | ні | пошти модераторів через кому |
| `GOOGLE_CLIENT_ID` | Variable | ні | вхід через Google (див. нижче) |
| `GOOGLE_CLIENT_SECRET` | Secret | ні | вхід через Google |
| `GOOGLE_BOOKS_API_KEY` | Secret | ні | пошук обкладинок (без нього лише Open Library) |
| `TELEGRAM_BOT_TOKEN` | Secret | ні | токен бота з @BotFather; порожньо = бот вимкнений |

## 🔑 Вхід через Google (необов'язково)

1. [Google Cloud Console](https://console.cloud.google.com): проєкт → **Google Auth Platform** → екран згоди (Audience: **Internal** для організації УКУ або **External** + Publish) зі scopes `openid`, `email`, `profile`.
2. **Clients → Create client → Web application**, redirect URI:
   `https://readcycle-<account_id>.auth.eu-central-1.amazoncognito.com/oauth2/idpresponse`
3. Додайте `GOOGLE_CLIENT_ID` і `GOOGLE_CLIENT_SECRET` у GitHub та запустіть деплой: кнопка з'явиться сама.

Пошта все одно має бути `@ucu.edu.ua`; Google-вхід зв'язується з наявним акаунтом з паролем (один студент = один профіль).

## ⚙️ Змінні Terraform (`infra/variables.tf`)

| Змінна | За замовчуванням | Призначення |
|---|---|---|
| `allowed_email_domain` | `ucu.edu.ua` | домен пошти для реєстрації |
| `domain_name`, `route53_zone_id` | порожньо | власний домен (інакше `*.cloudfront.net`) |
| `extra_cors_origins` | `["http://localhost:5173"]` | додаткові origins для CORS |

## ✅ Перевірка після деплою

- [ ] Сайт відкривається по HTTPS
- [ ] Реєстрація з `@ucu.edu.ua` проходить, код приходить на пошту
- [ ] З іншою поштою реєстрація відхиляється
- [ ] `curl $API/me` без токена → `401`, з токеном → `200`

## 📝 Рішення та припущення

- **Усі Lambda в одному zip** (`archive_file` з `backend/src`): boto3 уже є в runtime, збірка не потрібна. Новий endpoint = файл у `handlers/` + рядок у `local.api_routes` в `infra/main.tf`.
- **API приймає ID-токен** (в ньому є email), помилки наших Lambda мають вигляд `{"error": {"code", "message"}}`.
- **CORS** лише для домену сайту (та localhost для розробки).
- **Конфіг не в коді:** `infra/deploy.sh` генерує `config.json` з Terraform outputs.
- **OIDC `sub`:** GitHub додає числові ID репозиторію в `sub`, тому trust policy ролі приймає обидва формати.
- **State bootstrap-у локальний** (поза git); його створює адмін один раз.
- **Доступ людей до AWS** через IAM Identity Center (SSO), без довгих ключів.
- **Листи з кодом** надсилає Cognito (~50 на добу): для запуску на всіх студентів перейти на SES.

## 💰 Вартість

Для сотень користувачів **≈ $0–1 на місяць** (free tier: CloudFront, Lambda, API Gateway, DynamoDB on-demand, Cognito Lite до 10k MAU).
