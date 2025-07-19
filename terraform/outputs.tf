# Trading Execution Engine Terraform Outputs

output "service_account_email" {
  description = "Email of the Trading Execution Engine service account"
  value       = google_service_account.trading_execution_engine.email
}

output "cloud_run_service_url" {
  description = "URL of the Trading Execution Engine Cloud Run service"
  value       = google_cloud_run_v2_service.trading_execution_engine.uri
}

output "cloud_run_service_name" {
  description = "Name of the Trading Execution Engine Cloud Run service"
  value       = google_cloud_run_v2_service.trading_execution_engine.name
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository for Docker images"
  value       = google_artifact_registry_repository.trading_execution_engine.name
}

output "artifact_registry_url" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.trading_execution_engine.repository_id}"
}

output "bigquery_dataset_id" {
  description = "BigQuery dataset ID for execution data"
  value       = google_bigquery_dataset.execution_data.dataset_id
}

output "bigquery_dataset_location" {
  description = "BigQuery dataset location"
  value       = google_bigquery_dataset.execution_data.location
}

output "secret_manager_secrets" {
  description = "Secret Manager secret names"
  value = {
    broker_api_key = google_secret_manager_secret.broker_api_key.secret_id
  }
}

output "scheduler_job_names" {
  description = "Names of Cloud Scheduler jobs"
  value = [
    google_cloud_scheduler_job.live_trading.name,
    google_cloud_scheduler_job.position_management.name
  ]
}

output "monitoring_alert_policy_name" {
  description = "Name of the monitoring alert policy"
  value       = google_monitoring_alert_policy.execution_failures.name
}

output "budget_name" {
  description = "Name of the budget alert (if enabled)"
  value       = var.enable_budget_alerts ? google_billing_budget.execution_engine_budget[0].display_name : null
}

# Configuration outputs for other services
output "execution_engine_config" {
  description = "Execution Engine configuration for other services"
  value = {
    service_url           = google_cloud_run_v2_service.trading_execution_engine.uri
    service_account_email = google_service_account.trading_execution_engine.email
    dataset_id           = google_bigquery_dataset.execution_data.dataset_id
    live_trading_schedule = var.live_trading_schedule
    position_management_schedule = var.position_management_schedule
  }
  sensitive = false
}

# Deployment information
output "deployment_info" {
  description = "Deployment information and next steps"
  value = {
    docker_image_url = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.trading_execution_engine.repository_id}/trading-execution-engine:latest"
    health_check_url = "${google_cloud_run_v2_service.trading_execution_engine.uri}/health"
    execution_endpoint = "${google_cloud_run_v2_service.trading_execution_engine.uri}/execute"
    position_management_endpoint = "${google_cloud_run_v2_service.trading_execution_engine.uri}/manage-positions"
    secret_setup_required = [
      "Set broker API key in Secret Manager: ${google_secret_manager_secret.broker_api_key.secret_id}"
    ]
  }
}
