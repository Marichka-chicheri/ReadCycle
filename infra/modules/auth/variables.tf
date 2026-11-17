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
