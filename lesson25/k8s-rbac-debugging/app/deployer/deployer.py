"""
CI/CD Deployer Service
Simulates a deployment automation tool that interacts with Kubernetes API
"""
import os
import sys
import time
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KubernetesDeployer:
    """Deployment automation tool that requires specific RBAC permissions"""
    
    def __init__(self, namespace: str = "production"):
        self.namespace = namespace
        try:
            # Load in-cluster config when running as pod
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes configuration")
        except config.ConfigException:
            # Fall back to kubeconfig for local development
            config.load_kube_config()
            logger.info("Loaded kubeconfig configuration")
        
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()
        self.rbac_v1 = client.RbacAuthorizationV1Api()
    
    def check_permissions(self) -> dict:
        """
        Check if ServiceAccount has required permissions
        This demonstrates the auth can-i check programmatically
        """
        permissions = {
            'deployments': {'create': False, 'get': False, 'list': False, 'update': False},
            'services': {'create': False, 'get': False, 'list': False},
            'configmaps': {'create': False, 'get': False, 'list': False},
            'secrets': {'get': False, 'list': False}
        }
        
        # Test each permission
        auth_v1 = client.AuthorizationV1Api()
        
        for resource, verbs in permissions.items():
            for verb in verbs.keys():
                ssr = client.V1SelfSubjectAccessReview(
                    spec=client.V1SelfSubjectAccessReviewSpec(
                        resource_attributes=client.V1ResourceAttributes(
                            namespace=self.namespace,
                            verb=verb,
                            group='apps' if resource == 'deployments' else '',
                            resource=resource
                        )
                    )
                )
                
                try:
                    result = auth_v1.create_self_subject_access_review(ssr)
                    permissions[resource][verb] = result.status.allowed
                except ApiException as e:
                    logger.error(f"Failed to check permission {verb} {resource}: {e}")
        
        return permissions
    
    def deploy_application(self, app_name: str, image: str, replicas: int = 2) -> bool:
        """
        Deploy an application to Kubernetes
        This will fail if RBAC permissions are insufficient
        """
        logger.info(f"Attempting to deploy {app_name} to namespace {self.namespace}")
        
        # Create Deployment
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=app_name, namespace=self.namespace),
            spec=client.V1DeploymentSpec(
                replicas=replicas,
                selector=client.V1LabelSelector(
                    match_labels={"app": app_name}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": app_name}),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name=app_name,
                                image=image,
                                ports=[client.V1ContainerPort(container_port=8080)],
                                resources=client.V1ResourceRequirements(
                                    requests={"cpu": "100m", "memory": "128Mi"},
                                    limits={"cpu": "200m", "memory": "256Mi"}
                                )
                            )
                        ]
                    )
                )
            )
        )
        
        try:
            self.apps_v1.create_namespaced_deployment(
                namespace=self.namespace,
                body=deployment
            )
            logger.info(f"✓ Successfully created deployment {app_name}")
            return True
        except ApiException as e:
            logger.error(f"✗ Failed to create deployment {app_name}")
            logger.error(f"Status: {e.status}")
            logger.error(f"Reason: {e.reason}")
            logger.error(f"Body: {e.body}")
            
            # Parse the error to show which permission is missing
            if e.status == 403:
                logger.error("=" * 60)
                logger.error("RBAC PERMISSION DENIED")
                logger.error("=" * 60)
                logger.error("This ServiceAccount lacks permission to create deployments")
                logger.error(f"Namespace: {self.namespace}")
                logger.error("Required permission: create deployments.apps")
                logger.error("=" * 60)
            return False
    
    def create_service(self, app_name: str) -> bool:
        """Create a Service for the application"""
        logger.info(f"Attempting to create service {app_name}")
        
        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=app_name, namespace=self.namespace),
            spec=client.V1ServiceSpec(
                selector={"app": app_name},
                ports=[client.V1ServicePort(port=80, target_port=8080)],
                type="ClusterIP"
            )
        )
        
        try:
            self.core_v1.create_namespaced_service(
                namespace=self.namespace,
                body=service
            )
            logger.info(f"✓ Successfully created service {app_name}")
            return True
        except ApiException as e:
            logger.error(f"✗ Failed to create service {app_name}: {e.reason}")
            return False
    
    def get_deployment_status(self, app_name: str) -> dict:
        """Get deployment status - requires 'get' permission"""
        logger.info(f"Checking deployment status for {app_name}")
        
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=app_name,
                namespace=self.namespace
            )
            return {
                'replicas': deployment.spec.replicas,
                'ready_replicas': deployment.status.ready_replicas or 0,
                'available_replicas': deployment.status.available_replicas or 0
            }
        except ApiException as e:
            logger.error(f"✗ Failed to get deployment status: {e.reason}")
            if e.status == 403:
                logger.error("Missing permission: get deployments.apps")
            return {}
    
    def scale_deployment(self, app_name: str, replicas: int) -> bool:
        """Scale deployment - requires 'update' or 'patch' permission"""
        logger.info(f"Attempting to scale {app_name} to {replicas} replicas")
        
        try:
            # Read current deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name=app_name,
                namespace=self.namespace
            )
            
            # Update replica count
            deployment.spec.replicas = replicas
            
            # Apply update
            self.apps_v1.patch_namespaced_deployment(
                name=app_name,
                namespace=self.namespace,
                body=deployment
            )
            logger.info(f"✓ Successfully scaled {app_name}")
            return True
        except ApiException as e:
            logger.error(f"✗ Failed to scale deployment: {e.reason}")
            if e.status == 403:
                logger.error("Missing permission: update/patch deployments.apps")
            return False


def main():
    """Main deployment workflow"""
    print("=" * 60)
    print("CI/CD DEPLOYMENT AUTOMATION")
    print("=" * 60)
    
    namespace = os.getenv("TARGET_NAMESPACE", "production")
    deployer = KubernetesDeployer(namespace=namespace)
    
    # Step 1: Check permissions
    print("\n[1/5] Checking RBAC Permissions...")
    permissions = deployer.check_permissions()
    
    print("\nPermission Matrix:")
    for resource, verbs in permissions.items():
        print(f"\n  {resource}:")
        for verb, allowed in verbs.items():
            status = "✓" if allowed else "✗"
            print(f"    {status} {verb}")
    
    # Step 2: Deploy application
    print("\n[2/5] Deploying Application...")
    app_name = "sample-app"
    image = "nginx:1.21-alpine"
    
    deploy_success = deployer.deploy_application(app_name, image)
    
    if not deploy_success:
        print("\n" + "=" * 60)
        print("DEPLOYMENT FAILED - RBAC ISSUE DETECTED")
        print("=" * 60)
        print("\nDebugging Steps:")
        print("1. Check ServiceAccount: kubectl get sa -n ci-cd")
        print("2. Check RoleBindings: kubectl get rolebindings -n production")
        print("3. Check Role permissions: kubectl describe role deployer-role -n production")
        print(f"4. Test permission: kubectl auth can-i create deployments --as=system:serviceaccount:ci-cd:deployer -n {namespace}")
        sys.exit(1)
    
    # Step 3: Create Service
    print("\n[3/5] Creating Service...")
    deployer.create_service(app_name)
    
    # Step 4: Wait for deployment
    print("\n[4/5] Waiting for deployment to become ready...")
    time.sleep(5)
    
    # Step 5: Check status
    print("\n[5/5] Checking Deployment Status...")
    status = deployer.get_deployment_status(app_name)
    
    if status:
        print(f"\nDeployment Status:")
        print(f"  Desired Replicas: {status['replicas']}")
        print(f"  Ready Replicas: {status['ready_replicas']}")
        print(f"  Available Replicas: {status['available_replicas']}")
    
    print("\n" + "=" * 60)
    print("DEPLOYMENT COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()
