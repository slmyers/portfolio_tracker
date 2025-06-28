# Local Infrastructure with Terraform and Docker

This directory contains Terraform configuration to provision local infrastructure (Redis and Postgres) using Docker.

## Prerequisites
- Docker Desktop for Mac must be installed and running.
- Terraform must be installed (see project root README for instructions).

## Usage

1. **Start Docker Desktop**
   - Make sure Docker Desktop is running (look for the whale icon in your menu bar).

2. **Run Terraform with the correct Docker socket**
   - Use the provided script to set the Docker host and run Terraform:

   ```sh
   ./launch_terraform_local.sh
   ```

   This script sets the `TF_VAR_docker_host` environment variable to the correct socket for Docker Desktop on macOS and runs `terraform apply` in this directory.

3. **Manual alternative**
   - You can also run the following manually:

   ```sh
   export TF_VAR_docker_host="unix:///Users/stevenmyers/Library/Containers/com.docker.docker/Data/docker-cli.sock"
   terraform apply
   ```

## Notes
- The Docker host socket is configurable via the `docker_host` variable in `main.tf`.
- If you are not on macOS, you may need to adjust the socket path accordingly.
- The script assumes you are running from this directory.
