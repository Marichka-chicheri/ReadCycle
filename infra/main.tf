data "aws_caller_identity" "current" {}

locals {
  account_id   = data.aws_caller_identity.current.account_id
  cors_origins = concat([module.frontend_hosting.site_url], var.extra_cors_origins)

  # Add new API routes here: one entry = one Lambda (backend/src/handlers/<module>.py).
  api_routes = {
    health      = { route_key = "GET /health", handler = "handlers.health.handler", auth = false }
    me          = { route_key = "GET /me", handler = "handlers.me.handler", auth = true }
    profile_get = { route_key = "GET /profile", handler = "handlers.profile.get_handler", auth = true }
    profile_put = { route_key = "PUT /profile", handler = "handlers.profile.put_handler", auth = true }
  }
}

# All Lambdas share one zip of backend/src (stdlib + boto3 from the runtime, no extra deps).
data "archive_file" "backend" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/src"
  output_path = "${path.module}/build/backend.zip"
  excludes    = ["**/__pycache__/**"]
}

module "frontend_hosting" {
  source          = "./modules/frontend_hosting"
  name            = "readcycle"
  account_id      = local.account_id
  domain_name     = var.domain_name
  route53_zone_id = var.route53_zone_id
  providers = {
    aws           = aws
    aws.us_east_1 = aws.us_east_1
  }
}

module "data" {
  source       = "./modules/data"
  name         = "readcycle"
  account_id   = local.account_id
  cors_origins = local.cors_origins
}

module "auth" {
  source               = "./modules/auth"
  name                 = "readcycle"
  allowed_email_domain = var.allowed_email_domain
  lambda_zip           = data.archive_file.backend.output_path
  lambda_zip_hash      = data.archive_file.backend.output_base64sha256
}

module "api" {
  source             = "./modules/api"
  name               = "readcycle"
  routes             = local.api_routes
  lambda_zip         = data.archive_file.backend.output_path
  lambda_zip_hash    = data.archive_file.backend.output_base64sha256
  cors_origins       = local.cors_origins
  jwt_issuer         = module.auth.issuer
  jwt_audience       = [module.auth.user_pool_client_id]
  table_name         = module.data.table_name
  table_arn          = module.data.table_arn
  photos_bucket_name = module.data.photos_bucket_name
  photos_bucket_arn  = module.data.photos_bucket_arn
}
