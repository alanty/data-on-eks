import time
import uuid
import yaml

from locust import User, task, constant_throughput, events
from kubernetes import client, config
from datetime import datetime, timezone

from rich.console import Console

console = Console(log_path=False)

test_id = f"test-{str(uuid.uuid4())[:8]}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
test_start_time = time.perf_counter()



@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument("--jobs-per-min", type=int, default="8", help="Jobs creation rate.")
    parser.add_argument("--spark-job-template", type=str, default="spark-template.yaml", help="SparkApplication file to be used to submit the spark jobs")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    console.log(f"Test [green]{test_id}[/green] is started.")
    console.log(f"Job per minute is set to [green]{str(environment.parsed_options.jobs_per_min)}[/green] , constant_throughput({str(environment.parsed_options.jobs_per_min / 60)})")
    console.log(f"Spark job template is set to [green]{environment.parsed_options.spark_job_template}")
    # constant_throughput is calls per second,  dividing by 60s to get per second rate
    SparkScaleUser.wait_time = constant_throughput((environment.parsed_options.jobs_per_min / 60))
    SparkScaleUser.spark_template = environment.parsed_options.spark_job_template


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    elapsed_time = time.perf_counter() - test_start_time
    console.log(f"Test [green]{test_id}[/green] has stopped, took {elapsed_time} seconds. Jobs may still be running.")


# SparkScaleUser creates SparkApplication resources 
class SparkScaleUser(User):
    
    def on_start(self):
        console.log(f"Scale Test started on user id {self.user_id}")

    def on_stop(self):
        console.log(f"Scale Test stopped on user id {self.user_id}")
        # delete any applications still running
        kube_config = config.load_kube_config()
        kube_client_api = client.ApiClient(kube_config)
        kube_crd_client_api = client.CustomObjectsApi(kube_client_api)
        try:
            kapi_response = kube_crd_client_api.delete_collection_namespaced_custom_object(
                group="sparkoperator.k8s.io",
                version="v1beta2",
                label_selector="app=spark-sleep",
                namespace="spark-team-a",
                plural="sparkapplications",
            )
            console.log(f"Deleted SparkApplications {kapi_response}")
        # issue with K8s API?
        except client.rest.ApiException as e:
            console.log(f"{e}")

    @task
    def submit_spark_job(self):
        job_id = f"{self.user_id}{str(uuid.uuid4())[:8]}"

        console.log(f"Creating SparkApplication for [green]{job_id}[/green]")

        kube_config = config.load_kube_config()
        kube_client_api = client.ApiClient(kube_config)
        kube_crd_client_api = client.CustomObjectsApi(kube_client_api)


        with open(self.spark_template) as yaml_data:
            try:
                #load the file data to an object
                spark_crd_data = yaml.safe_load(yaml_data)
                # override the name of the job and namespace
                spark_crd_data["metadata"]["name"] = job_id
                spark_crd_data["metadata"]["namespace"] = "spark-team-a"
                console.log(f"Submitting SparkApplication with spec: \n{spark_crd_data}")

                try:
                    kapi_response = kube_crd_client_api.create_namespaced_custom_object(
                        group="sparkoperator.k8s.io",
                        version="v1beta2",
                        namespace="spark-team-a",
                        plural="sparkapplications",
                        body = spark_crd_data
                    )
                    self.running_jobs.append(job_id)
                    console.log(f"Retrieved Spark job details {kapi_response}")
                # issue with K8s API?
                except client.rest.ApiException as e:
                    console.log(f"{e}")
            # bad yaml file?
            except yaml.YAMLError as e:
                console.log(f"{e}")

        self.last_invoked_ts = int(time.time())
        self.total_jobs_submitted += 1
    
    def __init__(self, *args, **kwargs):
        super(SparkScaleUser, self).__init__(*args, **kwargs)
        self.user_id = f"{test_id}-{str(uuid.uuid4())[:8]}"
        self.total_jobs_submitted = 0
        self.last_invoked_ts = 0
        self.max_submit_lat = 0
        self.running_jobs = []


