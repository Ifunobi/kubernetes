#!/bin/bash

# This script creates 12 minikube nodes with under nodepools: To be used to in contrast with a python script for sorting defective nodes in a cluster
# To be used with the nodestatus.py script and other scripts that need resource provisioning

#!/bin/bash

# Define variables
FRUIT_TYPES=("apple" "banana" "cherry" "mango" "orange") # Node pool labels
NODE_COUNT=12
CPUS=2
MEMORY=2048 

# Start Minikube with one control plane node and then scale to 6 worker nodes
echo "Starting Minikube with control plane node..."
minikube start --cpus=$CPUS --memory=${MEMORY}MB

# Adding 11 worker nodes
echo "Adding ${NODE_COUNT-1} worker nodes..."
for i in $(seq 2 $NODE_COUNT);
do 
    minikube node add --worker=true  # Start worker node with default settings
done

# Wait for Minikube to be up and running
echo "Waiting for Minikube to start..."
minikube status


# Capture the node names in an array
mapfile -t NodeNames < <(kubectl get nodes --no-headers | awk '{print $1}')

# Iterate over the node names
for i in "${!NodeNames[@]}"; do
  node="${NodeNames[$i]}"
  fruit_index=$((i % ${#FRUIT_TYPES[@]}))  # Use modulo to cycle through fruit types
  LABEL="kubernetes.io/nodepool=${FRUIT_TYPES[$fruit_index]}"  # Assign the fruit type
  
  echo "Labeling node ${node} with ${LABEL}"
  # Assign the nodepool labels to the nodes
  kubectl label node "${node}" "${LABEL}"
done


# Verify the labels
kubectl get nodes --show-labels



sleep 30
# Drain some nodes to Ensure some are in Ready.SchedulingDisabled state

for i in "${!NodeNames[@]}"; do
  # Skip the first two nodes (index 0 and 1)
  if (( i < 3 )); then
    continue
  fi

  node="${NodeNames[$i]}"  

  # Cordon the node to mark it as unschedulable
  echo "Cordoning node ${node}..."
  kubectl cordon "${node}"

  # Drain the node to gracefully evict pods and set it in Ready.SchedulingDisabled mode
  echo "Draining node ${node}..."
  kubectl drain "${node}" --ignore-daemonsets --force --delete-local-data
done
