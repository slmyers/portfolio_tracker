terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

variable "environment" {
  description = "Deployment environment (local, aws, etc.)"
  type        = string
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

resource "docker_image" "timescaledb" {
  count = var.environment == "local" ? 1 : 0
  name  = "timescale/timescaledb:latest-pg15"
}

resource "docker_container" "timescaledb" {
  count = var.environment == "local" ? 1 : 0
  name  = "timescaledb"
  image = docker_image.timescaledb[0].name
  env = [
    "POSTGRES_USER=${var.timescale_user}",
    "POSTGRES_PASSWORD=${var.timescale_password}",
    "POSTGRES_DB=${var.timescale_db}"
  ]
  ports {
    internal = 5432
    external = 5432
  }
  restart = "unless-stopped"
}

output "timescaledb_container_id" {
  value = docker_container.timescaledb[*].id
  description = "The ID of the TimescaleDB container."
}
