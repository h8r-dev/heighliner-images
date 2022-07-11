#! /bin/sh

set -ex

# Create ecs
#
# Config envs firstly:
# 1. ALICLOUD_ACCESS_KEY 
# 2. ALICLOUD_SECRET_KEY
#
python ./create-ecs.py

# Wait for 5 seconds
sleep 5

# Get IP address && private key
IP=$(cat ./ecs-ip.txt)
PRIVATE_KEY=/root/.ssh/private-key.pem

# Make sure the server is running.
while ! ssh -i $PRIVATE_KEY root@$IP -o StrictHostKeyChecking=no echo "hi"; do
  echo "Waiting for the server: $IP to be ready!"
  sleep 3
done

# Add IP to SAN of kube-apiserver
# Reference: https://github.com/k3s-io/k3s/issues/3369
# Check if $IP existed in SAN records, if not, add it until it is found in record.
while ! ssh -i $PRIVATE_KEY root@$IP -o StrictHostKeyChecking=no kubectl -n kube-system get secret k3s-serving -o yaml | grep $IP; do
  echo "Adding $IP to SAN of kube-apiserver"
  ssh -i $PRIVATE_KEY root@$IP \
    -o StrictHostKeyChecking=no \
    curl -k --resolve $IP:6443:127.0.0.1 https://$IP:6443/ping
  sleep 3
done

# Init a k8s cluster
# Pass the SSH key file content to /root/private-key.pem
# k3sup will store kubeconfig content to ./kubeconfig file.
k3sup install --ip $IP \
  --tls-san $IP \
  --user root \
  --ssh-key $PRIVATE_KEY

# Send kubeconfig return to callback service.
# You should preSet CALLBACK_URL, CALLBACK_TOKEN envs.
#
python ./request.py
