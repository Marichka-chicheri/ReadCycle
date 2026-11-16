output "table_name" {
  value = aws_dynamodb_table.main.name
}

output "table_arn" {
  value = aws_dynamodb_table.main.arn
}

output "photos_bucket_name" {
  value = aws_s3_bucket.photos.bucket
}

output "photos_bucket_arn" {
  value = aws_s3_bucket.photos.arn
}
