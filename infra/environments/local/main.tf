terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}


variable "docker_host" {
  description = "Docker host socket"
  type        = string
  default     = "unix:///var/run/docker.sock"
}

provider "docker" {
  host = var.docker_host
}

resource "docker_image" "redis" {
  name = "redis:7"
}

resource "docker_container" "redis" {
  name  = "redis"
  image = docker_image.redis.name
  ports {
    internal = 6379
    external = 6379
  }
}

resource "docker_image" "postgres" {
  name = "postgres:16"
}

resource "docker_container" "postgres" {
  name  = "postgres"
  image = docker_image.postgres.name
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
