output "user_pool_id" {
  value = aws_cognito_user_pool.main.id
}

output "user_pool_client_id" {
  value = aws_cognito_user_pool_client.web.id
}

output "issuer" {
  value = "https://cognito-idp.${data.aws_region.current.region}.amazonaws.com/${aws_cognito_user_pool.main.id}"
}

# Cognito hosted UI host (used by the SPA for the Google redirect); empty when Google is off.
output "cognito_domain" {
  value = length(aws_cognito_user_pool_domain.main) > 0 ? "${aws_cognito_user_pool_domain.main[0].domain}.auth.${data.aws_region.current.region}.amazoncognito.com" : ""
}
