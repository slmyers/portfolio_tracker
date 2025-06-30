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

resource "docker_image" "redis" {
  count = var.environment == "local" ? 1 : 0
  name  = "redis:7"
}

resource "docker_container" "redis" {
  count = var.environment == "local" ? 1 : 0
  name  = "redis"
  image = docker_image.redis[0].name
  ports {
    internal = 6379
    external = 6379
  }
}
