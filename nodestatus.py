# This script collects data on all nodes in the cluster that are not in "Ready" state and exports to a csv file
# Provision test resources using minikubenodes.sh script

import pandas as pd
from kubernetes import client, config
import os

# Load kube-config and initialize Kubernetes API client
config.load_kube_config()
v1 = client.CoreV1Api()

# Get the cluster name and the current context
contexts, active_context = config.list_kube_config_contexts()
cluster_name = active_context['context']['cluster']

# Get all nodes in the cluster
nodes = v1.list_node().items

# CSV Headers
header = ["Cluster", "Node Name", "Status in Cluster", "NodePool"]
data = []

# Define the CSV file
file_name = "node_status.csv"

def get_node_status(node):
    """Get the status of a node based on its conditions."""
    for condition in node.status.conditions:
        if condition.type == "Ready":
            if condition.status == "True":
                if node.spec.unschedulable:
                    return "Ready.SchedulingDisabled"
                return "Ready"
            else:
                # Not ready status logic
                if node.spec.unschedulable:
                    return "NotReady.SchedulingDisabled"
                return "NotReady"
    return "Unknown"

def get_node_environment_tag(node):
    """Retrieve the nodepool tag from the node labels."""
    return node.metadata.labels.get("kubernetes.io/nodepool", "Unknown")

# Gather data for nodes
for node in nodes:
    node_name = node.metadata.name
    node_status = get_node_status(node)
    node_environment_tag = get_node_environment_tag(node)

    # Append to data if node status is not "Ready"
    if node_status != "Ready":
        data.append([cluster_name, node_name, node_status, node_environment_tag])

# Create a DataFrame from the new data    
new_df = pd.DataFrame(data, columns=header)

# Check if file exists and is not empty    
if os.path.isfile(file_name) and os.path.getsize(file_name) > 0:
    try:
        existing_df = pd.read_csv(file_name)
        updated_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=["Node Name"], keep="last")
    except pd.errors.EmptyDataError:
        # If the existing file is empty, just use new_df
        updated_df = new_df
else:
    # If the file does not exist, use new_df directly
    updated_df = new_df

# Write the updated data to the CSV file
updated_df.to_csv(file_name, index=False)

print(f"Node statuses and environment tags have been updated in {file_name}")
