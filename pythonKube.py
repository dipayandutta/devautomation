from kubernetes import client, config


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

if __name__ == '__main__':
	main()
