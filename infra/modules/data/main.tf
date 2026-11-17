# Single DynamoDB table (pk/sk) for all app entities + private bucket for photos
# (avatars/<user>/..., covers/<user>/...).
resource "aws_dynamodb_table" "main" {
  name         = "${var.name}-main"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }
  attribute {
    name = "sk"
    type = "S"
  }
  attribute {
    name = "gsi1pk"
    type = "S"
  }
  attribute {
    name = "gsi1sk"
    type = "S"
  }

  # Catalog index: gsi1pk = "BOOK" | "WISH", gsi1sk = "<created_at>#<id>".
  # Lists everyone's books / wishes newest first (main page, matching).
  global_secondary_index {
    name            = "gsi1"
    hash_key        = "gsi1pk"
    range_key       = "gsi1sk"
    projection_type = "ALL"
  }
}

resource "aws_s3_bucket" "photos" {
  bucket = "${var.name}-photos-${var.account_id}"
}

resource "aws_s3_bucket_public_access_block" "photos" {
  bucket                  = aws_s3_bucket.photos.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Browsers upload/download directly with presigned URLs, so the site origin needs CORS.
# POST: uploads use a presigned POST form (S3 enforces the size limit).
resource "aws_s3_bucket_cors_configuration" "photos" {
  bucket = aws_s3_bucket.photos.id
  cors_rule {
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = var.cors_origins
    allowed_headers = ["*"]
    max_age_seconds = 3000
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "photos" {
  bucket = aws_s3_bucket.photos.id
  rule {
    id     = "abort-incomplete-uploads"
    status = "Enabled"
    filter {}
    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}
