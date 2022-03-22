terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.27"
    }
  }

  required_version = ">= 0.15.0"
}

provider "aws" {
  profile = "default"
  region  = var.region
}

###################################################################
# Local variables
###################################################################

locals {
  suffix = var.deployment_id == "" ? "" : "${var.deployment_id}"
}

###################################################################
# API Gateway
###################################################################

resource "aws_api_gateway_rest_api" "thumbnail" {
  name        = "thumbnail-generator${local.suffix}"
  description = "This is API for uploading thumbnail image source"

  # Reference: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-payload-encodings-configure-with-console.html
  binary_media_types = [
    "image/jpg"
  ]
}

resource "aws_api_gateway_resource" "thumbnail_upload" {
  rest_api_id = aws_api_gateway_rest_api.thumbnail.id
  parent_id   = aws_api_gateway_rest_api.thumbnail.root_resource_id
  path_part   = "upload"
}

resource "aws_api_gateway_method" "thumbnail_upload" {
  rest_api_id   = aws_api_gateway_rest_api.thumbnail.id
  resource_id   = aws_api_gateway_resource.thumbnail_upload.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "thumbnail_upload" {
  rest_api_id             = aws_api_gateway_rest_api.thumbnail.id
  resource_id             = aws_api_gateway_resource.thumbnail_upload.id
  http_method             = aws_api_gateway_method.thumbnail_upload.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.upload.invoke_arn
}

resource "aws_api_gateway_deployment" "thumbnail" {
  rest_api_id = aws_api_gateway_rest_api.thumbnail.id

  triggers = {
    # NOTE: The configuration below will satisfy ordering considerations,
    #       but not pick up all future REST API changes. More advanced patterns
    #       are possible, such as using the filesha1() function against the
    #       Terraform configuration file(s) or removing the .id references to
    #       calculate a hash against whole resources. Be aware that using whole
    #       resources will show a difference after the initial implementation.
    #       It will stabilize to only change when resources change afterwards.
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.thumbnail_upload.id,
      aws_api_gateway_method.thumbnail_upload.id,
      aws_api_gateway_integration.thumbnail_upload.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "thumbnail" {
  deployment_id        = aws_api_gateway_deployment.thumbnail.id
  rest_api_id          = aws_api_gateway_rest_api.thumbnail.id
  stage_name           = "dev"
  xray_tracing_enabled = true
}


resource "aws_cloudwatch_log_group" "example" {
  name              = "API-Gateway-Execution-Logs_${aws_api_gateway_rest_api.thumbnail.id}/${aws_api_gateway_stage.thumbnail.stage_name}"
  retention_in_days = 90
}

resource "aws_api_gateway_method_settings" "example" {
  rest_api_id = aws_api_gateway_rest_api.thumbnail.id
  stage_name  = aws_api_gateway_stage.thumbnail.stage_name
  method_path = "*/*"

  settings {
    data_trace_enabled = true
    logging_level      = "INFO"
  }
}

resource "aws_api_gateway_account" "thumbnail" {
  cloudwatch_role_arn = aws_iam_role.thumbnail_api_cloudwatch.arn
}

resource "aws_iam_role" "thumbnail_api_cloudwatch" {
  name = "api_gateway_cloudwatch_global${local.suffix}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "apigateway.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "thumbnail_api_cloudwatch" {
  name = "default"
  role = aws_iam_role.thumbnail_api_cloudwatch.id

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:DescribeLogGroups",
                "logs:DescribeLogStreams",
                "logs:PutLogEvents",
                "logs:GetLogEvents",
                "logs:FilterLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
EOF
}

###################################################################
# Lambda - Upload
###################################################################

resource "aws_lambda_permission" "apigw_lambda_upload" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.upload.function_name
  principal     = "apigateway.amazonaws.com"

  # The /*/* portion grants access from any method on any resource
  # within the API Gateway "REST API".
  source_arn = "${aws_api_gateway_rest_api.thumbnail.execution_arn}/*/*"
}

data "archive_file" "lambdas_code" {
  type        = "zip"
  source_dir  = "${path.module}/../bin/Debug/netcoreapp3.1/publish/"
  output_path = "lambdas.zip"
}

resource "aws_lambda_function" "upload" {
  filename      = data.archive_file.lambdas_code.output_path
  function_name = "thumbnail-upload${local.suffix}"
  role          = aws_iam_role.upload.arn
  handler       = "ThumbnailGenerator::ThumbnailGenerator.AWS.Upload::Handler"
  runtime       = "dotnetcore3.1"
  timeout       = 20
  memory_size   = 1769


  environment {
    variables = {
      IMAGE_BUCKET = aws_s3_bucket.thumbnail.id
    }
  }

  tracing_config {
    mode = "Active"
  }

  source_code_hash = filebase64sha256(data.archive_file.lambdas_code.output_path)
}

resource "aws_iam_role" "upload" {
  name = "thumbnail-upload-lamda-role${local.suffix}"

  assume_role_policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
POLICY
}

resource "aws_iam_role_policy_attachment" "upload" {
  role       = aws_iam_role.upload.name
  policy_arn = aws_iam_policy.upload.arn
}

resource "aws_iam_policy" "upload" {
  name   = "thumbnail-upload-lamda-role-policy${local.suffix}"
  path   = "/"
  policy = data.aws_iam_policy_document.upload.json
}

data "aws_iam_policy_document" "upload" {

  statement {
    sid    = "AllowCloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      "*"
    ]
  }

  statement {
    sid    = "AllowXRay"
    effect = "Allow"
    actions = [
      "xray:PutTraceSegments",
      "xray:PutTelemetryRecords",
      "xray:GetSamplingRules",
      "xray:GetSamplingTargets",
      "xray:GetSamplingStatisticSummaries",
    ]
    resources = [
      "*"
    ]
  }

  statement {
    sid    = "AllowAcessS3"
    effect = "Allow"
    actions = [
      "s3:*Object*",
    ]
    resources = [
      "*"
    ]
  }

}

# This is to optionally manage the CloudWatch Log Group for the Lambda Function.
# If skipping this resource configuration, also add "logs:CreateLogGroup" to the IAM policy below.
resource "aws_cloudwatch_log_group" "upload_logging" {
  name              = "/aws/lambda/${aws_lambda_function.upload.function_name}"
  retention_in_days = 90
}

###################################################################
# S3 bucket
###################################################################

resource "aws_s3_bucket" "thumbnail" {
  bucket = "thumbnail-generator-bucket${local.suffix}"
}

resource "aws_s3_bucket_notification" "create_thumbnail" {
  bucket = aws_s3_bucket.thumbnail.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.create_thumbnail.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "input/"
    filter_suffix       = ".jpg"
  }

  depends_on = [aws_lambda_permission.create_thumbnail]
}

###################################################################
# Lambda - Create Thumbnail
###################################################################

resource "aws_iam_role" "create_thumbnail" {
  name = "create-thumbnail-lambda-role${local.suffix}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_lambda_permission" "create_thumbnail" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.create_thumbnail.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.thumbnail.arn
}

resource "aws_lambda_function" "create_thumbnail" {
  filename      = data.archive_file.lambdas_code.output_path
  function_name = "thumbnail-create-thumbnail${local.suffix}"
  role          = aws_iam_role.create_thumbnail.arn
  handler       = "ThumbnailGenerator::ThumbnailGenerator.AWS.CreateThumbnail::Handler"
  runtime       = "dotnetcore3.1"
  timeout       = 20
  memory_size   = 1769

  tracing_config {
    mode = "Active"
  }

  source_code_hash = filebase64sha256(data.archive_file.lambdas_code.output_path)
}

resource "aws_iam_role_policy_attachment" "create_thumbnail" {
  role       = aws_iam_role.create_thumbnail.name
  policy_arn = aws_iam_policy.create_thumbnail.arn
}

resource "aws_iam_policy" "create_thumbnail" {
  name   = "thumbnail-create-thumbnail-role-policy${local.suffix}"
  path   = "/"
  policy = data.aws_iam_policy_document.create_thumbnail.json
}

data "aws_iam_policy_document" "create_thumbnail" {

  statement {
    sid    = "AllowCloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      "*"
    ]
  }

  statement {
    sid    = "AllowXRay"
    effect = "Allow"
    actions = [
      "xray:PutTraceSegments",
      "xray:PutTelemetryRecords",
      "xray:GetSamplingRules",
      "xray:GetSamplingTargets",
      "xray:GetSamplingStatisticSummaries",
    ]
    resources = [
      "*"
    ]
  }

  statement {
    sid    = "AllowAcessS3"
    effect = "Allow"
    actions = [
      "s3:*Object*",
    ]
    resources = [
      "*"
    ]
  }

}

# This is to optionally manage the CloudWatch Log Group for the Lambda Function.
# If skipping this resource configuration, also add "logs:CreateLogGroup" to the IAM policy below.
resource "aws_cloudwatch_log_group" "create_thumbnail" {
  name              = "/aws/lambda/${aws_lambda_function.create_thumbnail.function_name}"
  retention_in_days = 90
}
