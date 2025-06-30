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

resource "docker_image" "postgres" {
  count = var.environment == "local" ? 1 : 0
  name  = "postgres:16"
}

resource "docker_container" "postgres" {
  count = var.environment == "local" ? 1 : 0
  name  = "postgres"
  image = docker_image.postgres[0].name
  env = [
    "POSTGRES_USER=postgres",
    "POSTGRES_PASSWORD=postgres",
    "POSTGRES_DB=portfolio"
  ]
  ports {
    internal = 5432
    external = 5432
  }
}
