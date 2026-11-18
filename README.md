# ReadCycle

ReadCycle — вебсайт, де студенти УКУ обмінюються паперовими книгами. Зареєструватися можна лише з університетською поштою `@ucu.edu.ua`. Цей репозиторій — основа прототипу: хостинг, вхід, API і база вже готові, функції для книг додаються поверх.

> Команді, яка продовжує розробку: почніть з [HANDOFF.md](HANDOFF.md) (дані деплою, швидкий старт, куди додавати функції).

## Зміст

- [Поточний деплой](#поточний-деплой)
- [Архітектура](#архітектура)
- [Структура репозиторію](#структура-репозиторію)
- [Рішення та припущення](#рішення-та-припущення)
- [Локальний запуск](#локальний-запуск)
- [Деплой у новий AWS-акаунт](#деплой-у-новий-aws-акаунт)
- [CI/CD (GitHub Actions)](#cicd-github-actions)
- [Вхід через Google](#вхід-через-google)
- [Змінні](#змінні)
- [Орієнтовна вартість](#орієнтовна-вартість)
- [Чеклист перевірки](#чеклист-перевірки)
- [Як додавати функції](#як-додавати-функції)

## Поточний деплой

Акаунт `274394226432`, регіон `eu-central-1`:

| Output | Значення |
|---|---|
| `site_url` | https://d1my76p49bey2o.cloudfront.net |
| `api_url` | https://sp31m1fyue.execute-api.eu-central-1.amazonaws.com |
| `user_pool_id` | `eu-central-1_KbY1FZtNp` |
| `user_pool_client_id` | `1fqjgdcffur7hdn58tm1dh65ct` |

Актуальні значення: `terraform -chdir=infra output`.

## Архітектура

```
Браузер
  │  HTTPS
  ├──► CloudFront (*.cloudfront.net або domain_name, сертифікат ACM у us-east-1)
  │       └─ OAC ──► S3 readcycle-site-<acct> (приватний): збірка React + config.json
  │
  ├──► Cognito User Pool readcycle-users (email + код підтвердження)
  │       └─ Pre Sign-up тригер ──► Lambda readcycle-pre-signup (пропускає лише @allowed_email_domain)
  │
  └──► API Gateway HTTP API readcycle-api  (CORS: лише домен сайту)
          ├─ GET /health ─────────────────────► Lambda readcycle-api-health
          └─ GET /me ── JWT authorizer (Cognito) ─► Lambda readcycle-api-me
                                                     │
                       DynamoDB readcycle-main ◄─────┤  (pk/sk, on-demand)
                       S3 readcycle-photos-<acct> ◄──┘  (фото через presigned URL)

Terraform state: S3 readcycle-tfstate-<acct> + DynamoDB readcycle-tf-locks (infra/bootstrap)
CI: GitHub Actions ──OIDC──► IAM-роль readcycle-github-deploy ──► scripts/deploy.sh
```

## Структура репозиторію

```
backend/
  src/handlers/     # один файл = одна Lambda / один маршрут (health, me, pre_signup)
  src/common/       # http.py (JSON-відповіді, формат помилок), storage.py (presigned URL)
  tests/            # pytest
  requirements.txt  # boto3 (вже є в Lambda runtime) + pytest + ruff
frontend/
  src/pages/        # сторінки (Home, Login, Register): нові додавати сюди
  src/auth.js       # Cognito: реєстрація / підтвердження / вхід / вихід
  src/api.js        # fetch + ID-токен + розбір помилок
infra/
  main.tf variables.tf outputs.tf versions.tf
  modules/{frontend_hosting,auth,api,data}
  bootstrap/        # одноразово: бакет для state, lock-таблиця, OIDC-роль для GitHub
scripts/deploy.sh   # єдина команда деплою (локально і в CI)
.github/workflows/deploy.yml
```

## Рішення та припущення

- **Один zip для всіх Lambda.** `archive_file` пакує `backend/src`. Під час роботи потрібні лише stdlib і boto3, а boto3 вже є в Lambda runtime, тож ні кроку збірки, ні layers немає.
- **Одна Lambda на маршрут.** Маршрути перелічені в `local.api_routes` у `infra/main.tf`. Новий endpoint — це новий файл у `handlers/` і один рядок у цьому списку.
- **API приймає ID-токен, а не access-токен.** У ньому є claim `email`, а authorizer перевіряє `aud` = client id.
- **Формат помилок** наших Lambda: `{"error": {"code": "...", "message": "..."}}`. Виняток — 401 від JWT authorizer API Gateway, він повертає `{"message":"Unauthorized"}`: у HTTP API це тіло змінити не можна. Фронт обробляє обидва формати.
- **CORS** дозволяє лише `site_url`. Для локальної розробки додайте `http://localhost:5173` у `extra_cors_origins`.
- **Перевірка домену** сувора: лише `@ucu.edu.ua`, без піддоменів, без урахування регістру. Фронт теж перевіряє домен, щоб одразу показати зрозуміле повідомлення. Справжній захист — Pre Sign-up Lambda; вона спрацьовує і на AdminCreateUser.
- **Листи надсилає сам Cognito** (`COGNITO_DEFAULT`, близько 50 листів на добу). Для прототипу цього досить, перед запуском варто перейти на SES.
- **Тариф Cognito — Lite**: безкоштовно до 10k MAU.
- **Конфіг не в коді.** `scripts/deploy.sh` генерує `config.json` з Terraform outputs і кладе його поруч з `index.html`. Фронт завантажує його під час старту.
- **State bootstrap-у локальний** (`infra/bootstrap/terraform.tfstate`, у `.gitignore`). Його один раз створює адмін, і ці ресурси рідко змінюються. Якщо файл загубиться, ресурси можна повернути через `terraform import`.
- **Блокування — через DynamoDB-таблицю**, як вимагає завдання. Terraform ≥1.10 також підтримує `use_lockfile = true` в S3, якщо колись захочете прибрати таблицю.
- **Власному домену потрібна зона Route 53.** Сертифікат ACM валідується через DNS, плюс створюються alias-записи A/AAAA. Без `domain_name` сайт працює на `*.cloudfront.net`.
- **Права CI-ролі** покривають сервіси цього стеку. Доступ до IAM обмежено іменами `readcycle-*`. Роль можна отримати лише з push у `main` репозиторію `Marichka-chicheri/ReadCycle`.
- **Формат `sub` в OIDC.** Для новіших репозиторіїв GitHub додає до `sub` незмінні числові ID: `repo:owner@<id>/repo@<id>:ref:refs/heads/main`. Через це перший деплой падав з `Not authorized to perform sts:AssumeRoleWithWebIdentity`. Trust policy в `infra/bootstrap/main.tf` приймає обидва формати (з ID і без). Якщо це знову трапиться, діагностика: тимчасово надрукувати `sub` з токена в кроці workflow і порівняти з умовою ролі.
- **Доступ людей до AWS** йде через IAM Identity Center (SSO, `aws configure sso`), без довгих ключів. Для цього потрібен AWS CLI v2.

## Локальний запуск

Бекенд (тести й lint):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
ruff check . && pytest
```

Фронт працює з розгорнутими API і Cognito:

```bash
cd frontend
npm install
terraform -chdir=../infra output   # скопіюйте значення в public/config.json (шаблон: public/config.example.json)
npm run dev                        # http://localhost:5173
```

Щоб API приймав запити з localhost, додайте `extra_cors_origins = ["http://localhost:5173"]` у `infra/terraform.tfvars` і передеплойте.

## Деплой у новий AWS-акаунт

Потрібні Terraform ≥ 1.6, AWS CLI, Node 22+, bash (на Windows підійде Git Bash) і AWS-креденшели адмін-користувача. Не використовуйте root.

**1. Bootstrap (один раз на акаунт).** Якщо ваш репозиторій не `Marichka-chicheri/ReadCycle`, передайте `-var github_repo=owner/name`.

```bash
terraform -chdir=infra/bootstrap init
terraform -chdir=infra/bootstrap apply
terraform -chdir=infra/bootstrap output   # state_bucket, github_deploy_role_arn
```

**2. Деплой (одна команда).**

```bash
cp .env.example .env   # впишіть значення state_bucket у TF_STATE_BUCKET
bash scripts/deploy.sh
```

Скрипт виконує `terraform apply`, збирає фронт, пише `config.json`, робить `aws s3 sync`, інвалідацію CloudFront і друкує `site_url`, `api_url`, `user_pool_id`, `user_pool_client_id`. Перший запуск триває близько 5 хвилин, найдовше створюється CloudFront.

**Видалення:** `terraform -chdir=infra destroy` (з тим самим `-backend-config`). Ресурси bootstrap захищені `prevent_destroy`.

## CI/CD (GitHub Actions)

`.github/workflows/deploy.yml`:

- **кожен push і PR:** ruff, pytest, збірка фронту, `terraform fmt -check` і `validate`;
- **push у `main`:** додатково `scripts/deploy.sh` під OIDC-роллю (terraform apply → s3 sync → інвалідація CloudFront).

Налаштування (один раз). Секретів і довгоживучих ключів немає:

1. Виконайте bootstrap (крок 1 вище).
2. У GitHub відкрийте **Settings → Secrets and variables → Actions → Variables** і додайте:
   - `AWS_ROLE_ARN` = `github_deploy_role_arn` (тут: `arn:aws:iam::274394226432:role/readcycle-github-deploy`)
   - `TF_STATE_BUCKET` = `state_bucket` (тут: `readcycle-tfstate-274394226432`)
3. Зробіть push у `main`.

Ці значення не секретні, тому зберігаються як variables. Доступ контролює trust policy ролі: вона дозволяє лише цей репозиторій і гілку.

## Вхід через Google

Кнопка «Продовжити з Google» на сторінках входу й реєстрації. Вона **вимкнена**, доки не задано `GOOGLE_CLIENT_ID`: сайт працює як раніше, без кнопки.

**Як це працює.** Браузер переходить на hosted UI Cognito (`/oauth2/authorize`, code + PKCE), Cognito звертається до Google і повертає користувача на `/auth/callback`, де фронт обмінює код на токени. Далі все як зі звичайним входом: API отримує той самий ID-токен.

**Лише пошта УКУ.** Pre Sign-up Lambda спрацьовує і для Google-входу: пошта не з `ucu.edu.ua` відхиляється, як і забанена. Додатково для Google:
- Google має підтвердити пошту (`email_verified`), інакше вхід відхиляється. Без цього будь-хто міг би завести Google-акаунт на чужу адресу `@ucu.edu.ua` і захопити її профіль.
- Якщо в студента вже є акаунт з паролем на цій пошті, Google-вхід **зв'язується** з ним (одна людина = один профіль, книги й вішліст на місці). Перший такий вхід Cognito просить повторити, фронт робить це автоматично.
- Якщо пошта вже входить через Google, реєстрація з паролем для неї блокується з підказкою натиснути кнопку Google.

**Налаштування (один раз).**
1. [Google Cloud Console](https://console.cloud.google.com) → створіть проєкт → **APIs & Services → OAuth consent screen**: User type **External**, назва ReadCycle, scopes `openid`, `email`, `profile`. Натисніть **Publish app** (статус «In production»). Ці scopes не потребують перевірки Google. У статусі «Testing» вхід працює лише для доданих тестових користувачів (до 100).
2. **Credentials → Create credentials → OAuth client ID → Web application**. У **Authorized redirect URIs** додайте
   `https://readcycle-<account_id>.auth.eu-central-1.amazoncognito.com/oauth2/idpresponse`
   (для цього акаунта: `https://readcycle-274394226432.auth.eu-central-1.amazoncognito.com/oauth2/idpresponse`). Доменне ім'я відоме наперед, тож це можна зробити до деплою. «Authorized JavaScript origins» не потрібні.
3. У GitHub (**Settings → Secrets and variables → Actions**) додайте:
   - Variable `GOOGLE_CLIENT_ID` = Client ID
   - Secret `GOOGLE_CLIENT_SECRET` = Client secret
4. Запустіть деплой (пуш у `main` або `bash scripts/deploy.sh` з `TF_VAR_google_client_id` та `TF_VAR_google_client_secret`). Terraform створить домен hosted UI, провайдера Google і оновить клієнта Cognito, `config.json` отримає `cognitoDomain`, і кнопка з'явиться.

**Обмеження.** Секрет клієнта зберігається в Terraform state (як і токен Telegram-бота). Після виходу з сайту сесія Google у браузері лишається, тож повторний вхід через Google може пройти без вибору акаунта. Профіль, створений через Google, не має пароля: «Забули пароль?» для нього не працює.

## Змінні

`infra/` (перевизначаються в `infra/terraform.tfvars`, шаблон — `terraform.tfvars.example`):

| Змінна | За замовчуванням | Призначення |
|---|---|---|
| `region` | `eu-central-1` | Регіон усіх ресурсів, крім сертифіката ACM |
| `allowed_email_domain` | `ucu.edu.ua` | Зареєструватися можна лише з поштою цього домену |
| `domain_name` | `""` | Власний домен (опційно); порожньо — `*.cloudfront.net` |
| `route53_zone_id` | `""` | Зона Route 53 для `domain_name` |
| `google_client_id` | `""` | OAuth Client ID для входу через Google; порожньо — кнопки немає (GitHub variable `GOOGLE_CLIENT_ID`) |
| `google_client_secret` | `""` | OAuth Client secret (GitHub secret `GOOGLE_CLIENT_SECRET`) |
| `extra_cors_origins` | `[]` | Додаткові CORS-origins (наприклад, localhost) |

`infra/bootstrap/`: `region`, `github_repo` (`owner/name`), `github_branch` (`main`).

`.env` (для локального `deploy.sh`): `TF_STATE_BUCKET`, `AWS_REGION`, опційно `AWS_PROFILE`.

## Орієнтовна вартість

На масштабі прототипу (сотні користувачів) — **приблизно $0–1 на місяць**:

| Сервіс | Free tier | Примітка |
|---|---|---|
| CloudFront | 1 TB і 10M запитів/міс (always free) | PriceClass_100 |
| S3 | 5 GB (12 міс) | далі центи за GB |
| Lambda | 1M викликів/міс (always free) | |
| API Gateway HTTP | 1M/міс (12 міс) | далі $1 за 1M |
| DynamoDB on-demand | 25 GB зберігання | оплата за запити, центи |
| Cognito Lite | 10k MAU безкоштовно | |
| CloudWatch Logs | 5 GB | зберігання 14 днів |
| Terraform state | — | центи |

## Чеклист перевірки

Виконано 2026-11-16 на деплої вище:

- [x] Сайт відкривається по HTTPS (`200`), HTTP перенаправляє на HTTPS (`301`), SPA-маршрути (`/login`) повертають `200`.
- [x] Прямий доступ до S3-бакета сайту заблоковано (`403`).
- [x] Реєстрація з `@ucu.edu.ua` проходить Pre Sign-up тригер.
- [x] Реєстрація з іншим доменом (`@gmail.com`) відхиляється з `EMAIL_DOMAIN_NOT_ALLOWED`; фронт показує «Реєстрація можлива лише з університетською поштою @ucu.edu.ua.»
- [x] `GET /health` → `200 {"status": "ok"}`
- [x] `GET /me` без токена → `401`, з невалідним токеном → `401`
- [x] `GET /me` з ID-токеном Cognito → `200 {"sub": ..., "email": ...}`
- [x] CORS: origin сайту отримує `Access-Control-Allow-Origin`, чужий origin — ні.

Як повторити перевірки вручну:

```bash
API=$(terraform -chdir=infra output -raw api_url)
curl -i "$API/health"          # 200
curl -i "$API/me"              # 401
aws cognito-idp sign-up --client-id $(terraform -chdir=infra output -raw user_pool_client_id) \
  --username someone@gmail.com --password 'Passw0rdtest'   # PreSignUp failed ... EMAIL_DOMAIN_NOT_ALLOWED
```

Перевірка з токеном: зареєструйтеся на сайті з реальною поштою `@ucu.edu.ua`. Після входу головна сторінка викличе `/me` і покаже вашу пошту.

## Як додавати функції

- **Новий endpoint API:**
  1. Створіть `backend/src/handlers/books.py` з `@api_handler def handler(event, context)`.
  2. Додайте `books_list = { route_key = "GET /books", handler = "handlers.books.handler", auth = true }` у `local.api_routes` в `infra/main.tf`.
  3. Додайте тест у `backend/tests/`.
- **Дані:** таблиця `TABLE_NAME` (ключі `pk`/`sk`, наприклад `pk=BOOK#<id>`, `sk=META`). GSI додається в `infra/modules/data`.
- **Фото:** `common.storage.presigned_upload_url(key, content_type)`, потім браузер робить `PUT` напряму в S3.
- **Нова сторінка:** файл у `frontend/src/pages/` і маршрут в `App.jsx` (обгорнути в `<ProtectedRoute>`). Для запитів до API — `api('/books')` з `src/api.js`.
