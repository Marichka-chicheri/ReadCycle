output "site_url" {
  value = module.frontend_hosting.site_url
}

output "api_url" {
  value = module.api.api_url
}

output "user_pool_id" {
  value = module.auth.user_pool_id
}

output "user_pool_client_id" {
  value = module.auth.user_pool_client_id
}

# Used by scripts/deploy.sh
output "allowed_email_domain" {
  value = var.allowed_email_domain
}

output "site_bucket" {
  value = module.frontend_hosting.bucket_name
}

output "cloudfront_distribution_id" {
  value = module.frontend_hosting.distribution_id
}
