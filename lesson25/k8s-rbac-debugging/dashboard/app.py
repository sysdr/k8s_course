#!/usr/bin/env python3
"""
Kubernetes RBAC Debugging Dashboard
Real-time monitoring and visualization of RBAC operations
"""
import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import threading
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Global cache for metrics
metrics_cache = {
    'cluster': {},
    'rbac': {},
    'deployments': {},
    'jobs': {},
    'pods': {},
    'permissions': {},
    'last_update': None
}

# Cache lock for thread safety
cache_lock = threading.Lock()


class KubernetesMetrics:
    """Collect metrics from Kubernetes cluster"""
    
    def __init__(self):
        try:
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes configuration")
        except config.ConfigException:
            try:
                config.load_kube_config()
                logger.info("Loaded kubeconfig configuration")
            except Exception as e:
                logger.error(f"Failed to load Kubernetes config: {e}")
        
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.rbac_v1 = client.RbacAuthorizationV1Api()
        self.batch_v1 = client.BatchV1Api()
        self.auth_v1 = client.AuthorizationV1Api()
    
    def get_cluster_info(self):
        """Get cluster nodes and namespaces"""
        try:
            nodes = self.core_v1.list_node()
            namespaces = self.core_v1.list_namespace()
            
            node_info = []
            for node in nodes.items:
                node_info.append({
                    'name': node.metadata.name,
                    'status': next((s.type for s in node.status.conditions if s.status == 'True' and s.type in ['Ready', 'NotReady']), 'Unknown'),
                    'role': 'control-plane' if 'node-role.kubernetes.io/control-plane' in node.metadata.labels else 'worker',
                    'cpu': node.status.capacity.get('cpu', 'N/A'),
                    'memory': node.status.capacity.get('memory', 'N/A')
                })
            
            namespace_list = [ns.metadata.name for ns in namespaces.items]
            
            return {
                'nodes': node_info,
                'namespaces': namespace_list,
                'node_count': len(node_info),
                'namespace_count': len(namespace_list)
            }
        except Exception as e:
            logger.error(f"Error getting cluster info: {e}")
            return {'error': str(e)}
    
    def get_rbac_status(self):
        """Get RBAC configuration status"""
        try:
            sa_list = []
            role_list = []
            rolebinding_list = []
            
            # Get ServiceAccounts
            for ns in ['ci-cd', 'production', 'staging']:
                try:
                    sas = self.core_v1.list_namespaced_service_account(namespace=ns)
                    for sa in sas.items:
                        sa_list.append({
                            'name': sa.metadata.name,
                            'namespace': sa.metadata.namespace,
                            'created': sa.metadata.creation_timestamp.isoformat() if sa.metadata.creation_timestamp else None
                        })
                except ApiException:
                    pass
            
            # Get Roles
            for ns in ['ci-cd', 'production', 'staging']:
                try:
                    roles = self.rbac_v1.list_namespaced_role(namespace=ns)
                    for role in roles.items:
                        rules_summary = []
                        for rule in role.rules:
                            resources = ', '.join(rule.resources) if rule.resources else '*'
                            verbs = ', '.join(rule.verbs) if rule.verbs else '*'
                            rules_summary.append(f"{resources}: {verbs}")
                        
                        role_list.append({
                            'name': role.metadata.name,
                            'namespace': role.metadata.namespace,
                            'rules': rules_summary,
                            'rules_count': len(role.rules)
                        })
                except ApiException:
                    pass
            
            # Get RoleBindings
            for ns in ['ci-cd', 'production', 'staging']:
                try:
                    bindings = self.rbac_v1.list_namespaced_role_binding(namespace=ns)
                    for binding in bindings.items:
                        subjects = []
                        for subject in binding.subjects:
                            subjects.append(f"{subject.kind}/{subject.name}@{subject.namespace if hasattr(subject, 'namespace') and subject.namespace else 'cluster'}")
                        
                        rolebinding_list.append({
                            'name': binding.metadata.name,
                            'namespace': binding.metadata.namespace,
                            'role_ref': f"{binding.role_ref.kind}/{binding.role_ref.name}",
                            'subjects': subjects
                        })
                except ApiException:
                    pass
            
            # Check for broken vs fixed configuration
            broken_config = False
            fixed_config = False
            
            # Check if role exists in ci-cd (broken)
            try:
                self.rbac_v1.read_namespaced_role(name='deployer-role', namespace='ci-cd')
                broken_config = True
            except ApiException:
                pass
            
            # Check if role exists in production (fixed)
            try:
                self.rbac_v1.read_namespaced_role(name='deployer-role', namespace='production')
                fixed_config = True
            except ApiException:
                pass
            
            return {
                'serviceaccounts': sa_list,
                'roles': role_list,
                'rolebindings': rolebinding_list,
                'broken_config': broken_config,
                'fixed_config': fixed_config,
                'config_status': 'broken' if broken_config and not fixed_config else ('fixed' if fixed_config else 'none')
            }
        except Exception as e:
            logger.error(f"Error getting RBAC status: {e}")
            return {'error': str(e)}
    
    def get_deployment_status(self):
        """Get deployment status in production namespace"""
        try:
            deployments = []
            try:
                deps = self.apps_v1.list_namespaced_deployment(namespace='production')
                for dep in deps.items:
                    deployments.append({
                        'name': dep.metadata.name,
                        'namespace': dep.metadata.namespace,
                        'replicas': dep.spec.replicas,
                        'ready': dep.status.ready_replicas or 0,
                        'available': dep.status.available_replicas or 0,
                        'status': 'Ready' if (dep.status.ready_replicas or 0) == dep.spec.replicas else 'Not Ready'
                    })
            except ApiException:
                pass
            
            # Get services
            services = []
            try:
                svcs = self.core_v1.list_namespaced_service(namespace='production')
                for svc in svcs.items:
                    services.append({
                        'name': svc.metadata.name,
                        'namespace': svc.metadata.namespace,
                        'type': svc.spec.type,
                        'cluster_ip': svc.spec.cluster_ip,
                        'ports': [f"{p.port}->{p.target_port}" for p in svc.spec.ports]
                    })
            except ApiException:
                pass
            
            return {
                'deployments': deployments,
                'services': services
            }
        except Exception as e:
            logger.error(f"Error getting deployment status: {e}")
            return {'error': str(e)}
    
    def get_job_status(self):
        """Get deployment job status"""
        try:
            jobs = []
            try:
                job_list = self.batch_v1.list_namespaced_job(namespace='ci-cd')
                for job in job_list.items:
                    status = 'Unknown'
                    if job.status.conditions:
                        for condition in job.status.conditions:
                            if condition.type == 'Complete' and condition.status == 'True':
                                status = 'Complete'
                            elif condition.type == 'Failed' and condition.status == 'True':
                                status = 'Failed'
                    
                    jobs.append({
                        'name': job.metadata.name,
                        'namespace': job.metadata.namespace,
                        'status': status,
                        'start_time': job.status.start_time.isoformat() if job.status.start_time else None,
                        'completion_time': job.status.completion_time.isoformat() if job.status.completion_time else None,
                        'succeeded': job.status.succeeded or 0,
                        'failed': job.status.failed or 0,
                        'active': job.status.active or 0
                    })
            except ApiException:
                pass
            
            return {'jobs': jobs}
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return {'error': str(e)}
    
    def get_pod_status(self):
        """Get pod status across namespaces"""
        try:
            pods = []
            for ns in ['ci-cd', 'production', 'staging']:
                try:
                    pod_list = self.core_v1.list_namespaced_pod(namespace=ns)
                    for pod in pod_list.items:
                        status = pod.status.phase
                        if pod.status.container_statuses:
                            container_status = pod.status.container_statuses[0]
                            if container_status.state.waiting:
                                status = f"Waiting: {container_status.state.waiting.reason}"
                            elif container_status.state.terminated:
                                status = f"Terminated: {container_status.state.terminated.reason}"
                        
                        pods.append({
                            'name': pod.metadata.name,
                            'namespace': pod.metadata.namespace,
                            'status': status,
                            'node': pod.spec.node_name,
                            'created': pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
                            'restarts': sum(c.restart_count for c in pod.status.container_statuses) if pod.status.container_statuses else 0
                        })
                except ApiException:
                    pass
            
            return {
                'pods': pods,
                'message': 'No application pods found. Deploy resources with: ./scripts/deploy.sh [broken|fixed]' if not pods else None
            }
        except Exception as e:
            logger.error(f"Error getting pod status: {e}")
            return {'error': str(e)}
    
    def check_permissions(self):
        """Check RBAC permissions for deployer ServiceAccount"""
        try:
            sa_name = "deployer"
            sa_namespace = "ci-cd"
            target_namespace = "production"
            sa_full_name = f"system:serviceaccount:{sa_namespace}:{sa_name}"
            
            permissions = {
                'deployments': {
                    'create': False,
                    'get': False,
                    'list': False,
                    'update': False
                },
                'services': {
                    'create': False,
                    'get': False,
                    'list': False
                },
                'configmaps': {
                    'create': False,
                    'get': False,
                    'list': False
                },
                'secrets': {
                    'get': False,
                    'list': False
                }
            }
            
            # Try to use SubjectAccessReview (requires cluster-admin permissions)
            # If that fails, fall back to checking Role definitions
            use_sar = True
            try:
                # Test if we can use SubjectAccessReview
                test_sar = client.V1SubjectAccessReview(
                    spec=client.V1SubjectAccessReviewSpec(
                        user=sa_full_name,
                        resource_attributes=client.V1ResourceAttributes(
                            namespace=target_namespace,
                            verb='get',
                            resource='pods'
                        )
                    )
                )
                self.auth_v1.create_subject_access_review(test_sar)
            except ApiException as e:
                if e.status == 403:
                    use_sar = False
                    logger.info("Cannot use SubjectAccessReview, falling back to Role inspection")
                else:
                    raise
            
            if use_sar:
                # Use SubjectAccessReview to check actual permissions
                for resource, verbs in permissions.items():
                    for verb in verbs.keys():
                        try:
                            sar = client.V1SubjectAccessReview(
                                spec=client.V1SubjectAccessReviewSpec(
                                    user=sa_full_name,
                                    resource_attributes=client.V1ResourceAttributes(
                                        namespace=target_namespace,
                                        verb=verb,
                                        group='apps' if resource == 'deployments' else '',
                                        resource=resource
                                    )
                                )
                            )
                            result = self.auth_v1.create_subject_access_review(sar)
                            permissions[resource][verb] = result.status.allowed
                        except Exception as e:
                            logger.error(f"Error checking permission {verb} {resource}: {e}")
            else:
                # Fall back to inspecting Role definitions
                try:
                    role = self.rbac_v1.read_namespaced_role(name='deployer-role', namespace=target_namespace)
                    for rule in role.rules:
                        api_group = rule.api_groups[0] if rule.api_groups else ''
                        resources = rule.resources if rule.resources else []
                        rule_verbs = rule.verbs if rule.verbs else []
                        
                        for resource_name, verb_dict in permissions.items():
                            if resource_name in resources or '*' in resources:
                                if api_group == 'apps' or (resource_name != 'deployments' and api_group == ''):
                                    for verb in verb_dict.keys():
                                        if verb in rule_verbs or '*' in rule_verbs:
                                            permissions[resource_name][verb] = True
                except ApiException:
                    # Role doesn't exist or can't be read
                    pass
            
            return {
                'serviceaccount': sa_full_name,
                'namespace': target_namespace,
                'permissions': permissions,
                'method': 'SubjectAccessReview' if use_sar else 'Role Inspection',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error checking permissions: {e}")
            return {'error': str(e)}
    
    def get_job_logs(self, job_name='deployment-job', namespace='ci-cd', lines=50):
        """Get logs from deployment job pod"""
        try:
            # First check if job exists
            try:
                job = self.batch_v1.read_namespaced_job(name=job_name, namespace=namespace)
            except ApiException as e:
                if e.status == 404:
                    return {
                        'logs': [],
                        'message': f'No deployment job found. Deploy resources with: ./scripts/deploy.sh broken',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                raise
            
            # Find pod for the job
            pods = self.core_v1.list_namespaced_pod(namespace=namespace, 
                                                    label_selector='app=ci-cd-deployer')
            
            # Also try to find pods by job name
            if not pods.items:
                all_pods = self.core_v1.list_namespaced_pod(namespace=namespace)
                pods.items = [p for p in all_pods.items if job_name in p.metadata.name]
            
            if not pods.items:
                return {
                    'logs': [],
                    'message': f'Job "{job_name}" exists but no pods found yet. The job may be pending or failed.',
                    'job_status': 'No pods',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Get the most recent pod
            pod = sorted(pods.items, key=lambda p: p.metadata.creation_timestamp, reverse=True)[0]
            
            # Get logs
            try:
                logs = self.core_v1.read_namespaced_pod_log(
                    name=pod.metadata.name,
                    namespace=namespace,
                    tail_lines=lines
                )
                
                log_lines = logs.split('\n') if logs else []
                return {
                    'pod_name': pod.metadata.name,
                    'logs': log_lines[-lines:] if len(log_lines) > lines else log_lines,
                    'timestamp': datetime.utcnow().isoformat()
                }
            except ApiException as e:
                if e.status == 400:
                    return {
                        'logs': [],
                        'pod_name': pod.metadata.name,
                        'message': f'Pod {pod.metadata.name} exists but logs are not available yet (pod may be initializing)',
                        'pod_status': pod.status.phase,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                raise
        except Exception as e:
            logger.error(f"Error getting job logs: {e}")
            return {'error': str(e), 'logs': []}


# Initialize metrics collector
metrics_collector = KubernetesMetrics()


def update_metrics():
    """Update metrics cache in background"""
    global metrics_cache
    
    while True:
        try:
            logger.info("Updating metrics cache...")
            
            new_cache = {
                'cluster': metrics_collector.get_cluster_info(),
                'rbac': metrics_collector.get_rbac_status(),
                'deployments': metrics_collector.get_deployment_status(),
                'jobs': metrics_collector.get_job_status(),
                'pods': metrics_collector.get_pod_status(),
                'permissions': metrics_collector.check_permissions(),
                'last_update': datetime.utcnow().isoformat()
            }
            
            with cache_lock:
                metrics_cache = new_cache
            
            logger.info("Metrics cache updated")
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
        
        time.sleep(5)  # Update every 5 seconds


# Start background thread for metrics updates
metrics_thread = threading.Thread(target=update_metrics, daemon=True)
metrics_thread.start()


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/metrics')
def get_metrics():
    """Get all metrics"""
    with cache_lock:
        return jsonify(metrics_cache)


@app.route('/api/cluster')
def get_cluster():
    """Get cluster metrics"""
    with cache_lock:
        return jsonify(metrics_cache.get('cluster', {}))


@app.route('/api/rbac')
def get_rbac():
    """Get RBAC metrics"""
    with cache_lock:
        return jsonify(metrics_cache.get('rbac', {}))


@app.route('/api/deployments')
def get_deployments():
    """Get deployment metrics"""
    with cache_lock:
        return jsonify(metrics_cache.get('deployments', {}))


@app.route('/api/jobs')
def get_jobs():
    """Get job metrics"""
    with cache_lock:
        return jsonify(metrics_cache.get('jobs', {}))


@app.route('/api/pods')
def get_pods():
    """Get pod metrics"""
    with cache_lock:
        return jsonify(metrics_cache.get('pods', {}))


@app.route('/api/permissions')
def get_permissions():
    """Get permission check results"""
    with cache_lock:
        return jsonify(metrics_cache.get('permissions', {}))


@app.route('/api/logs')
def get_logs():
    """Get job logs"""
    logs = metrics_collector.get_job_logs()
    return jsonify(logs)


@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })


if __name__ == '__main__':
    # Initial metrics collection
    logger.info("Starting dashboard server...")
    logger.info("Collecting initial metrics...")
    
    port = int(os.getenv('PORT', 8080))
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"Dashboard available at http://{host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)

