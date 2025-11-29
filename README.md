# Flask + MongoDB on Kubernetes (Minikube)

A demo project deploying a Python Flask application with MongoDB as a backend, using Kubernetes (Minikube) for orchestration.  
This setup includes: authenticated MongoDB (StatefulSet), persistent storage (PV/PVC), inter‑pod networking via DNS, resource limits, and autoscaling (HPA).

---

## 📁 Repository Structure

```
.
├── app.py
├── Dockerfile
├── requirements.txt
├── K8s‑flask‑mongo‑yamls/
│   ├── namespace.yaml
│   ├── mongo‑headless-svc.yaml
│   ├── mongo-service.yaml
│   ├── mongo-statefulset.yaml
│   ├── mongo-volume.yaml
│   ├── flask-deployment.yaml
│   ├── flask-service.yaml
│   └── flask-hpa.yaml
└── README.md
```

---

## 🛠️ Prerequisites

- Docker & Docker Hub account
- Minikube
- kubectl
- Python 3.x

---

## 1. Build & Push Docker Image

```bash
docker build -t <docker-username>/flask-mongo-app:v1 .
docker login
docker push <docker-username>/flask-mongo-app:v1
```

---

## 2. Start Minikube & Enable Metrics Server

```bash
minikube start --driver=docker --memory=3072 --cpus=2
minikube addons enable metrics-server
kubectl -n kube-system get deployment metrics-server
```

---

## 3. Create Namespace & Secret

```bash
kubectl apply -f K8s-flask-mongo-yamls/namespace.yaml
kubectl -n flask-mongo create secret generic mongo-creds   --from-literal=MONGO_USER=admin   --from-literal=MONGO_PASS='YOUR_SECURE_PASSWORD'
```

---

## 4. Setup Persistent Storage

```bash
kubectl -n flask-mongo apply -f K8s-flask-mongo-yamls/mongo-volume.yaml
kubectl -n flask-mongo get pv,pvc
```

---

## 5. Deploy MongoDB StatefulSet & Services

```bash
kubectl -n flask-mongo apply -f mongo-headless-svc.yaml
kubectl -n flask-mongo apply -f mongo-statefulset.yaml
kubectl -n flask-mongo apply -f mongo-service.yaml
```

---

## 6. Deploy Flask App

```bash
kubectl -n flask-mongo apply -f flask-deployment.yaml
kubectl -n flask-mongo apply -f flask-service.yaml
```

Access:

```bash
minikube service -n flask-mongo flask-service --url
```

---

## 7. DNS Resolution

Flask communicates with MongoDB using:

```
mongo:27017
```

Kubernetes DNS resolves service names inside the cluster.

---

## 8. Resource Requests & Limits

```yaml
resources:
  requests:
    cpu: "200m"
    memory: "250Mi"
  limits:
    cpu: "500m"
    memory: "500Mi"
```

---

## 9. Autoscaling (HPA)

```bash
kubectl -n flask-mongo apply -f flask-hpa.yaml
kubectl -n flask-mongo get hpa -w
```

Test load:

```bash
kubectl run loadgen --image=radial/busyboxplus:curl --restart=Never --     /bin/sh -c "while true; do curl http://flask-service:8080 > /dev/null; done"
```

---

## 10. Included for Submission

- Dockerfile
- Kubernetes YAMLs
- README.md
- Autoscaling screenshots
- Testing explanations

---

## 11. Troubleshooting

- Ensure metrics‑server is running.
- Increase Minikube resources if pods crash.
- Fix image tags to avoid ImagePullBackOff.

---

## ✅ Summary

This project demonstrates a complete Flask + MongoDB deployment on Kubernetes with persistent storage, secure authentication, autoscaling, and DNS-based inter-pod communication.
