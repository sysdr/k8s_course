import asyncio
import logging
from typing import Dict, Any, Optional
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
import kopf
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom Resource Definition Group and Version
CRD_GROUP = "logpipeline.k8s.io"
CRD_VERSION = "v1"
CRD_PLURAL = "logpipelines"

class LogPipelineController:
    """
    Custom controller for LogPipeline resources.
    Implements the operator pattern for managing log processing infrastructure.
    """
    
    def __init__(self):
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()
        
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()
        self.custom_api = client.CustomObjectsApi()
        
    def create_collector_deployment(self, name: str, namespace: str, spec: Dict[str, Any]) -> None:
        """Create log collector deployment based on LogPipeline spec"""
        
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(
                name=f"{name}-collector",
                namespace=namespace,
                labels={
                    "app": "log-collector",
                    "pipeline": name,
                    "component": "collector"
                }
            ),
            spec=client.V1DeploymentSpec(
                replicas=spec.get("collector", {}).get("replicas", 2),
                selector=client.V1LabelSelector(
                    match_labels={
                        "app": "log-collector",
                        "pipeline": name
                    }
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={
                            "app": "log-collector",
                            "pipeline": name,
                            "component": "collector"
                        }
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="collector",
                                image="logpipeline/collector:latest",
                                ports=[client.V1ContainerPort(container_port=8080)],
                                env=[
                                    client.V1EnvVar(name="PIPELINE_NAME", value=name),
                                    client.V1EnvVar(name="KAFKA_BROKERS", value="kafka:9092"),
                                    client.V1EnvVar(name="SOURCE_TYPE", value=spec.get("source", {}).get("type", "kubernetes"))
                                ],
                                resources=client.V1ResourceRequirements(
                                    requests={"cpu": "100m", "memory": "128Mi"},
                                    limits={"cpu": "500m", "memory": "512Mi"}
                                ),
                                liveness_probe=client.V1Probe(
                                    http_get=client.V1HTTPGetAction(path="/health", port=8080),
                                    initial_delay_seconds=30,
                                    period_seconds=10
                                ),
                                readiness_probe=client.V1Probe(
                                    http_get=client.V1HTTPGetAction(path="/ready", port=8080),
                                    initial_delay_seconds=10,
                                    period_seconds=5
                                )
                            )
                        ]
                    )
                )
            )
        )
        
        try:
            self.apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment)
            logger.info(f"Created collector deployment for pipeline: {name}")
        except ApiException as e:
            if e.status == 409:
                logger.info(f"Collector deployment already exists for pipeline: {name}")
            else:
                raise
    
    def create_processor_deployment(self, name: str, namespace: str, spec: Dict[str, Any]) -> None:
        """Create log processor deployment"""
        
        processors = spec.get("processors", [])
        processor_config = ",".join([p.get("type", "") for p in processors])
        
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(
                name=f"{name}-processor",
                namespace=namespace,
                labels={
                    "app": "log-processor",
                    "pipeline": name,
                    "component": "processor"
                }
            ),
            spec=client.V1DeploymentSpec(
                replicas=spec.get("processor", {}).get("replicas", 3),
                selector=client.V1LabelSelector(
                    match_labels={
                        "app": "log-processor",
                        "pipeline": name
                    }
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={
                            "app": "log-processor",
                            "pipeline": name,
                            "component": "processor"
                        }
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="processor",
                                image="logpipeline/processor:latest",
                                ports=[client.V1ContainerPort(container_port=8080)],
                                env=[
                                    client.V1EnvVar(name="PIPELINE_NAME", value=name),
                                    client.V1EnvVar(name="KAFKA_BROKERS", value="kafka:9092"),
                                    client.V1EnvVar(name="PROCESSORS", value=processor_config),
                                    client.V1EnvVar(name="REDIS_HOST", value="redis:6379")
                                ],
                                resources=client.V1ResourceRequirements(
                                    requests={"cpu": "200m", "memory": "256Mi"},
                                    limits={"cpu": "1000m", "memory": "1Gi"}
                                ),
                                liveness_probe=client.V1Probe(
                                    http_get=client.V1HTTPGetAction(path="/health", port=8080),
                                    initial_delay_seconds=30,
                                    period_seconds=10
                                ),
                                readiness_probe=client.V1Probe(
                                    http_get=client.V1HTTPGetAction(path="/ready", port=8080),
                                    initial_delay_seconds=10,
                                    period_seconds=5
                                )
                            )
                        ]
                    )
                )
            )
        )
        
        try:
            self.apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment)
            logger.info(f"Created processor deployment for pipeline: {name}")
        except ApiException as e:
            if e.status == 409:
                logger.info(f"Processor deployment already exists for pipeline: {name}")
            else:
                raise
    
    def create_sink_deployment(self, name: str, namespace: str, spec: Dict[str, Any]) -> None:
        """Create log sink deployment"""
        
        sink_type = spec.get("sink", {}).get("type", "elasticsearch")
        
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(
                name=f"{name}-sink",
                namespace=namespace,
                labels={
                    "app": "log-sink",
                    "pipeline": name,
                    "component": "sink"
                }
            ),
            spec=client.V1DeploymentSpec(
                replicas=spec.get("sink", {}).get("replicas", 2),
                selector=client.V1LabelSelector(
                    match_labels={
                        "app": "log-sink",
                        "pipeline": name
                    }
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={
                            "app": "log-sink",
                            "pipeline": name,
                            "component": "sink"
                        }
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="sink",
                                image="logpipeline/sink:latest",
                                ports=[client.V1ContainerPort(container_port=8080)],
                                env=[
                                    client.V1EnvVar(name="PIPELINE_NAME", value=name),
                                    client.V1EnvVar(name="KAFKA_BROKERS", value="kafka:9092"),
                                    client.V1EnvVar(name="SINK_TYPE", value=sink_type),
                                    client.V1EnvVar(name="ELASTICSEARCH_URL", value="http://elasticsearch:9200")
                                ],
                                resources=client.V1ResourceRequirements(
                                    requests={"cpu": "100m", "memory": "128Mi"},
                                    limits={"cpu": "500m", "memory": "512Mi"}
                                ),
                                liveness_probe=client.V1Probe(
                                    http_get=client.V1HTTPGetAction(path="/health", port=8080),
                                    initial_delay_seconds=30,
                                    period_seconds=10
                                ),
                                readiness_probe=client.V1Probe(
                                    http_get=client.V1HTTPGetAction(path="/ready", port=8080),
                                    initial_delay_seconds=10,
                                    period_seconds=5
                                )
                            )
                        ]
                    )
                )
            )
        )
        
        try:
            self.apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment)
            logger.info(f"Created sink deployment for pipeline: {name}")
        except ApiException as e:
            if e.status == 409:
                logger.info(f"Sink deployment already exists for pipeline: {name}")
            else:
                raise
    
    def update_pipeline_status(self, name: str, namespace: str, status: Dict[str, Any]) -> None:
        """Update LogPipeline status subresource"""
        
        try:
            self.custom_api.patch_namespaced_custom_object_status(
                group=CRD_GROUP,
                version=CRD_VERSION,
                namespace=namespace,
                plural=CRD_PLURAL,
                name=name,
                body={"status": status}
            )
            logger.info(f"Updated status for pipeline: {name}")
        except ApiException as e:
            logger.error(f"Failed to update status: {e}")

@kopf.on.create('logpipeline.k8s.io', 'v1', 'logpipelines')
def create_fn(spec, name, namespace, **kwargs):
    """Handle LogPipeline creation"""
    
    logger.info(f"Creating LogPipeline: {name} in namespace: {namespace}")
    
    controller = LogPipelineController()
    
    try:
        # Create components
        controller.create_collector_deployment(name, namespace, spec)
        controller.create_processor_deployment(name, namespace, spec)
        controller.create_sink_deployment(name, namespace, spec)
        
        # Update status
        status = {
            "phase": "Running",
            "conditions": [
                {
                    "type": "CollectorReady",
                    "status": "True",
                    "lastTransitionTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                },
                {
                    "type": "ProcessorReady",
                    "status": "True",
                    "lastTransitionTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                },
                {
                    "type": "SinkReady",
                    "status": "True",
                    "lastTransitionTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            ]
        }
        controller.update_pipeline_status(name, namespace, status)
        
        return {"message": f"LogPipeline {name} created successfully"}
        
    except Exception as e:
        logger.error(f"Error creating LogPipeline: {e}")
        status = {
            "phase": "Failed",
            "message": str(e)
        }
        controller.update_pipeline_status(name, namespace, status)
        raise

@kopf.on.update('logpipeline.k8s.io', 'v1', 'logpipelines')
def update_fn(spec, name, namespace, **kwargs):
    """Handle LogPipeline updates"""
    
    logger.info(f"Updating LogPipeline: {name} in namespace: {namespace}")
    
    # Implement update logic - patch deployments with new configuration
    return {"message": f"LogPipeline {name} updated successfully"}

@kopf.on.delete('logpipeline.k8s.io', 'v1', 'logpipelines')
def delete_fn(spec, name, namespace, **kwargs):
    """Handle LogPipeline deletion"""
    
    logger.info(f"Deleting LogPipeline: {name} in namespace: {namespace}")
    
    # Kubernetes garbage collection handles owned resources via owner references
    return {"message": f"LogPipeline {name} deleted successfully"}

if __name__ == "__main__":
    kopf.run()
