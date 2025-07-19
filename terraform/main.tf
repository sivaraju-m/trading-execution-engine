# Trading Execution Engine Terraform Infrastructure
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  
  backend "gcs" {
    bucket = "ai-trading-terraform-state"
    prefix = "trading-execution-engine"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "trading_execution_engine" {
  location      = var.region
  repository_id = "trading-execution-engine"
  description   = "Trading Execution Engine Docker repository"
  format        = "DOCKER"

  labels = {
    component   = "trading-execution-engine"
    environment = var.environment
    managed-by  = "terraform"
  }
}

# Service Account for Trading Execution Engine
resource "google_service_account" "trading_execution_engine" {
  account_id   = "trading-execution-engine-sa"
  display_name = "Trading Execution Engine Service Account"
  description  = "Service account for Trading Execution Engine"
}

# IAM bindings for service account
resource "google_project_iam_member" "trading_execution_engine_bigquery_user" {
  project = var.project_id
  role    = "roles/bigquery.user"
  member  = "serviceAccount:${google_service_account.trading_execution_engine.email}"
}

resource "google_project_iam_member" "trading_execution_engine_bigquery_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.trading_execution_engine.email}"
}

resource "google_project_iam_member" "trading_execution_engine_storage_object_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.trading_execution_engine.email}"
}

resource "google_project_iam_member" "trading_execution_engine_monitoring_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.trading_execution_engine.email}"
}

resource "google_project_iam_member" "trading_execution_engine_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.trading_execution_engine.email}"
}

# Secret Manager for broker API keys
resource "google_secret_manager_secret" "broker_api_key" {
  secret_id = "broker-api-key"
  
  replication {
    automatic = true
  }
  
  labels = {
    component   = "trading-execution-engine"
    environment = var.environment
    managed-by  = "terraform"
  }
}

resource "google_secret_manager_secret_iam_member" "broker_api_key_accessor" {
  secret_id = google_secret_manager_secret.broker_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.trading_execution_engine.email}"
}

# Cloud Run service
resource "google_cloud_run_v2_service" "trading_execution_engine" {
  name     = "trading-execution-engine"
  location = var.region
  
  deletion_protection = false

  template {
    service_account = google_service_account.trading_execution_engine.email
    
    timeout = "3600s"
    
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/trading-execution-engine/trading-execution-engine:latest"
      
      ports {
        container_port = 8080
      }
      
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      
      env {
        name  = "REGION"
        value = var.region
      }

      env {
        name = "BROKER_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.broker_api_key.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = var.cloud_run_cpu
          memory = var.cloud_run_memory
        }
      }
      
      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 30
        timeout_seconds       = 10
        period_seconds        = 10
        failure_threshold     = 3
      }
      
      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 60
        timeout_seconds       = 10
        period_seconds        = 30
        failure_threshold     = 3
      }
    }
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
    
    labels = {
      component   = "trading-execution-engine"
      environment = var.environment
      managed-by  = "terraform"
    }
  }
  
  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [google_artifact_registry_repository.trading_execution_engine]
}

# IAM policy for Cloud Run service
resource "google_cloud_run_service_iam_member" "trading_execution_engine_invoker" {
  service  = google_cloud_run_v2_service.trading_execution_engine.name
  location = google_cloud_run_v2_service.trading_execution_engine.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.trading_execution_engine.email}"
}

# BigQuery dataset for execution data
resource "google_bigquery_dataset" "execution_data" {
  dataset_id    = "execution_data"
  friendly_name = "Trading Execution Data"
  description   = "Dataset for storing trading execution data, orders, and fills"
  location      = var.bigquery_location

  labels = {
    component   = "trading-execution-engine"
    environment = var.environment
    managed-by  = "terraform"
  }

  delete_contents_on_destroy = false

  access {
    role          = "OWNER"
    user_by_email = google_service_account.trading_execution_engine.email
  }
}

# Cloud Scheduler job for live trading
resource "google_cloud_scheduler_job" "live_trading" {
  name        = "live-trading-job"
  description = "Live trading execution during market hours"
  schedule    = var.live_trading_schedule
  time_zone   = var.timezone
  region      = var.region

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.trading_execution_engine.uri}/execute"
    
    oidc_token {
      service_account_email = google_service_account.trading_execution_engine.email
    }
    
    headers = {
      "Content-Type" = "application/json"
    }
    
    body = base64encode(jsonencode({
      execution_type = "live"
      market_hours   = true
    }))
  }
}

# Cloud Scheduler job for position management
resource "google_cloud_scheduler_job" "position_management" {
  name        = "position-management-job"
  description = "Position monitoring and risk management"
  schedule    = var.position_management_schedule
  time_zone   = var.timezone
  region      = var.region

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.trading_execution_engine.uri}/manage-positions"
    
    oidc_token {
      service_account_email = google_service_account.trading_execution_engine.email
    }
    
    headers = {
      "Content-Type" = "application/json"
    }
    
    body = base64encode(jsonencode({
      action = "monitor_and_adjust"
    }))
  }
}

# Monitoring alert policy for execution failures
resource "google_monitoring_alert_policy" "execution_failures" {
  display_name = "Trading Execution Failures"
  combiner     = "OR"
  
  conditions {
    display_name = "Execution Engine Error Rate"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"trading-execution-engine\""
      duration        = "300s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 0.05
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_MEAN"
        group_by_fields = ["resource.labels.service_name"]
      }
    }
  }
  
  notification_channels = var.notification_channels
  
  alert_strategy {
    auto_close = "86400s"
  }
}

# Budget alert for execution engine costs
resource "google_billing_budget" "execution_engine_budget" {
  count = var.enable_budget_alerts ? 1 : 0
  
  billing_account = var.billing_account_id
  display_name    = "Trading Execution Engine Budget"

  budget_filter {
    projects = ["projects/${var.project_id}"]
    labels = {
      component = "trading-execution-engine"
    }
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.monthly_budget)
    }
  }

  threshold_rules {
    threshold_percent = 0.8
    spend_basis      = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 1.0
    spend_basis      = "CURRENT_SPEND"
  }
}
