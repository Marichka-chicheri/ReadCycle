# ReadCycle: передача команді

Готова основа прототипу: сайт, вхід лише з пошти УКУ, API, база, фото-бакет і автодеплой. Функції книг, пошуку та відгуків додаються поверх. Деталі архітектури та рішень див. у [README.md](README.md).

## Дані деплою

Регіон `eu-central-1`, AWS-акаунт `274394226432`.

| Що | Значення |
|---|---|
| Сайт (`site_url`) | https://d1my76p49bey2o.cloudfront.net |
| API (`api_url`) | https://sp31m1fyue.execute-api.eu-central-1.amazonaws.com |
| Cognito User Pool ID (`user_pool_id`) | `eu-central-1_KbY1FZtNp` |
| Cognito Client ID (`user_pool_client_id`) | `1fqjgdcffur7hdn58tm1dh65ct` |
| Дозволений домен пошти | `ucu.edu.ua` |

Це не секрети: вони й так потрапляють у браузер (`/config.json` на сайті). Секретів у репозиторії немає.

Ресурси в AWS (усі з префіксом `readcycle`):

| Ресурс | Назва |
|---|---|
| DynamoDB-таблиця (ключі `pk`/`sk`) | `readcycle-main` |
| S3-бакет для фото | `readcycle-photos-274394226432` |
| S3-бакет сайту | `readcycle-site-274394226432` |
| S3-бакет Terraform state | `readcycle-tfstate-274394226432` |
| IAM-роль для CI | `arn:aws:iam::274394226432:role/readcycle-github-deploy` |

## Як працює деплой

Пуш у `main` запускає GitHub Actions (`.github/workflows/deploy.yml`):

1. **test:** ruff, pytest, збірка фронту, `terraform validate`.
2. **deploy:** `scripts/deploy.sh`: `terraform apply`, збірка фронту, генерація `config.json`, `aws s3 sync`, інвалідація CloudFront.

Через 3–5 хвилин після пушу зміни на сайті. Ключів AWS у GitHub немає: CI бере роль через OIDC. Потрібні лише дві змінні репозиторію (**Settings → Secrets and variables → Actions → Variables**), вони вже додані:

- `AWS_ROLE_ARN` = `arn:aws:iam::274394226432:role/readcycle-github-deploy`
- `TF_STATE_BUCKET` = `readcycle-tfstate-274394226432`

Роль може взяти лише workflow з гілки `main` цього репозиторію.

## Швидкий старт для розробника

Бекенд (тести й lint, AWS не потрібен):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
ruff check . && pytest
```

Фронт з розгорнутим API та Cognito:

```bash
cd frontend
npm install
```

Створіть `frontend/public/config.json` (він у `.gitignore`):

```json
{
  "apiUrl": "https://sp31m1fyue.execute-api.eu-central-1.amazonaws.com",
  "userPoolId": "eu-central-1_KbY1FZtNp",
  "userPoolClientId": "1fqjgdcffur7hdn58tm1dh65ct",
  "allowedEmailDomain": "ucu.edu.ua"
}
```

```bash
npm run dev   # http://localhost:5173
```

API дозволяє CORS лише домену сайту. Щоб працювало з localhost, додайте в `infra/terraform.tfvars` рядок `extra_cors_origins = ["http://localhost:5173"]` і задеплойте.

## Куди додавати функції

| Що додати | Де |
|---|---|
| Новий endpoint | файл у `backend/src/handlers/` з `@api_handler def handler(event, context)` + рядок у `local.api_routes` в `infra/main.tf` + тест у `backend/tests/` |
| Дані (книги тощо) | таблиця `readcycle-main`, змінна середовища `TABLE_NAME`, ключі `pk`/`sk` (наприклад `pk=BOOK#<id>`, `sk=META`) |
| Фото книг | `common.storage.presigned_upload_url(key, content_type)`, браузер робить `PUT` напряму в S3 |
| Нова сторінка | файл у `frontend/src/pages/` + маршрут в `frontend/src/App.jsx` у `<ProtectedRoute>` |
| Запит до API з фронту | `api('/books')` з `frontend/src/api.js` (токен додається сам) |

Формат помилок бекенду: `{"error": {"code": "...", "message": "..."}}`. Виняток: 401 від JWT authorizer API Gateway повертає `{"message":"Unauthorized"}`, фронт обробляє обидва формати.

## Доступ до AWS

Для роботи з кодом AWS-доступ не потрібен: тести локальні, а деплой робить CI. Доступ потрібен лише тому, хто керує інфраструктурою. Він видається через IAM Identity Center (SSO) в акаунті `274394226432`:

1. Власниця акаунта створює користувача в Identity Center і призначає йому роль `AdministratorAccess` (або вужчу).
2. Користувач налаштовує профіль:
   ```bash
   aws configure sso      # потрібен AWS CLI v2; session name: readcycle, region: eu-central-1
   aws sso login --profile readcycle
   export AWS_PROFILE=readcycle
   ```
3. Перевірка: `aws sts get-caller-identity` має показати `AWSReservedSSO_...`, а не root.

Довгих ключів не створювати. Root-акаунт для роботи не використовувати.

## Скарги, модерація, блокування

- **Скарга** (`POST /reports`) на книгу чи користувача з причиною: до 5 на добу від одного студента (`MAX_REPORTS_PER_DAY` у `backend/src/domain/report.py`). Сама скарга нікого не блокує: вона чекає на сторінці модератора, рішення ухвалює лише модератор.
- **Заблокований акаунт** зникає з каталогу, підбору обміну та чужих перегляду профілів; сам не може нічого додавати чи змінювати (403 `ACCOUNT_BANNED`), на сайті бачить екран «Акаунт заблоковано».
- **Сторінка модератора** `/moderator` (пункт «Модерація» в меню): скарги за цілями (найбільше скарг зверху), дії «Відхилити» (знімає **всі** відкриті скарги на цього студента і його книги), «Видалити книгу» (закриває скарги на цю книгу), «Заблокувати акаунт» (закриває всі скарги на студента), вкладка «Заблоковані» з розблокуванням. Усі `/mod/*` endpoint-и перевіряють пошту з ID-токена.
- **Хто модератор:** GitHub → Settings → Secrets and variables → Actions → **Variables** → `MODERATOR_EMAILS` = пошти через кому (наприклад `anna@ucu.edu.ua,petro@ucu.edu.ua`). Це мають бути пошти, якими модератори входять на сайт, тобто університетські (реєстрація дозволена лише з `@ucu.edu.ua`). У `.github/workflows/deploy.yml` у `env:` деплою має бути рядок `TF_VAR_moderator_emails: ${{ vars.MODERATOR_EMAILS }}`. Набуває чинності після наступного деплою (воно потрапляє в Lambda як `MODERATOR_EMAILS`). Доступу до AWS не потрібно.
- **Приватність контактів:** Telegram і телефон сервер віддає (`GET /users/{id}`) лише тому, з ким у власника профілю є збіг (`domain.matching.find_matches` по книгах і вішлістах двох людей). Решта бачить «Контакти з'являться, коли у вас буде збіг». Пошта в чужому профілі не показується ніколи. Телефон видно, лише якщо власник увімкнув «Показувати номер» (`show_phone`) або якщо Telegram не вказано.
- **Видалення акаунта:** `DELETE /profile` прибирає все з `USER#<id>` (профіль, книги, вішліст, блокування з обох боків), фото з S3 і закриває відкриті скарги на цю людину; потім браузер видаляє сам вхід Cognito (`deleteUser`). Заблокований модератором студент видалити акаунт не може. Крім того, пошта заблокованого студента запам'ятовується (`BANNED_EMAIL#<email>`), і Pre Sign-up Lambda не дасть зареєструватися з нею знову, навіть якщо вхід видалили в обхід сайту. Після розблокування пошта знову вільна.
- **Обмеження частоти запитів:** у `infra/main.tf` у маршрутів може бути `rate` (запитів/с): `GET /users/{id}` 5, пошук книг і обкладинок 3, видалення акаунта 1. Решта — загальні 20/с. Ліміт діє на маршрут загалом, не на окрему людину (так працює HTTP API).
- **Telegram-бот (сповіщення про вішліст):** коли хтось ставить книгу на полицю, бот пише всім, чий вішліст вона задовольняє (ті самі правила, що й у підборі обміну; заблоковані й забанені не отримують). Підключення: «Профіль → Сповіщення в Telegram → Підключити» відкриває `t.me/<бот>?start=<одноразовий код>`, людина тисне Start. Бот вимикається `/stop` або кнопкою в профілі. Код: `backend/src/common/telegram.py`, `common/alerts.py`, `domain/alerts.py`, `handlers/telegram.py`, `repositories/telegram.py`.
  - **Налаштування:** створити бота в @BotFather → токен у GitHub **Secret** `TELEGRAM_BOT_TOKEN`; у `deploy.yml` в `env:` деплою рядок `TF_VAR_telegram_bot_token: ${{ secrets.TELEGRAM_BOT_TOKEN }}`. `scripts/deploy.sh` сам реєструє webhook. Без токена бот просто вимкнений, і в профілі блоку не видно.
- **Без російських книг:** `backend/src/domain/language_policy.py`. Пошук книг і обкладинок відкидає видання з мовою `ru`/`rus`, з ISBN 978-5… (російська група) або з російськими ознаками в назві/авторі (ы, э, ъ, ё, слова «и», «что», «это»…; текст з і, ї, є, ґ, ў ніколи не вважається російським). Ті самі правила не дають додати таку книгу чи бажання вручну. Коротку назву без жодних ознак («Идиот») відрізнити неможливо: тут лишаються скарги й модератор.
- **Статус книги:** «на полиці» або «віддана». Віддана книга зникає з каталогу, підбору обміну й чужого перегляду профілю, у власній полиці стає напівпрозорою і не рахується в ліміт книг.
- **Блокування між студентами** (`PUT/DELETE /blocks/{id}`, `GET /my/blocks`): кнопка «Заблокувати» на чужому профілі; блок діє в обидва боки. Список і розблокування: «Профіль → Заблоковані».
- Ключі в DynamoDB описані на початку `backend/src/repositories/moderation.py`.

## Відомі обмеження прототипу

- **Листи з кодом підтвердження** надсилає вбудований відправник Cognito: приблизно 50 листів на добу. Перед запуском для всіх студентів переключити на Amazon SES.
- **Власний домен** не підключено (сайт на `*.cloudfront.net`). Щоб підключити: змінні `domain_name` та `route53_zone_id` в `infra/variables.tf`.
- **Bootstrap-state** (`infra/bootstrap/terraform.tfstate`) лежить локально у того, хто його створював, і не в git. Змінювати bootstrap можна лише з того комп'ютера (або відновити через `terraform import`).
- **Книг, пошуку та відгуків немає**: це наступний етап.

## Перевірка після змін

- [ ] Сайт відкривається по HTTPS.
- [ ] Реєстрація з `@ucu.edu.ua` проходить, лист із кодом приходить.
- [ ] Реєстрація з іншою поштою відхиляється з зрозумілим повідомленням.
- [ ] `GET {api_url}/health` → 200.
- [ ] `GET {api_url}/me` без токена → 401, з ID-токеном → 200 і email.
