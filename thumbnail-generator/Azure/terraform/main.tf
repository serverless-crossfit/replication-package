terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 2.71"
    }
  }

  required_version = ">= 0.14.9"
}

provider "azurerm" {
  features {}
}

###################################################################
# Local variables
###################################################################

locals {
  suffix               = var.deployment_id == "" ? "" : "${var.deployment_id}"
  publish_code_command = "az functionapp deployment source config-zip --resource-group ${azurerm_resource_group.rg.name} --name ${azurerm_function_app.function_app.name} --src ${data.archive_file.function_app_code.output_path}"
}

###################################################################
# Resoure Group
###################################################################

resource "azurerm_resource_group" "rg" {
  name     = "thumbnail-generator-tf${local.suffix}"
  location = var.region
}

###################################################################
# API Management
# - Unfornately, integration between API Management and function app
#   is not supported yet in Terraform provider: 
#   https://github.com/terraform-providers/terraform-provider-azurerm/issues/5032
#   so the integration is done manually via Azure console for now.
#   -  make sure "subscription required" is un-checked to simplify API call
###################################################################

resource "azurerm_api_management" "apim" {
  name                = "thumbnail-generator-apim${local.suffix}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  publisher_name  = "My Company"
  publisher_email = "company@terraform.io"

  sku_name = "Consumption_0"
}

resource "azurerm_api_management_backend" "apim_backend" {
  name                = "thumbnail-generator-apim-backend${local.suffix}"
  resource_group_name = azurerm_resource_group.rg.name
  api_management_name = azurerm_api_management.apim.name
  protocol            = "http"
  url                 = "https://backend"
}

resource "azurerm_api_management_logger" "apim_logger" {
  name                = "thumbnail-generator-apim-logger${local.suffix}"
  api_management_name = azurerm_api_management.apim.name
  resource_group_name = azurerm_resource_group.rg.name

  application_insights {
    instrumentation_key = azurerm_application_insights.ai.instrumentation_key
  }
}

resource "azurerm_api_management_diagnostic" "apim_diagnostic" {
  identifier               = "applicationinsights"
  resource_group_name      = azurerm_resource_group.rg.name
  api_management_name      = azurerm_api_management.apim.name
  api_management_logger_id = azurerm_api_management_logger.apim_logger.id

  sampling_percentage       = 100
  always_log_errors         = true
  log_client_ip             = true
  verbosity                 = "verbose"
  http_correlation_protocol = "W3C"
}

###################################################################
# Function App resources
###################################################################

resource "azurerm_storage_account" "function_app" {
  name                     = "thumbnailtf${local.suffix}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
}

resource "azurerm_storage_container" "function_app" {
  name                  = "deployment-artifacts${local.suffix}"
  storage_account_name  = azurerm_storage_account.function_app.name
  container_access_type = "private"
}

resource "azurerm_app_service_plan" "function_app" {
  name                = "thumbnail-generator-function-app-service-plan${local.suffix}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  kind                = "FunctionApp"
  sku {
    tier = "Dynamic"
    size = "Y1"
  }
}

resource "azurerm_function_app" "function_app" {
  name                       = "thumbnail-generator-function-app${local.suffix}"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  app_service_plan_id        = azurerm_app_service_plan.function_app.id
  storage_account_name       = azurerm_storage_account.function_app.name
  storage_account_access_key = azurerm_storage_account.function_app.primary_access_key

  # Make sure the version is right. otherwise, 404 for url 
  # https://stackoverflow.com/questions/64942139/new-deployed-azure-function-returns-404-not-found-error
  version = "~3"

  app_settings = {
    "WEBSITE_RUN_FROM_PACKAGE"       = "1",
    "FUNCTIONS_WORKER_RUNTIME"       = "dotnet",
    "APPINSIGHTS_INSTRUMENTATIONKEY" = azurerm_application_insights.ai.instrumentation_key,
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "false"
    # Custom variable for separate storage account, used in BlobHelper as well
    "CloudStorageAccount" = azurerm_storage_account.thumbnai_store.primary_connection_string
  }
}

###################################################################
# EventGrid as source for triggring CreateThumbnail function
###################################################################

resource "azurerm_eventgrid_system_topic" "function_app" {
  name                   = "thumbnail-blob-events${local.suffix}"
  resource_group_name    = azurerm_resource_group.rg.name
  location               = azurerm_resource_group.rg.location
  source_arm_resource_id = azurerm_storage_account.thumbnai_store.id
  topic_type             = "Microsoft.Storage.StorageAccounts"
}

resource "azurerm_eventgrid_system_topic_event_subscription" "function_app" {
  name                = "RunOnBlobUploaded${local.suffix}"
  system_topic        = azurerm_eventgrid_system_topic.function_app.name
  resource_group_name = azurerm_resource_group.rg.name

  included_event_types = [
    "Microsoft.Storage.BlobCreated"
  ]

  subject_filter {
    subject_begins_with = "/blobServices/default/containers/input"
  }

  azure_function_endpoint {
    function_id = "${azurerm_function_app.function_app.id}/functions/Create-Thumbnail"
    max_events_per_batch = 1 # default value
    preferred_batch_size_in_kilobytes = 64 # default value
  }
}

###################################################################
# Deploy Function App code
# Reference: https://markheath.net/post/deploying-azure-functions-with-azure-cli
###################################################################

data "archive_file" "function_app_code" {
  type        = "zip"
  source_dir  = "${path.module}/../bin/Debug/netcoreapp3.1/publish/"
  output_path = "function-app.zip"
}

resource "azurerm_storage_blob" "storage_blob" {
  name                   = "${filesha256(data.archive_file.function_app_code.output_path)}.zip"
  storage_account_name   = azurerm_storage_account.function_app.name
  storage_container_name = azurerm_storage_container.function_app.name
  type                   = "Block"
  source                 = data.archive_file.function_app_code.output_path
}

resource "null_resource" "function_app_publish" {
  provisioner "local-exec" {
    command = local.publish_code_command
  }
  depends_on = [local.publish_code_command]
  triggers = {
    file_md5             = data.archive_file.function_app_code.output_md5
    publish_code_command = local.publish_code_command
  }
}

###################################################################
# Separate storage for storing thumbnai images 
###################################################################

resource "azurerm_storage_account" "thumbnai_store" {
  name                     = "thumbnaistore${local.suffix}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
}

resource "azurerm_storage_container" "input" {
  name                  = "input"
  storage_account_name  = azurerm_storage_account.thumbnai_store.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "output" {
  name                  = "output"
  storage_account_name  = azurerm_storage_account.thumbnai_store.name
  container_access_type = "private"
}

###################################################################
# Application Insights  
###################################################################

resource "azurerm_application_insights" "ai" {
  name                = "thumbnail-generator-insights${local.suffix}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  workspace_id        = azurerm_log_analytics_workspace.ai.id
  application_type    = "web"
}

resource "azurerm_log_analytics_workspace" "ai" {
  name                = "log-analytics-workspace${local.suffix}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 365
}

resource "azurerm_application_insights_api_key" "ai" {
  name                    = "thumbnail-generator-insights-api-key${local.suffix}"
  application_insights_id = azurerm_application_insights.ai.id
  read_permissions        = ["aggregate", "api", "draft", "extendqueries", "search"]
}
