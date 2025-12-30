from kubernetes import client, config
from google import genai
import os

gemClient = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_NAMESPACES = {
	"kube-system",
	"kube-public",
	"kube-node-lease"
}

def getKubeConfig():
	try:
		config.load_kube_config()
		print("Loaded the kubeconfig")
	except ConfigException:
		try:
			config.load_incluster_config()
			print("Loaded the incluster kubeconfig")
		except ConfigException as e:
			raise RuntimeError("Failed to Load the kube config")

	v1 = client.CoreV1Api()
	apps_v1 = client.AppsV1Api()
	return v1,apps_v1

def collect_cluster_state(v1, apps_v1):
    output = []

    # Nodes
    nodes = v1.list_node().items
    output.append(f"Number of Nodes: {len(nodes)}")
    for n in nodes:
        output.append(f"Node: {n.metadata.name}")

    # Services
    output.append("\nServices:")
    svcs = v1.list_service_for_all_namespaces().items
    for s in svcs:
        output.append(f"{s.metadata.namespace}->{s.metadata.name}")

    # Deployments
    output.append("\nDeployments:")
    deploys = apps_v1.list_deployment_for_all_namespaces().items
    for d in deploys:
        output.append(f"{d.metadata.namespace}->{d.metadata.name}")

    # Pods
    output.append("\nPods:")
    pods = v1.list_pod_for_all_namespaces().items
    for p in pods:
        output.append(
            f"{p.metadata.namespace}->{p.metadata.name} "
            f"[{p.status.phase}] "
            f"CreatedAt={p.metadata.creation_timestamp}"
        )

    return "\n".join(output)


def ask_gemini_with_cluster_context(cluster_state, user_prompt):
    prompt = f"""
You are a Kubernetes expert assistant.

Below is the current Kubernetes cluster state:

====================
{cluster_state}
====================

User request:
"{user_prompt}"

Your task:
1. Explain what the user wants
2. Suggest the correct Kubernetes approach
3. Warn if there are risks (SNO cluster, resource usage, etc.)
4. Do NOT execute commands
"""

    response = gemClient.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text

def getNodeDetails(v1):
	nodes = v1.list_node().items
	for node in nodes:
		nodeStatus = [c.status for c in node.status.conditions if c.type=="Ready"][0]
		print("CPU: ",node.status.capacity.get("CPU"))
		print("OS: ",node.status.node_info.os_image)
		print("Runtime Version: ",node.status.node_info.container_runtime_version)
	print(nodeStatus)
	if nodeStatus == True:
		print("Nodes are Ready")

def getNamespaces(v1):
	print("List of all Namespaces")
	print("------------------------")
	namespaces = v1.list_namespace().items
	for namespace in namespaces:
		print(namespace.metadata.name)

def getPods(v1):
	pods = v1.list_pod_for_all_namespaces()
	print("List all Pods")
	print("---------------")
	for p in pods.items:
		print(f"{p.metadata.namespace}--> {p.metadata.name} [{p.status.phase}]")

		
def getEvents(v1):
	events = v1.list_event_for_all_namespaces()
	print("List all Events")
	print("------------------")
	for event in events.items:
		print(f"{event.metadata.namespace} -> {event.reason}: {event.message}")

def detectClusterType(v1):
	nodes = v1.list_node().items

	numberOfNodes = len(nodes)

	if numberOfNodes == 1:
		print("This is a sinle node Kubernetes")
	else:
		print(f"Number of nodes are {numberOfNodes}")
	
	for node in nodes:
		print("Name of the Node is -->",node.metadata.name)

def getSVC(v1):
	svcs = v1.list_service_for_all_namespaces()
	print("All Services")
	for svc in svcs.items:
		print(f"{svc.metadata.namespace}-->{svc.metadata.name}")


def getDeployment(apps_v1):
	deployments = apps_v1.list_deployment_for_all_namespaces()

	print("All Deployments")
	for deploy in deployments.items:
		print(f"{deploy.metadata.namespace}-->{deploy.metadata.name}")

def gemini(v1,apps_v1):
	print("\nEnter prompt for Gemini:")
	user_prompt = input("> ")

	cluster_state = collect_cluster_state(v1, apps_v1)

	gemini_response = ask_gemini_with_cluster_context(
    cluster_state,
    user_prompt
	)

	print("\nGemini Response")
	print("----------------")
	print(gemini_response)


def main():
	v1,apps_v1 = getKubeConfig()
	detectClusterType(v1)
	getSVC(v1)
	getDeployment(apps_v1)
	getNodeDetails(v1)
	getPods(v1)
	getEvents(v1)
	getNamespaces(v1)
	gemini(v1,apps_v1)
	collect_cluster_state(v1, apps_v1)
if __name__ == '__main__':
	main()
