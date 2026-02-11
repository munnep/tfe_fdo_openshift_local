# TFE FDO on OpenShift Local (CRC)

This guide documents how to set up a local OpenShift environment using CodeReady Containers (CRC) for Terraform Enterprise FDO development and testing.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Architecture OpenShift Local (CRC)](#architecture-openshift-local-crc)
- [Architecture Terraform Enterprise on CRC](#architecture-terraform-enterprise-on-crc)
- [Installation CRC](#installation-crc)
- [Accessing the Cluster](#accessing-the-cluster)
  - [Web Console](#web-console)
  - [CLI Access](#cli-access)
  - [Default Credentials](#default-credentials)
- [Deploying Terraform Enterprise on CRC](#deploying-terraform-enterprise-on-crc)
- [Proxy Pod (Squid Server)](#proxy-pod-squid-server)
- [Managing the Cluster](#managing-the-cluster)
  - [Check Status](#check-status)
  - [Stop the Cluster](#stop-the-cluster)
  - [Delete and Recreate](#delete-and-recreate)
  - [Networking](#networking)
  - [Troubleshooting](#troubleshooting)
  - [Documentation](#documentation)

## Prerequisites

- Red Hat account for pull secret 
- Sufficient system resources (16GB+ RAM recommended)

## Architecture OpenShift Local (CRC)

CRC runs a single-node OpenShift cluster inside a lightweight VM on your Mac:

```
Your Mac
  └── CRC VM (via Hypervisor.framework/vfkit)
        └── RHEL CoreOS
              └── OpenShift (single-node cluster)
                    └── CRI-O (container runtime)
                          └── Your containers/pods
```

| Component | Description |
|-----------|-------------|
| Hypervisor | macOS Hypervisor.framework (via vfkit) |
| VM Image | Pre-configured RHEL CoreOS with OpenShift |
| Container Runtime | CRI-O (not Docker/Podman) |

## Architecture Terraform Enterprise on CRC

![](diagram/diagram_tfe_fdo_crc_openshift.png)  



## Installation CRC

- Get Pull Secret

Download your pull secret from: https://console.redhat.com/openshift/create/local

> **Note:** Pull secrets expire every 60 days for developer subscriptions.

![](media/2026-02-11-09-46-44.png)


- Setup CRC

Download the software and install  
![](media/2026-02-11-09-47-31.png)

```bash
crc config set preset openshift
crc setup
```

- Configure Resources (Optional but Recommended)

For TFE FDO, increase the default resources:

```bash
crc config set memory 16384    # 16GB RAM
crc config set disk-size 64    # 64GB disk
```

- Start CRC

```bash
crc start
```

You will be prompted to enter your pull secret on first start.

## Accessing the Cluster

### Web Console

- **URL:** https://console-openshift-console.apps-crc.testing
- Open directly: `crc console`

### CLI Access

```bash
# Configure shell environment
eval $(crc oc-env)

# Login as admin
oc login -u kubeadmin https://api.crc.testing:6443

# Login as regular user
oc login -u developer -p developer https://api.crc.testing:6443
```

### Default Credentials

| User | Password | Role |
|------|----------|------|
| `kubeadmin` | (generated) | cluster-admin |
| `developer` | `developer` | regular user |

To retrieve credentials if forgotten:

```bash
crc console --credentials
```

## Deploying Terraform Enterprise on CRC

- Create a file called `variables.auto.tfvars` file and adjust all settings to your needs.  

```
# General
route53_zone        = "munnep.com"                     # Main domain for Route53
route53_subdomain   = "tfe1"                           # Subdomain for TFE
cert_email          = "patrick.munne@ibm.com"          # Email for certificate generation
   

# Cloudflare
cloudflare_account_id = "xxxxxx"                       # Cloudflare account ID
cloudflare_api_token  = "xxxxxx"                       # API token for Cloudflare

# TFE
admin_username          = "admin"                      # Username for TFE admin user
admin_email             = "patrick.munne@ibm.com"      # Email for TFE admin user
admin_password          = "secret$321"                 # Password for TFE admin user
tfe_encryption_password = "secret$321"                 # Encryption password for TFE
release_sequence        = "1.0.2"                      # TFE release sequence
tfe_raw_license         = "xxxxxxxx"                   # License string for TFE
```

- Build the environment using the code
```
terraform init  
terraform apply  
```

- output example
```
Plan: 22 to add, 0 to change, 0 to destroy.

Outputs:
    cloudflare_delete_tunnel_command = "cloudflared tunnel delete tfe-tunnel-openshift"
    cloudflare_list_tunnels_command = "cloudflared tunnel list"
    cloudflare_login_command = "cloudflared login"
    postgres_port_forward_command = "oc port-forward -n terraform-enterprise svc/tfe-postgres 5432:5432"
    postgres_url = "postgresql://postgres:postgresql@localhost:5432/postgres"
    seaweedfs_filer_url = "http://localhost:8080/"
    tfe_admin_console = "https://admin-tfe3.munnep.com"
    tfe_execute_script_to_create_user_admin = "./scripts/configure_tfe.sh tfe3.munnep.com patrick.munne@ibm.com admin Password#1"
    tfe_url = "https://tfe3.munnep.com"
```

Once the apply is complete, run the config script to create an admin user and test organization in TFE.  
The command is given in the output with `tfe_execute_script_to_create_user_admin`.  

Note:  
`terraform destroy` will not destroy the cloudflare tunnel.  
You will need to delete this manually with the command shown after the apply.  
Default is `cloudflared tunnel delete tfe-tunnel-minikube`.  

The UI interface cloudflare tunnel:  
![](media/2026-01-23-13-01-37.png)  



## Proxy pod (squid server)

A Squid proxy server can be deployed in the cluster on port 3128. This can be useful for testing TFE in environments that require outbound traffic to go through a proxy.

Add the variable 
```
enable_proxy = true
```


## Managing the Cluster

### Check Status

```bash
crc status
```

Example output:
```
CRC VM:          Running
OpenShift:       Running (v4.20.5)
RAM Usage:       6.532GB of 10.93GB
Disk Usage:      24.81GB of 32.68GB (Inside the CRC VM)
Cache Usage:     40.22GB
Cache Directory: /Users/patrick/.crc/cache
```

### Stop the Cluster

```bash
crc stop
```

### Delete and Recreate

```bash
crc delete
crc start
```

> **Note:** Deleting will remove all data. Use `crc stop` to preserve state.

### Networking

CRC uses a local DNS domain for routing:

| Endpoint | URL |
|----------|-----|
| Web Console | `https://console-openshift-console.apps-crc.testing` |
| API Server | `https://api.crc.testing:6443` |
| Your Apps | `https://<route>-<namespace>.apps-crc.testing` |

> **Note:** CRC is only accessible from your local machine. The `.testing` domain is not publicly routable.

### Troubleshooting

#### View Current Config

```bash
crc config view
```

#### Update Pull Secret

```bash
crc stop
crc config set pull-secret-file /path/to/pull-secret.json
crc start
```

### Documentation

- CRC Docs: https://crc.dev/docs/using/
