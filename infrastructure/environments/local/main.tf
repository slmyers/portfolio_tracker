terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

variable "environment" {
  description = "Deployment environment (local, aws, etc.)"
  type        = string
  default     = "local"
}

variable "docker_host" {
  description = "Docker host socket"
  type        = string
  default     = "unix:///var/run/docker.sock"
}

variable "timescale_user" {
  description = "TimescaleDB user"
  type        = string
}

variable "timescale_password" {
  description = "TimescaleDB password"
  type        = string
  sensitive   = true
}

variable "timescale_db" {
  description = "TimescaleDB database name"
  type        = string
}

provider "docker" {
  host = var.docker_host
}

# module "postgres" {
#   source = "../../modules/postgres"
#   environment = var.environment
#   providers = {
#     docker = docker
#   }
# }

module "timescaledb" {
  source = "../../modules/timescaledb"
  environment = var.environment
  timescale_user = var.timescale_user
  timescale_password = var.timescale_password
  timescale_db = var.timescale_db
  providers = {
    docker = docker
  }
}

module "redis" {
  source = "../../modules/redis"
  environment = var.environment
  
  providers = {
    docker = docker
  }
}
