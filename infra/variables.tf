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
