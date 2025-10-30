# Kubernetes (k3s) deployment

## Prerequisites
- k3s or any Kubernetes cluster
- kubectl configured to the cluster

## Apply manifests
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/services-backend.yaml
kubectl apply -f k8s/frontend.yaml
```

## Access
- Configure DNS or hosts entry to point `tourism.local` to your node IP.
- k3s ships with Traefik; Ingress `tourism-ingress` exposes the app.

## Notes
- Images are referenced as `:latest`. Build and push to a registry accessible by the cluster, or use k3s local image import:
```bash
# example (Linux host)
docker build -t tourism-platform-auth-service:latest auth-service
k3s ctr images import <(docker save tourism-platform-auth-service:latest)
```
