# Agent Gateway Integration Validation Guide

This deployment guide outlines the steps required to configure and validate **Agent Gateway** integration for an MCP Client Agent running on **Vertex AI Agent Runtime** using **Streamable HTTP** transport.

### Environment Setup
```bash
export PROJ_ID=your-project-id
```

### ⚠️ Prerequisites
- A deployed **Agent Gateway** configured in `AGENT_TO_ANYWHERE` (egress) mode.
- Grant **Compute Admin** (`roles/compute.admin`) to the Vertex AI Service Agent (`service-<PROJECT_NUMBER>@gcp-sa-aiplatform.iam.gserviceaccount.com`).
- Grant **DNS Peer** (`roles/dns.peer`) to the Vertex AI Service Agent and Service Extensions Service Agent (`service-<PROJECT_NUMBER>@gcp-sa-dep.iam.gserviceaccount.com`).

---

## 🛠️ Step 1: Create the VPC Network (`agent-vpc`)

Create a dedicated custom-mode VPC network named `agent-vpc` within your project:

```bash
gcloud compute networks create agent-vpc \
  --subnet-mode=custom \
  --project=${PROJ_ID}
```

---

## 🛠️ Step 2: Create the Subnet (`network-attachment`)

Create a subnet named `network-attachment` in region `us-east1` with Private Google Access enabled:

```bash
gcloud compute networks subnets create network-attachment \
  --network=agent-vpc \
  --range=192.168.10.0/28 \
  --region=us-east1 \
  --enable-private-ip-google-access \
  --project=${PROJ_ID}
```

---

## 🛠️ Step 3: Create PSC Google APIs Endpoint (`172.16.10.10`)

Reserve a global internal IP address and create a Private Service Connect (PSC) endpoint targeting all Google APIs (`all-apis` bundle):

```bash
# 1. Reserve the IP address
gcloud compute addresses create psc-google-apis-ip \
  --global \
  --purpose=PRIVATE_SERVICE_CONNECT \
  --addresses=172.16.10.10 \
  --network=agent-vpc \
  --project=${PROJ_ID}

# 2. Create the PSC forwarding rule
gcloud compute forwarding-rules create pscgoogleapis \
  --global \
  --network=agent-vpc \
  --address=psc-google-apis-ip \
  --target-google-apis-bundle=all-apis \
  --project=${PROJ_ID}
```

---

## 🛠️ Step 4: Create Private DNS Zone (`cloud-run`)

Create a private Cloud DNS managed zone named `cloud-run` mapped to `run.app.` within `agent-vpc`:

```bash
gcloud dns managed-zones create cloud-run \
  --description="Private DNS zone for Cloud Run" \
  --dns-name="run.app." \
  --visibility=private \
  --networks=agent-vpc \
  --project=${PROJ_ID}
```

---

## 🛠️ Step 5: Create DNS A Record (`*.run.app.`)

Create a wildcard DNS A record in the `cloud-run` zone pointing `*.run.app.` to the PSC endpoint IP address (`172.16.10.10`):

```bash
gcloud dns record-sets create "*.run.app." \
  --zone=cloud-run \
  --type=A \
  --ttl=300 \
  --rrdatas=172.16.10.10 \
  --project=${PROJ_ID}
```

---

## 🛠️ Step 6: Enable DNS Query Logging

Create a DNS policy enabling query logging on `agent-vpc` for troubleshooting:

```bash
gcloud dns policies create agent-dns-policy \
  --description="DNS logging policy for agent-vpc" \
  --networks=agent-vpc \
  --enable-logging \
  --project=${PROJ_ID}
```

---

## 🛠️ Step 7: Create PSC Network Attachment

Create a Private Service Connect (PSC) Network Attachment named `agent-attachment` in region `us-east1` allowing automatic acceptance from any project:

```bash
gcloud compute network-attachments create agent-attachment \
  --region=us-east1 \
  --subnets=network-attachment \
  --connection-preference=ACCEPT_AUTOMATIC \
  --project=${PROJ_ID}
```

---

## 🛠️ Step 8: Create Egress Firewall Rule (`agent-gateway-egress-log`)

Create an egress firewall rule with logging enabled to monitor traffic egressing from Agent Gateway to the VPC:

```bash
gcloud compute firewall-rules create agent-gateway-egress-log \
  --network=agent-vpc \
  --direction=EGRESS \
  --priority=100 \
  --action=ALLOW \
  --rules=all \
  --destination-ranges=0.0.0.0/0 \
  --enable-logging \
  --project=${PROJ_ID}
```

---

## 🛠️ Step 9: Configure and Patch Agent Gateway (`networkConfig`)

Attach your Private Service Connect Network Attachment and Cloud DNS Peering configuration directly to your regional Agent Gateway:

1. Create a configuration file named `patch-gateway.yaml`:
```yaml
name: agw-codelab2-us-east1-ata
protocols:
  - MCP
googleManaged:
  governedAccessPath: AGENT_TO_ANYWHERE
registries:
  - "//agentregistry.googleapis.com/projects/YOUR_PROJECT_ID/locations/us-east1"
networkConfig:
  egress:
    networkAttachment: projects/YOUR_PROJECT_ID/regions/us-east1/networkAttachments/agent-attachment
  dnsPeeringConfig:
    domains:
      - run.app.
    targetProject: YOUR_PROJECT_ID
    targetNetwork: projects/YOUR_PROJECT_ID/global/networks/agent-vpc
```

2. Import the patched configuration:
```bash
gcloud alpha network-services agent-gateways import agw-codelab2-us-east1-ata \
  --source=patch-gateway.yaml \
  --location=us-east1 \
  --project=${PROJ_ID}
```

---

## 🛠️ Step 10: Configure Agent Runtime (`.agent_engine_config.json`)

Update your [`.agent_engine_config.json`](.agent_engine_config.json) to enable **Agent Identity** and route outbound traffic through your managed **Agent Gateway**:

```json
{
  "identity_type": "AGENT_IDENTITY",
  "agent_gateway_config": {
    "agent_to_anywhere_config": {
      "agent_gateway": "projects/YOUR_PROJECT_ID/locations/us-east1/agentGateways/YOUR_GATEWAY_NAME"
    }
  },
  "env_vars": {
    "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true"
  }
}
```

*Note: Replace `YOUR_PROJECT_ID` and `YOUR_GATEWAY_NAME` with your actual project ID and Gateway name.*

### Grant Required Roles to Agent Identity PrincipalSet
When `"identity_type": "AGENT_IDENTITY"` is enabled, grant the following roles to the managed `PrincipalSet` (`principalSet://agents.global.org-ORGANIZATION_ID.system.id.goog/attribute.platformContainer/aiplatform/projects/PROJECT_NUMBER`):
- `roles/aiplatform.user`
- `roles/aiplatform.agentDefaultAccess`
- `roles/agentregistry.viewer`
- `roles/logging.logWriter`
- `roles/monitoring.metricWriter`
- `roles/browser`

---

## 🚀 Next Steps (Agent Gateway Setup)
- [x] **Create VPC Network (`agent-vpc`)**
- [x] **Create Subnet (`network-attachment`)**
- [x] **Create PSC Google APIs Endpoint (`172.16.10.10`)**
- [x] **Create Private DNS Zone (`cloud-run`)**
- [x] **Create DNS A Record (`*.run.app.`)**
- [x] **Enable DNS Query Logging**
- [x] **Create PSC Network Attachment**
- [x] **Create Egress Firewall Rule (`agent-gateway-egress-log`)**
- [x] **Configure & Patch Agent Gateway (`networkConfig`)**
- [x] **Configure Agent Runtime**: Update `.agent_engine_config.json` with user-supplied entries.
- [x] **Deploy the Client Agent**: Run `adk deploy agent_engine` to push the agent.

---

## 🔍 Verification (DNS Peering & Egress Traffic)

You can verify that DNS peering and network egress are functioning properly via Cloud Logging:

1. **Verify DNS Peering**:
   Check Cloud DNS query logs to confirm resolution of `*.run.app.` originating across peering from the Vertex AI tenant network:
   ```log
   resource.type="dns_query"
   jsonPayload.queryName="mcp-weather-server-431967288103.us-east1.run.app."
   ```

2. **Verify Network Attachment & Egress Firewall**:
   Check Cloud Firewall egress logs to confirm outgoing connections from Agent Runtime hitting the internal Private Service Connect IP (`172.16.10.10`):
   ```log
   resource.type="gce_subnetwork"
   jsonPayload.rule_details.reference="projects/deepakmichael-codelab2/global/firewalls/agent-gateway-egress-log"
   ```

3. **Verify Agent Gateway Routing (`agentGatewayConfig`)**:
   Query the deployed runtime API to verify that egress traffic is configured to route through your Agent Gateway:
   ```bash
   curl -s -X GET \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     "https://us-east1-aiplatform.googleapis.com/v1beta1/projects/deepakmichael-codelab2/locations/us-east1/reasoningEngines/2534858087139901440" \
     | jq '.spec.deploymentSpec.agentGatewayConfig'
   ```
