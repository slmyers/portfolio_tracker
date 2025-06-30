#!/bin/bash
# launch_terraform_local.sh
# Usage: ./launch_terraform_local.sh
# This script sets the Docker host for macOS Docker Desktop and runs terraform apply in the local infra directory.

export TF_VAR_docker_host="unix:///var/run/docker.sock"
cd "$(dirname "$0")"
terraform init
terraform apply
