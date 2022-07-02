#! /bin/sh

set -ex

# Create ecs
#
# Config envs firstly:
# 1. ALICLOUD_ACCESS_KEY 
# 2. ALICLOUD_SECRET_KEY
#
python ./create-ecs.py

# Wait for at least 20 seconds.
sleep 20

# Get IP address && private key
IP=$(cat ./ecs-ip.txt)
PRIVATE_KEY=/root/private-key.pem

# Add IP to SAN of kube-apiserver
# Reference: https://github.com/k3s-io/k3s/issues/3369
ssh -i $PRIVATE_KEY root@$IP \
  -o StrictHostKeyChecking=no \
  curl -k --resolve $IP:6443:127.0.0.1 https://$IP:6443/ping

# Init a k8s cluster
# Pass the SSH key file content to /root/private-key.pem
k3sup install --ip $IP \
  --tls-san $IP \
  --user root \
  --ssh-key $PRIVATE_KEY
