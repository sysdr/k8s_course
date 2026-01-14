from kubernetes import client, config
from datetime import datetime
import time
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageMonitor:
    def __init__(self):
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        
        self.v1 = client.CoreV1Api()
        self.storage_v1 = client.StorageV1Api()
    
    def check_pvcs(self, namespace="default"):
        """Monitor PVC status"""
        try:
            pvcs = self.v1.list_namespaced_persistent_volume_claim(namespace)
            
            for pvc in pvcs.items:
                status = pvc.status.phase
                name = pvc.metadata.name
                
                if status == "Pending":
                    logger.warning(f"PVC {name} in {namespace} is PENDING")
                    self.diagnose_pending_pvc(name, namespace)
                elif status == "Bound":
                    logger.info(f"PVC {name} in {namespace} is BOUND")
                else:
                    logger.error(f"PVC {name} in {namespace} has status: {status}")
        except Exception as e:
            logger.error(f"Error checking PVCs: {e}")
    
    def diagnose_pending_pvc(self, pvc_name, namespace):
        """Diagnose why a PVC is pending"""
        try:
            pvc = self.v1.read_namespaced_persistent_volume_claim(pvc_name, namespace)
            
            # Check StorageClass
            sc_name = pvc.spec.storage_class_name
            if sc_name:
                try:
                    sc = self.storage_v1.read_storage_class(sc_name)
                    logger.info(f"  StorageClass '{sc_name}' exists")
                except:
                    logger.error(f"  StorageClass '{sc_name}' NOT FOUND!")
            else:
                logger.warning(f"  No StorageClass specified (relying on default)")
            
            # Check events
            events = self.v1.list_namespaced_event(namespace)
            for event in events.items:
                if event.involved_object.name == pvc_name:
                    logger.info(f"  Event: {event.message}")
        except Exception as e:
            logger.error(f"Error diagnosing PVC: {e}")
    
    def check_storage_classes(self):
        """List all StorageClasses"""
        try:
            storage_classes = self.storage_v1.list_storage_class()
            logger.info(f"Available StorageClasses:")
            for sc in storage_classes.items:
                default = sc.metadata.annotations.get(
                    'storageclass.kubernetes.io/is-default-class', 'false'
                )
                logger.info(f"  - {sc.metadata.name} (default: {default})")
        except Exception as e:
            logger.error(f"Error listing StorageClasses: {e}")
    
    def monitor_loop(self, interval=30):
        """Continuous monitoring loop"""
        logger.info("Starting storage monitor...")
        
        while True:
            logger.info(f"\n--- Storage Check at {datetime.now()} ---")
            
            # Check all namespaces with our scenarios
            for ns in ["scenario-01", "scenario-02", "scenario-03", 
                      "scenario-04", "scenario-05", "scenario-06"]:
                try:
                    self.check_pvcs(ns)
                except:
                    pass  # Namespace might not exist yet
            
            self.check_storage_classes()
            
            time.sleep(interval)

if __name__ == "__main__":
    monitor = StorageMonitor()
    monitor.monitor_loop()
