locals {
  project_name = "ProjectName"
  app_name     = "project-name"
}

resource "aws_ecr_repository" "ecr_repo" {
  name = "${local.app_name}-repo"

  image_scanning_configuration {
    scan_on_push = true
  }
}

module "ecs_lambda" {
  source = "github.com/byuawsfhtl/terraform-ecs-lambda?ref=prd"

  project_name = local.project_name
  app_name     = local.app_name
  env          = var.env

  ecr_repo  = aws_ecr_repository.ecr_repo
  image_tag = var.image_tag

  ecs_command               = ["python", "awsEcs/views/main.py"]
  ecs_environment_variables = { "ENV" = var.env } # Optional
  ecs_policies              = []

  ecs_cpu    = 256 # Optional - Default is 256
  ecs_memory = 512 # Optional - Default is 512

  lambda_environment_variables = { "ENV" = var.env } # Optional
  lambda_endpoint_definitions = [
    {
      path_part       = "run"
      allowed_headers = "Custom-Function-Header1,Custom-Function-Header2" # Optional

      method_definitions = [
        {
          http_method = "POST"
          command     = ["awsLambda.views.main.handle_runEcsTask"]
          timeout     = 3 # Optional
        }
      ]
    }
  ]
  lambda_policies = []
}