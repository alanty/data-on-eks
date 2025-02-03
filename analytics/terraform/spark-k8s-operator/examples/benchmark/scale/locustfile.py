from locust import User, task, events, between, constant_throughput
from k8s_client import SparkK8sClient
import uuid
import os


@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument("--jobs-per-min", type=int, default="1", help="Jobs creation rate.")
    parser.add_argument("--jobs-limit", type=int, default="5", help="Maximum number of jobs submitted")
    parser.add_argument("--spark-job-template", type=str, default="spark-app-template.yaml", help="SparkApplication file to be used to submit the spark jobs")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Load test is starting.")
    print("jobs_per_min = ", str(environment.parsed_options.jobs_per_min), "constant_throughput = ", str(environment.parsed_options.jobs_per_min / 60))
    print("jobs_limit = ", str(environment.parsed_options.jobs_limit))
    print("spark_job_template = ", environment.parsed_options.spark_job_template)
    # constant_throughput is calls per second,  dividing by 60s to get per second rate
    SparkOperatorUser.wait_time = constant_throughput((environment.parsed_options.jobs_per_min / 60))
    SparkOperatorUser.jobs_limit = environment.parsed_options.jobs_limit
    SparkOperatorUser.spark_template = environment.parsed_options.spark_job_template

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Load test is stopping. Check the logs for issues cleaning up.")

class SparkOperatorUser(User):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.k8s_client = SparkK8sClient()
        self.jobs_submitted = 0

    def on_stop(self):
        print("SparkOperatorUser is stopping. Deleting SparkApplications in: ", self.k8s_client.spark_app_template["metadata"]["namespace"])
        # delete any applications still running
        self.k8s_client.delete_namespace_spark_application(self.k8s_client.spark_app_template["metadata"]["namespace"])

    @task
    def submit_spark_job(self):
        if self.jobs_submitted < self.jobs_limit:
            app_name = f"load-test-{uuid.uuid4().hex[:8]}"
            print("Creating SparkApplication for: ", app_name)
            try:
                self.k8s_client.create_spark_application(app_name)
                self.k8s_client.get_spark_application_status(app_name)
                self.jobs_submitted += 1
            except Exception as e:
                import traceback
                self.environment.runner.log_exception(f"{type(e).__name__}: {str(e)}")
        else:
            print("Maximum Job submissions reached")
