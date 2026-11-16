terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.7"
    }
  }

  # bucket is passed at init: terraform init -backend-config="bucket=<state_bucket>"
  backend "s3" {
    key            = "readcycle/infra.tfstate"
    region         = "eu-central-1"
    dynamodb_table = "readcycle-tf-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = { Project = "readcycle", ManagedBy = "terraform" }
  }
}

# CloudFront only accepts ACM certificates from us-east-1.
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
  default_tags {
    tags = { Project = "readcycle", ManagedBy = "terraform" }
  }
}
