variable "deployment_id" {
  description = "Given id used for suffix the resources for supporting multiple deployments. Only lower case letters and numbers are alloweed"
  default     = ""

  validation {
    condition     = can(regex("^[a-z0-9]*$", var.deployment_id))
    error_message = "The deployment_id value can only consist of lowercase letters and numbers."
  }
}

variable "region" {
  description = "AWS region"
  default     = "us-east-1"
}
