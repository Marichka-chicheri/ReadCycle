variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "allowed_email_domain" {
  description = "Only emails from this domain can sign up"
  type        = string
  default     = "ucu.edu.ua"
}

variable "domain_name" {
  description = "Optional custom domain (e.g. readcycle.example.com). Empty = use *.cloudfront.net"
  type        = string
  default     = ""
}

variable "route53_zone_id" {
  description = "Route 53 hosted zone for domain_name (required only if domain_name is set)"
  type        = string
  default     = ""
}

variable "extra_cors_origins" {
  description = "Extra origins allowed by API/photos CORS. Localhost is on by default so the team can run the frontend locally (CI has no terraform.tfvars)."
  type        = list(string)
  default     = ["http://localhost:5173"]
}

variable "google_books_api_key" {
  description = "Google Books API key for cover search and book lookup. Comes from the GOOGLE_BOOKS_API_KEY GitHub secret; without it only Open Library is used."
  type        = string
  default     = ""
  sensitive   = true
}

variable "moderator_emails" {
  description = "Comma-separated emails of moderators (see the moderator page). Comes from the MODERATOR_EMAILS GitHub variable."
  type        = string
  default     = ""
}

variable "telegram_bot_token" {
  description = "Token of the ReadCycle Telegram bot from @BotFather (\"\" = bot switched off). From the TELEGRAM_BOT_TOKEN GitHub secret."
  type        = string
  default     = ""
  sensitive   = true
}

variable "google_client_id" {
  description = "OAuth client ID of the Google Cloud 'Web application' client. Empty = Google sign-in is off. From the GOOGLE_CLIENT_ID GitHub variable."
  type        = string
  default     = ""
}

variable "google_client_secret" {
  description = "OAuth client secret for Google sign-in. From the GOOGLE_CLIENT_SECRET GitHub secret."
  type        = string
  default     = ""
  sensitive   = true
}
