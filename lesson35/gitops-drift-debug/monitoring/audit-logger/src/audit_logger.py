"""
Audit Logger - Monitors Kubernetes API for manual changes
Detects drift by watching for kubectl operations
"""
import os
import json
import logging
from kubernetes import client, config, watch
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Watch for deployment changes and log them"""
    logger.info("Starting audit logger...")
    
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()
    
    v1 = client.AppsV1Api()
    w = watch.Watch()
    
    logger.info("Watching for deployment changes...")
    
    for event in w.stream(v1.list_deployment_for_all_namespaces):
        deployment = event['object']
        event_type = event['type']
        
        if event_type in ['MODIFIED', 'DELETED']:
            audit_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': event_type,
                'resource_type': 'Deployment',
                'resource_name': deployment.metadata.name,
                'namespace': deployment.metadata.namespace,
                'annotations': deployment.metadata.annotations or {},
                'labels': deployment.metadata.labels or {}
            }
            
            logger.info(f"Audit Event: {json.dumps(audit_entry)}")
            
            # In production, send to log aggregation service
            # For now, just log to stdout

if __name__ == "__main__":
    main()
