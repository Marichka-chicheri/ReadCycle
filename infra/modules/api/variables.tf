variable "name" {
  type = string
}

variable "routes" {
  description = "Map of name => { route_key, handler, auth }"
  type = map(object({
    route_key = string
    handler   = string
    auth      = bool
  }))
}

variable "lambda_zip" {
  type = string
}

variable "lambda_zip_hash" {
  type = string
}

variable "cors_origins" {
  type = list(string)
}

variable "jwt_issuer" {
  type = string
}

variable "jwt_audience" {
  type = list(string)
}

variable "table_name" {
  type = string
}

variable "table_arn" {
  type = string
}

variable "photos_bucket_name" {
  type = string
}

variable "photos_bucket_arn" {
  type = string
}

variable "google_books_api_key" {
  description = "Google Books API key (\"\" = search only in Open Library)"
  type        = string
  default     = ""
  sensitive   = true
}
