# HTTP API + one Lambda per route. Routes with auth = true require a valid Cognito JWT.
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = var.cors_origins
    allow_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    allow_headers = ["authorization", "content-type"]
    max_age       = 3600
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true
  default_route_settings {
    throttling_burst_limit = 50
    throttling_rate_limit  = 20
  }
}

resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id           = aws_apigatewayv2_api.main.id
  name             = "${var.name}-cognito"
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  jwt_configuration {
    issuer   = var.jwt_issuer
    audience = var.jwt_audience
  }
}

# ----- shared Lambda role -----
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "api" {
  name               = "${var.name}-api-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "logs" {
  role       = aws_iam_role.api.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "data_access" {
  statement {
    actions = [
      "dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:DeleteItem",
      "dynamodb:Query", "dynamodb:Scan", "dynamodb:BatchGetItem", "dynamodb:BatchWriteItem",
    ]
    resources = [var.table_arn, "${var.table_arn}/index/*"]
  }
  statement {
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${var.photos_bucket_arn}/*"]
  }
  # Google Books API key for cover search (SecureString, created by hand; see README).
  statement {
    actions   = ["ssm:GetParameter"]
    resources = ["arn:aws:ssm:*:*:parameter${var.google_books_key_param}"]
  }
}

resource "aws_iam_role_policy" "data_access" {
  name   = "${var.name}-api-data"
  role   = aws_iam_role.api.id
  policy = data.aws_iam_policy_document.data_access.json
}

# ----- per-route Lambda + integration + route -----
resource "aws_cloudwatch_log_group" "route" {
  for_each          = var.routes
  name              = "/aws/lambda/${var.name}-api-${each.key}"
  retention_in_days = 14
}

resource "aws_lambda_function" "route" {
  for_each         = var.routes
  function_name    = "${var.name}-api-${each.key}"
  role             = aws_iam_role.api.arn
  runtime          = "python3.12"
  handler          = each.value.handler
  filename         = var.lambda_zip
  source_code_hash = var.lambda_zip_hash
  timeout          = 10
  memory_size      = 256
  environment {
    variables = {
      TABLE_NAME             = var.table_name
      PHOTOS_BUCKET          = var.photos_bucket_name
      GOOGLE_BOOKS_KEY_PARAM = var.google_books_key_param
    }
  }
  depends_on = [aws_cloudwatch_log_group.route]
}

resource "aws_apigatewayv2_integration" "route" {
  for_each               = var.routes
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.route[each.key].invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "route" {
  for_each           = var.routes
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = each.value.route_key
  target             = "integrations/${aws_apigatewayv2_integration.route[each.key].id}"
  authorization_type = each.value.auth ? "JWT" : "NONE"
  authorizer_id      = each.value.auth ? aws_apigatewayv2_authorizer.cognito.id : null
}

resource "aws_lambda_permission" "route" {
  for_each      = var.routes
  statement_id  = "AllowApiGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.route[each.key].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
