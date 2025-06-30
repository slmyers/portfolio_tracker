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

provider "docker" {
  host = var.docker_host
}

module "postgres" {
  source = "../../modules/postgres"
  environment = var.environment
  
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
