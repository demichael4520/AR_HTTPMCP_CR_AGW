# Agent Gateway Integration Validation Guide

This deployment guide outlines the steps required to configure and validate **Agent Gateway** integration for an MCP Client Agent running on **Vertex AI Agent Runtime** using **Streamable HTTP** transport.

### Environment Setup
```bash
export PROJ_ID=your-project-id
```

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

## 🚀 Next Steps (Agent Gateway Setup)
- [x] **Create VPC Network (`agent-vpc`)**
- [x] **Create Subnet (`network-attachment`)**
- [x] **Create PSC Google APIs Endpoint (`172.16.10.10`)**
- [x] **Create Private DNS Zone (`cloud-run`)**
- [x] **Create DNS A Record (`*.run.app.`)**
- [x] **Enable DNS Query Logging**
- [ ] **Create Proxy-Only Subnet**: Provision a proxy-only subnet for the Agent Gateway.
- [ ] **Deploy the Agent Gateway**: Create the gateway resource in `AGENT_TO_ANYWHERE` (egress) mode attached to `agent-vpc`.
- [ ] **Deploy the Client Agent**: Configure `.agent_engine_config.json` with your gateway resource name and deploy via `adk deploy`.
