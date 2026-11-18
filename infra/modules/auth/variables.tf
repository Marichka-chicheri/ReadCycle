variable "name" {
  type = string
}

variable "allowed_email_domain" {
  type = string
}

variable "lambda_zip" {
  type = string
}

variable "lambda_zip_hash" {
  type = string
}

variable "table_name" {
  description = "Main DynamoDB table: the pre sign-up trigger checks banned emails in it"
  type        = string
}

variable "table_arn" {
  type = string
}

variable "account_id" {
  description = "Used in the Cognito hosted UI domain prefix (must be globally unique)"
  type        = string
}

variable "google_client_id" {
  description = "OAuth client ID from Google Cloud Console. Empty = Google sign-in is off."
  type        = string
  default     = ""
}

variable "google_client_secret" {
  description = "OAuth client secret from Google Cloud Console"
  type        = string
  default     = ""
  sensitive   = true
}

variable "callback_origins" {
  description = "Site origins allowed to receive the OAuth redirect (<origin>/auth/callback)"
  type        = list(string)
  default     = []
}
