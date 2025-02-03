from kubernetes import client, config
import yaml
import os

class SparkK8sClient:
    def __init__(self):
        # Load kube config
        try:
            config.load_kube_config()
            template_path = os.path.join(os.path.dirname(__file__), 'spark-app-template.yaml')
            with open(template_path, 'r') as f:
                template = f.read()
                self.spark_app_template = yaml.safe_load(template)
        except:
            config.load_incluster_config()
        self.kube_config = config.load_kube_config()
        self.kube_client_api = client.ApiClient(self.kube_config)
        self.custom_objects_api = client.CustomObjectsApi(self.kube_client_api)
        
    def create_spark_application(self, name):
        """Create a basic Spark application"""
        spark_app = self.spark_app_template.copy()
        spark_app['metadata']['name'] = name
        spark_app['spec']['sparkConf']['spark.kubernetes.executor.podNamePrefix'] = name
        return self.custom_objects_api.create_namespaced_custom_object(
            group="sparkoperator.k8s.io",
            version="v1beta2",
            namespace=self.spark_app_template["metadata"]["namespace"],
            plural="sparkapplications",
            body=spark_app
        )
        
    def delete_spark_application(self, name):
        """Delete a Spark application"""
        return self.custom_objects_api.delete_namespaced_custom_object(
            group="sparkoperator.k8s.io",
            version="v1beta2",
            namespace=self.spark_app_template["metadata"]["namespace"],
            plural="sparkapplications",
            name=name
        )
        
    def delete_namespace_spark_application(self, namespace):
        # delete ALL matching objects in the 
        # TODO: this is a bit overkill, we should scope this to only the jobs submitted by this user
        return self.custom_objects_api.delete_collection_namespaced_custom_object(
                group="sparkoperator.k8s.io",
                version="v1beta2",
                namespace=namespace,
                plural="sparkapplications",
            )

    def get_spark_application_status(self, name):
        """Get the status of a Spark application"""
        return self.custom_objects_api.get_namespaced_custom_object_status(
            group="sparkoperator.k8s.io",
            version="v1beta2",
            namespace=self.spark_app_template["metadata"]["namespace"],
            plural="sparkapplications",
            name=name
        )
