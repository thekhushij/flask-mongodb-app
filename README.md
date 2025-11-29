
# Flask + MongoDB on Kubernetes (minikube) — Assignment README

**Project:** Flask application that stores/retrieves JSON data in MongoDB, deployed to a local Kubernetes (Minikube) cluster with authentication, storage, autoscaling, DNS, and resource management.

This README explains:
- how to build and push the Docker image,
- how to deploy the Kubernetes manifests,
- how to enable authentication and storage for MongoDB (StatefulSet + PV/PVC),
- how DNS and inter-pod communication work,
- resource requests/limits and HPA (autoscaling) setup and testing,
- verification and troubleshooting commands,
- design choices and testing summary.


---

## Repository layout (what I created)
```
.
├─ app.py
├─ Dockerfile
├─ requirements.txt
├─ K8s-flask-mongo-yamls/
│  ├─ namespace.yaml
│  ├─ mongo-headless-svc.yaml
│  ├─ mongo-service.yaml
│  ├─ mongo-statefulset.yaml
│  ├─ mongo-volume.yaml       # PV + PVC
│  ├─ flask-deployment.yaml
│  ├─ flask-service.yaml
│  ├─ flask-hpa.yaml
```

---

## 1) Build and push Docker image (already pushed in my run)
Replace `<your-docker-username>` and `<tag>` accordingly.

```bash
# build
docker build -t <your-docker-username>/flask-mongo-app:v1 .

# login (Docker Hub)
docker login

# push
docker push <your-docker-username>/flask-mongo-app:v1
```

**I used**: `thekhushij/flask-mongo-app:v1` as the image in the deployment manifest. Change it if you push to another repo.

---

## 2) Minikube & local Kubernetes setup (macOS M1 notes)
- I used Docker Desktop and Minikube (driver: docker).
- On Apple Silicon with limited RAM/CPU, ensure minikube started with enough resources, e.g.:
```bash
minikube start --driver=docker --memory=3072 --cpus=2
```
- If minikube fails due to CPU limits, increase CPU in Docker Desktop preferences or use `--cpus` when starting minikube.

### Install/enable metrics-server (required for HPA)
```bash
minikube addons enable metrics-server
# verify
kubectl -n kube-system get deployment metrics-server
```

---

## 3) Create namespace
```bash
kubectl apply -f K8s-flask-mongo-yamls/namespace.yaml
# verify
kubectl get ns
```

---

## 4) Create MongoDB credentials (Kubernetes Secret)
**Do not** commit plaintext credentials. Create secret in the namespace:

```bash
kubectl -n flask-mongo create secret generic mongo-creds \
  --from-literal=MONGO_USER=admin \
  --from-literal=MONGO_PASS='SOME_STRONG_PASSWORD'
```

(If you created it already in your terminal, skip this step.)

---

## 5) Persistent volume (PV) and PersistentVolumeClaim (PVC)
Apply PV/PVC manifest (I created `mongo-volume.yaml`):

```bash
kubectl -n flask-mongo apply -f K8s-flask-mongo-yamls/mongo-volume.yaml
kubectl -n flask-mongo get pv,pvc
```

> In minikube the storage class may be `standard`. For a manual pv example I used `storageClassName: manual`. Adjust for your environment.

---

## 6) MongoDB StatefulSet + Services
Order matters — apply headless service, statefulset, and cluster service.

```bash
kubectl -n flask-mongo apply -f K8s-flask-mongo-yamls/mongo-headless-svc.yaml
kubectl -n flask-mongo apply -f K8s-flask-mongo-yamls/mongo-statefulset.yaml
kubectl -n flask-mongo apply -f K8s-flask-mongo-yamls/mongo-service.yaml
kubectl -n flask-mongo get sts,po,svc -o wide
```

**Notes:**
- The StatefulSet config includes `securityContext` and `command` to enable auth (if you use a Mongo image that requires init). Another way: start MongoDB with `--auth` and create admin user using an init container or Kubernetes Job that runs `mongo` commands to create the user.
- The `mongo-host` used by the Flask app is `mongo:27017` (service name `mongo` in same namespace). Kubernetes DNS resolves `mongo` to the service cluster IP automatically — this is how pods find each other.

---

## 7) Flask Deployment + Service
Apply the Flask deployment and service:

```bash
kubectl -n flask-mongo apply -f K8s-flask-mongo-yamls/flask-deployment.yaml
kubectl -n flask-mongo apply -f K8s-flask-mongo-yamls/flask-service.yaml
```

Verify pods and service:
```bash
kubectl -n flask-mongo get deploy,po,svc -o wide
kubectl -n flask-mongo get endpoints
```

### Accessing Flask locally
- Using `kubectl port-forward`:
```bash
kubectl -n flask-mongo port-forward svc/flask-service 8080:8080
# then curl http://localhost:8080/ or http://localhost:8080/data
```
- Or with minikube:
```bash
minikube service -n flask-mongo flask-service --url
```

---

## 8) HPA (Horizontal Pod Autoscaler)
Apply HPA:

```bash
kubectl -n flask-mongo apply -f K8s-flask-mongo-yamls/flask-hpa.yaml
kubectl -n flask-mongo get hpa -w
kubectl -n flask-mongo describe hpa flask-hpa
```

**Important:** HPA requires the metrics API (metrics-server). If HPA reports `FailedGetResourceMetric` or cannot fetch metrics, ensure `metrics-server` is running:
```bash
kubectl -n kube-system get deployment metrics-server
kubectl -n kube-system get pods | grep metrics
kubectl top pods -n flask-mongo
```

**Testing autoscaling:**
Simulate load to raise CPU:
- Option A (run a load pod using `stress`):
```bash
kubectl -n flask-mongo run -i --tty load-generator --image=busybox -- /bin/sh
# inside pod, use a small busy loop or install stress. Example (busyloop in shell):
while true; do cat /dev/urandom > /dev/null; done
```
- Option B (use `kubectl run` to create multiple busy containers consuming CPU).
- Option C (use `hey` or `wrk` from your machine against exposed service).

Watch HPA and replicas:
```bash
kubectl -n flask-mongo get hpa -w
kubectl -n flask-mongo get deploy -o wide
kubectl -n flask-mongo get pods -o wide
```

Take screenshots showing:
- `kubectl top pods` (before and during load)
- `kubectl get hpa` showing CPU% and replica count
- `kubectl get deploy` showing scaled replica count

---

## 9) DNS resolution explanation (what to include in report)
- Kubernetes creates internal DNS records for services. A service named `mongo` in `flask-mongo` namespace becomes resolvable inside the cluster as:
  - `mongo` (within same namespace)
  - `mongo.flask-mongo` (from other namespaces)
  - `mongo.flask-mongo.svc.cluster.local` (full DNS)
- When Flask pod resolves `mongo`, it receives the cluster IP for the MongoDB service. Requests are then load-balanced to MongoDB pod(s).
- For StatefulSets, a headless service (clusterIP: None) allows stable network IDs (`<statefulset-name>-0.mongo-headless`, etc.), useful for MongoDB clusters and ordered startup.

---

## 10) Resource requests and limits (what I applied)
**Flask pod** (example used in `flask-deployment.yaml`):
```yaml
resources:
  requests:
    cpu: "200m"
    memory: "250Mi"
  limits:
    cpu: "500m"
    memory: "500Mi"
```
**Why:** `requests` tell the scheduler how much to reserve; `limits` bound the usage. HPA uses CPU utilization relative to requested CPU for scaling.

---

## 11) Security & design choices
- **Secrets**: DB creds are stored in a Kubernetes `Secret` (`mongo-creds`) and referenced via `env.valueFrom.secretKeyRef`.
- **StatefulSet** vs Deployment for DB: StatefulSet gives stable identity and stable storage mapping; better for databases.
- **Headless service**: Used for stable DNS names and direct pod access (if required).
- **PV/PVC**: Ensures MongoDB data persists across pod restarts.
- **Metrics server**: Required for HPA — enabled via `minikube addons enable metrics-server`.
- **Autoscaling**: HPA configured to scale based on CPU utilization (target 70%). Min replicas: 2, Max replicas: 5 (as requested).

---

## 12) Troubleshooting & common errors
- `resource name may not be empty` → check YAML `metadata.name` and ensure correct indentation.
- `failed to get cpu utilization` or `pods.metrics.k8s.io not found` → enable metrics-server and wait for it to be ready.
- `image pull` errors → ensure the image exists and is public or Docker credentials available.
- YAML parse errors → check indentation, hyphen placement, and scalar types (strings vs numbers). Use `yamllint` or `kubectl apply --dry-run=client -f <file>`.

---

## 13) Verification commands (quick checklist)
```bash
# namespace
kubectl get ns

# secrets
kubectl -n flask-mongo get secret mongo-creds -o yaml

# statefulset & pods
kubectl -n flask-mongo get sts,pods,svc,pvc -o wide

# logs
kubectl -n flask-mongo logs deploy/flask -l app=flask

# HPA
kubectl -n flask-mongo get hpa
kubectl -n flask-mongo describe hpa flask-hpa

# metrics
kubectl top pods -n flask-mongo
kubectl top nodes

# port-forward to test endpoints
kubectl -n flask-mongo port-forward svc/flask-service 8080:8080
curl -X GET http://localhost:8080/
curl -X POST -H "Content-Type: application/json" -d '{"sampleKey":"sampleValue"}' http://localhost:8080/data
```

---

## 14) What to include in the final submission (README + evidence)
- All YAML manifests used (.yaml files)
- Dockerfile and instructions to build/push
- Steps executed (commands) — ordered sequence so reviewer can reproduce
- Screenshots:
  - `kubectl get pods` and `kubectl get svc` after deployment
  - `kubectl top pods` before/during/after load
  - `kubectl get hpa` and `kubectl describe hpa` showing scaling events
  - logs showing Flask app connected to the DB (if applicable)
- Small explanation (1–2 paragraphs) of DNS resolution and resource requests/limits
- Design choices and alternatives considered

---



