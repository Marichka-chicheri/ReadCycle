# Cognito User Pool: sign-up by email + confirmation code; Pre Sign-up Lambda restricts the domain.
data "aws_region" "current" {}

resource "aws_cognito_user_pool" "main" {
  name                     = "${var.name}-users"
  user_pool_tier           = "LITE" # free up to 10k MAU; supports triggers + email sign-up
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
    require_uppercase = false
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # Cognito built-in email sender: ~50 emails/day. Switch to SES before real launch.
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    # the same template is used for the sign-up code and for the password-reset code
    email_subject = "ReadCycle: ваш код"
    email_message = "Ваш код ReadCycle: {####}. Якщо ви його не запитували, просто проігноруйте цей лист."
  }

  lambda_config {
    pre_sign_up = aws_lambda_function.pre_signup.arn
  }
}

resource "aws_cognito_user_pool_client" "web" {
  name                          = "${var.name}-web"
  user_pool_id                  = aws_cognito_user_pool.main.id
  generate_secret               = false # public SPA client
  explicit_auth_flows           = ["ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
  prevent_user_existence_errors = "ENABLED"
  id_token_validity             = 60
  access_token_validity         = 60
  refresh_token_validity        = 30
  token_validity_units {
    id_token      = "minutes"
    access_token  = "minutes"
    refresh_token = "days"
  }
}

# ----- Pre Sign-up Lambda -----
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "pre_signup" {
  name               = "${var.name}-pre-signup"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "pre_signup_logs" {
  role       = aws_iam_role.pre_signup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Read-only: the trigger only looks up BANNED_EMAIL#<email> items.
resource "aws_iam_role_policy" "pre_signup_banned_emails" {
  name = "${var.name}-pre-signup-banned-emails"
  role = aws_iam_role.pre_signup.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["dynamodb:GetItem"]
      Resource = var.table_arn
    }]
  })
}

resource "aws_cloudwatch_log_group" "pre_signup" {
  name              = "/aws/lambda/${var.name}-pre-signup"
  retention_in_days = 14
}

resource "aws_lambda_function" "pre_signup" {
  function_name    = "${var.name}-pre-signup"
  role             = aws_iam_role.pre_signup.arn
  runtime          = "python3.12"
  handler          = "handlers.pre_signup.handler"
  filename         = var.lambda_zip
  source_code_hash = var.lambda_zip_hash
  timeout          = 5
  memory_size      = 128
  environment {
    variables = {
      ALLOWED_EMAIL_DOMAIN = var.allowed_email_domain
      TABLE_NAME           = var.table_name
    }
  }
  depends_on = [aws_cloudwatch_log_group.pre_signup]
}

resource "aws_lambda_permission" "cognito" {
  statement_id  = "AllowCognitoInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.pre_signup.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = aws_cognito_user_pool.main.arn
}
