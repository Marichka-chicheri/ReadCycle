data "aws_caller_identity" "current" {}

locals {
  account_id   = data.aws_caller_identity.current.account_id
  cors_origins = concat([module.frontend_hosting.site_url], var.extra_cors_origins)

  # Add new API routes here: one entry = one Lambda (backend/src/handlers/<module>.py).
  api_routes = {
    health           = { route_key = "GET /health", handler = "handlers.health.handler", auth = false }
    me               = { route_key = "GET /me", handler = "handlers.me.handler", auth = true }
    profile_get      = { route_key = "GET /profile", handler = "handlers.profile.get_handler", auth = true }
    profile_put      = { route_key = "PUT /profile", handler = "handlers.profile.put_handler", auth = true }
    my_books_list    = { route_key = "GET /my/books", handler = "handlers.my_books.list_handler", auth = true }
    my_books_create  = { route_key = "POST /my/books", handler = "handlers.my_books.create_handler", auth = true }
    my_books_update  = { route_key = "PUT /my/books/{id}", handler = "handlers.my_books.update_handler", auth = true }
    my_books_delete  = { route_key = "DELETE /my/books/{id}", handler = "handlers.my_books.delete_handler", auth = true }
    my_wishes_list   = { route_key = "GET /my/wishes", handler = "handlers.my_wishes.list_handler", auth = true }
    my_wishes_create = { route_key = "POST /my/wishes", handler = "handlers.my_wishes.create_handler", auth = true }
    my_wishes_update = { route_key = "PUT /my/wishes/{id}", handler = "handlers.my_wishes.update_handler", auth = true }
    my_wishes_delete = { route_key = "DELETE /my/wishes/{id}", handler = "handlers.my_wishes.delete_handler", auth = true }
    catalog_list     = { route_key = "GET /books", handler = "handlers.catalog.list_handler", auth = true }
    matches          = { route_key = "GET /matches", handler = "handlers.matches.handler", auth = true }
    user_get         = { route_key = "GET /users/{id}", handler = "handlers.users.handler", auth = true }
    uploads_create   = { route_key = "POST /uploads", handler = "handlers.uploads.handler", auth = true }
    covers_search    = { route_key = "GET /covers/search", handler = "handlers.covers.handler", auth = true }
    books_lookup     = { route_key = "GET /books/lookup", handler = "handlers.book_lookup.handler", auth = true }
    reports_create   = { route_key = "POST /reports", handler = "handlers.reports.create_handler", auth = true }
    blocks_list      = { route_key = "GET /my/blocks", handler = "handlers.blocks.list_handler", auth = true }
    block_put        = { route_key = "PUT /blocks/{id}", handler = "handlers.blocks.block_handler", auth = true }
    block_delete     = { route_key = "DELETE /blocks/{id}", handler = "handlers.blocks.unblock_handler", auth = true }
    mod_reports      = { route_key = "GET /mod/reports", handler = "handlers.moderator.reports_handler", auth = true }
    mod_resolve      = { route_key = "POST /mod/reports/resolve", handler = "handlers.moderator.resolve_handler", auth = true }
    mod_bans         = { route_key = "GET /mod/bans", handler = "handlers.moderator.bans_handler", auth = true }
    mod_ban          = { route_key = "POST /mod/bans/{id}", handler = "handlers.moderator.ban_handler", auth = true }
    mod_unban        = { route_key = "DELETE /mod/bans/{id}", handler = "handlers.moderator.unban_handler", auth = true }
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

  google_books_api_key = var.google_books_api_key
  moderator_emails     = var.moderator_emails
}
