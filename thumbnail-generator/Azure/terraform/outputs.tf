###################################################################
# Outputs
###################################################################

output "application_insights_app_id" {
  value = azurerm_application_insights.ai.app_id
}

output "read_telemetry_api_key" {
  value     = azurerm_application_insights_api_key.ai.api_key
  sensitive = true
}
