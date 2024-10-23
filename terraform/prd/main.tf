terraform {
  required_version = ">=1.4.5"

  backend "s3" {
    bucket         = "terraform-state-storage-646364352403"
    dynamodb_table = "terraform-state-lock-646364352403"
    key            = "EcsLambdaTemplate.tfstate" // Replace 'EcsLambdaTemplate' with the project name
    region         = "us-west-2"
  }
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

provider "aws" {
  region = "us-west-2"
}

module "app" {
  source    = "../"
  env       = "prd"
  image_tag = var.image_tag
}
