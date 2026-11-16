#!/usr/bin/env bash
# One-command deploy: terraform apply -> build frontend -> config.json -> S3 sync -> CloudFront invalidation.
# Used both locally and by GitHub Actions. Needs: terraform, aws cli, node/npm, AWS credentials.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then set -a; . ./.env; set +a; fi
: "${TF_STATE_BUCKET:?Set TF_STATE_BUCKET (output of infra/bootstrap) in .env or env}"
export AWS_REGION="${AWS_REGION:-eu-central-1}"
export AWS_DEFAULT_REGION="$AWS_REGION"

echo "==> Terraform apply"
terraform -chdir=infra init -input=false -reconfigure -backend-config="bucket=${TF_STATE_BUCKET}"
terraform -chdir=infra apply -input=false -auto-approve

out() { terraform -chdir=infra output -raw "$1"; }
SITE_URL=$(out site_url)
API_URL=$(out api_url)
POOL_ID=$(out user_pool_id)
CLIENT_ID=$(out user_pool_client_id)
DOMAIN=$(out allowed_email_domain)
BUCKET=$(out site_bucket)
DIST_ID=$(out cloudfront_distribution_id)

echo "==> Build frontend"
(cd frontend && npm ci --no-audit --no-fund && npm run build)
rm -f frontend/dist/config.example.json
# Runtime config: generated here, never committed or baked into the JS bundle.
cat > frontend/dist/config.json <<EOF
{
  "apiUrl": "${API_URL}",
  "userPoolId": "${POOL_ID}",
  "userPoolClientId": "${CLIENT_ID}",
  "allowedEmailDomain": "${DOMAIN}"
}
EOF

echo "==> Upload to s3://${BUCKET}"
# Hashed assets are cached forever; index.html and config.json are always revalidated.
aws s3 sync frontend/dist "s3://${BUCKET}" --delete \
  --exclude index.html --exclude config.json \
  --cache-control "public,max-age=31536000,immutable"
aws s3 cp frontend/dist/index.html "s3://${BUCKET}/index.html" --cache-control "no-cache"
aws s3 cp frontend/dist/config.json "s3://${BUCKET}/config.json" --cache-control "no-cache"

echo "==> Invalidate CloudFront"
aws cloudfront create-invalidation --distribution-id "${DIST_ID}" --paths "/*" --query 'Invalidation.Id' --output text

cat <<EOF

Deployed:
  site_url            = ${SITE_URL}
  api_url             = ${API_URL}
  user_pool_id        = ${POOL_ID}
  user_pool_client_id = ${CLIENT_ID}
EOF
