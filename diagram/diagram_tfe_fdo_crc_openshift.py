# diagram_tfe_fdo_crc_openshift.py
# Requirements:
#   pip install diagrams
#   brew install graphviz  # on macOS
#
# Run:
#   source ../venv/bin/activate
#   python3 diagram_tfe_fdo_crc_openshift.py
#
# Output:
#   diagram_tfe_fdo_crc_openshift.png

from diagrams import Diagram, Cluster, Edge
from diagrams.generic.compute import Rack
from diagrams.generic.device import Tablet
from diagrams.onprem.compute import Server
from diagrams.onprem.client import Client, Users
from diagrams.onprem.container import Docker
from diagrams.k8s.compute import Pod
from diagrams.onprem.database import Postgresql
from diagrams.onprem.inmemory import Redis
from diagrams.aws.storage import S3
from diagrams.saas.cdn import Cloudflare

with Diagram(
    "TFE FDO on OpenShift Local (CRC) - macOS",
    show=False,
    filename="diagram_tfe_fdo_crc_openshift",
    outformat="png",
    direction="LR",
):
    # External user
    external_user = Users("External User")
    
    # Cloudflare public service
    cloudflare_public = Cloudflare("Cloudflare\n(Public)")

    # macOS host
    mac_host = Client("macOS host\n(Apple Mac)")

    # Hypervisor backend used by CRC (vfkit / Hypervisor.framework)
    hypervisor = Rack("Hypervisor.framework\n(vfkit)")

    # CRC VM (RHEL CoreOS)
    with Cluster("CRC VM (RHEL CoreOS)"):
        rhel_coreos = Server("RHEL CoreOS")

        # Inside the VM: CRI-O runtime hosting OpenShift
        with Cluster("OpenShift (single-node cluster)"):
            crio_runtime = Server("CRI-O runtime")
            openshift = Docker("OpenShift\n(Kubernetes)")

            # Kubernetes workloads running inside OpenShift
            with Cluster("OpenShift Workloads"):
                cloudflared_pod = Pod("cloudflared\n(tunnel)")
                tfe_pod = Pod("TFE\n(Terraform Enterprise)")
                postgres_pod = Postgresql("PostgreSQL\n(database)")
                seaweedfs_pod = S3("SeaweedFS\n(S3-compatible storage)")
                redis_pod = Redis("Redis\n(cache/session store)")

    # Relationships
    external_user >> Edge(label="HTTPS requests") >> cloudflare_public
    cloudflare_public >> Edge(label="Cloudflare tunnel") >> cloudflared_pod
    cloudflared_pod >> Edge(label="forwards to") >> tfe_pod
    mac_host >> Edge(label="crc start / manages") >> hypervisor
    hypervisor >> Edge(label="hosts") >> rhel_coreos
    rhel_coreos >> Edge(label="runs") >> crio_runtime
    crio_runtime >> Edge(label="hosts") >> openshift
    openshift >> [cloudflared_pod, tfe_pod, postgres_pod, seaweedfs_pod, redis_pod]
    
    # Internal pod relationships
    tfe_pod >> Edge(label="connects to") >> postgres_pod
    tfe_pod >> Edge(label="stores files") >> seaweedfs_pod
    tfe_pod >> Edge(label="caches sessions") >> redis_pod
