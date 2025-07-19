# Trading Execution Engine Terraform Variables

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "bigquery_location" {
  description = "BigQuery dataset location"
  type        = string
  default     = "US"
}

variable "timezone" {
  description = "Timezone for scheduled jobs"
  type        = string
  default     = "America/New_York"
}

# Cloud Run Configuration
variable "cloud_run_cpu" {
  description = "CPU allocation for Cloud Run"
  type        = string
  default     = "4"
}

variable "cloud_run_memory" {
  description = "Memory allocation for Cloud Run"
  type        = string
  default     = "8Gi"
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 1  # Always on for live trading
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 5
}

# Scheduling Configuration
variable "live_trading_schedule" {
  description = "Cron schedule for live trading (market hours)"
  type        = string
  default     = "*/5 9-16 * * 1-5"  # Every 5 minutes during market hours
}

variable "position_management_schedule" {
  description = "Cron schedule for position management"
  type        = string
  default     = "*/1 9-16 * * 1-5"  # Every minute during market hours
}

# Monitoring Configuration
variable "notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}

# Budget Configuration
variable "enable_budget_alerts" {
  description = "Enable budget alerts"
  type        = bool
  default     = true
}

variable "billing_account_id" {
  description = "Billing account ID for budget alerts"
  type        = string
  default     = ""
}

variable "monthly_budget" {
  description = "Monthly budget limit in USD"
  type        = number
  default     = 1000
}

# Security Configuration
variable "allowed_ingress" {
  description = "Allowed ingress configuration for Cloud Run"
  type        = string
  default     = "INGRESS_TRAFFIC_INTERNAL_ONLY"
}

variable "vpc_connector" {
  description = "VPC connector for private networking"
  type        = string
  default     = ""
}

# Performance Configuration
variable "concurrency" {
  description = "Maximum concurrent requests per instance"
  type        = number
  default     = 50
}

variable "execution_environment" {
  description = "Execution environment (EXECUTION_ENVIRONMENT_GEN1 or EXECUTION_ENVIRONMENT_GEN2)"
  type        = string
  default     = "EXECUTION_ENVIRONMENT_GEN2"
}

# Trading Configuration
variable "max_position_size" {
  description = "Maximum position size in USD"
  type        = number
  default     = 100000
}

variable "max_daily_loss" {
  description = "Maximum daily loss limit in USD"
  type        = number
  default     = 10000
}

variable "max_drawdown_percentage" {
  description = "Maximum drawdown percentage (0-1)"
  type        = number
  default     = 0.05
}

variable "risk_free_rate" {
  description = "Risk-free rate for calculations"
  type        = number
  default     = 0.05
}

# Broker Configuration
variable "broker_name" {
  description = "Primary broker name"
  type        = string
  default     = "alpaca"
}

variable "backup_broker_name" {
  description = "Backup broker name"
  type        = string
  default     = "interactive_brokers"
}

# Data Configuration
variable "execution_data_retention_days" {
  description = "Execution data retention period in days"
  type        = number
  default     = 2555  # ~7 years
}

variable "order_timeout_seconds" {
  description = "Order timeout in seconds"
  type        = number
  default     = 300
}

# Market Hours Configuration
variable "market_open_time" {
  description = "Market open time (EST)"
  type        = string
  default     = "09:30"
}

variable "market_close_time" {
  description = "Market close time (EST)"
  type        = string
  default     = "16:00"
}

variable "pre_market_start" {
  description = "Pre-market trading start time (EST)"
  type        = string
  default     = "04:00"
}

variable "after_hours_end" {
  description = "After-hours trading end time (EST)"
  type        = string
  default     = "20:00"
}

# Trading Strategies
variable "enabled_execution_strategies" {
  description = "List of enabled execution strategies"
  type        = list(string)
  default     = ["twap", "vwap", "limit", "market", "stop_loss"]
}

variable "slippage_tolerance" {
  description = "Maximum allowed slippage percentage"
  type        = number
  default     = 0.001  # 0.1%
}
