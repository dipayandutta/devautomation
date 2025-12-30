from kubernetes import client, config

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
	#pods = v1.list_pod_for_all_namespaces()
	#print("List all Pods")
	#print("---------------")
	#for p in pods.items:
	#	print(f"{p.metadata.namespace}--> {p.metadata.name} [{p.status.phase}]")
	pods = v1.list_pod_for_all_namespaces().items

	systemPods = []
	userPods = []
	
	for pod in pods:
		entry = f"{pod.metadata.namespace}-->{pod.metadata.name}[{pod.status.phase}]"
		entryCreationTimeStamp = pod.metadata.creation_timestamp

		if pod.metadata.namespace in SYSTEM_NAMESPACES:
			systemPods.append(entry)
		else:
			userPods.append((entry,entryCreationTimeStamp))


		print("List all Pods")
		print("---------------")
		print("System Pods")
		print("----------------")
		for pod in systemPods:
			print(pod)
		print("User Created Pods")
		print("------------------")
		for pod,timeStamp in userPods:
			print(f"{pod} | CreatedAt = {timeStamp}")
		
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


def main():
	v1,apps_v1 = getKubeConfig()
	detectClusterType(v1)
	getSVC(v1)
	getDeployment(apps_v1)
	getNodeDetails(v1)
	getPods(v1)
	getEvents(v1)
	getNamespaces(v1)
if __name__ == '__main__':
	main()
