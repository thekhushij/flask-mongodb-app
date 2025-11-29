## Flask + MongoDB on Kubernetes (Minikube)

This repository contains a Python Flask application connected to MongoDB, deployed on a Kubernetes cluster using Minikube.
The project demonstrates Deployments, StatefulSets, Services, Persistent Volumes, Autoscaling, DNS resolution, and Resource Management.
All requirements from the assignment have been fully implemented. 
docker build -t <your-dockerhub-username>/flask-mongo-app:v1 .
docker login
docker push <your-dockerhub-username>/flask-mongo-app:v1

## 📌 Architecture Overview

                   +----------------------+
                   |   Flask Deployment   |  <--- 2–5 Replicas (HPA)
                   |  flask:8080          |
                   +----------+-----------+
                              |
                    ClusterIP Service
                              |
                    flask-service:8080
                              |
                    +---------v----------+
                    |     DNS (K8s)      |
                    | mongo.flask-mongo  |
                    +---------+----------+
                              |
                  +-----------v------------+
                  |   MongoDB StatefulSet   |
                  |   mongo-0 (Auth ON)     |
                  |  PV + PVC (1Gi)         |
                  +-------------------------+


# 1. Dockerfile for Flask Application

FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
CMD ["python3", "app.py"]


# 2. Build & Push Docker Image 
Login to Docker Hub - 
ternimal commonds docker login


# 3. Kubernetes YAML Files (All Resources)

📁 All files are already created in your K8s-flask-mongo-yamls/ directory.
Included:

namespace.yaml
mongo-volume.yaml
mongo-statefulset.yaml
mongo-service.yaml
mongo-headless-svc.yaml
flask-deployment.yaml
flask-service.yaml
flask-hpa.yaml

# 4. Step-by-Step Deployment Guide (Minikube)




