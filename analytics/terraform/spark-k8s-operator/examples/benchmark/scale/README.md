# spark-operator-load-test

## Getting started
Locust creates User processes that execute Tasks based on the configuration in the `locustfile.py` file. This allows us to create SparkApplication CRDs at a consistent rate and scale.  

### Install locust
```
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run locust
#### Web UI
Running locust without parameters will launch a webui at [http://0.0.0.0:8089](http://0.0.0.0:8089):  
```bash
locust
```
From there you can configure the parameters in the web form and start the test.

#### Without GUI/Headless
Providing the `--headless` option disables the webui and instead runs automatically with the default parameters:  
```bash
locust --headless --only-summary -u 1 -r 1
```
This starts a single User over 1s.

#### Parameters
**Spark test options:**
```bash
  --jobs-per-min  Jobs creation rate per User (default: 1)
  --jobs-limit  Maximum number of jobs submitted per User (default: 5). If a value <=0 is supplied, the processes will submit jobs in sequence as fast as possible
  --spark-job-template  path to SparkApplication file to be used to submit the spark jobs (default: spark-app-template.yaml)
```
**Common options:**
```bash
  -u, --users <int>     Peak number of concurrent Locust users. Primarily used together with --headless or --autostart. Can be changed during a test by keyboard inputs w, W (spawn 1, 10 users) and s, S (stop 1, 10 users)
  -r, --spawn-rate <float>
                        Rate to spawn users at (users per second). Primarily used together with --headless or --autostart
  -t, --run-time <time string>
                        Stop after the specified amount of time, e.g. (300s, 20m, 3h, 1h30m, etc.). Only used together with --headless or --autostart. Defaults to run forever.
  --only-summary        Disable periodic printing of request stats during --headless run
```

When determining the load to apply, the number of users and job submission rate are multiplicative. i.e.: 
```
Num Users * Jobs per Min = total submission rate
```
and 
```
Num Users * Jobs Limit = total number of jobs
```

**Examples**
To submit 50 Jobs as fast as possible with a single process:
```bash
locust --headless --only-summary -u 1 -r 1 --jobs-per-min -1 --jobs-limit 50
```
You can increase the rate at which calls are made by increasing the number of users spawned (concurrency). 
```bash
locust --headless --only-summary -u 1 -r 1 --jobs-per-min -1 --jobs-limit 50
```

Submit 30 jobs a minute, until 100 jobs are submitted with both of these commands below
```bash
locust --headless --only-summary -u 1 -r 1 --jobs-per-min 30 --jobs-limit 100
```
or 
```bash
locust --headless --only-summary -u 2 -r 1 --jobs-per-min 15 --jobs-limit 50
```

To run the same test 3 times in a row with sleep in between
```bash
JOBS_MIN=-1
JOBS_LIMIT=10
TIMEOUT="7m"
USERS=1
RATE=1

sleep 240
locust --headless --only-summary -u $USERS -r $RATE -t $TIMEOUT --jobs-per-min $JOBS_MIN --jobs-limit $JOBS_LIMIT 2>&1 | tee -a load-test-$(date -u +"%Y-%m-%dT%H:%M:%SZ").log 

echo "\n~~~~~~~~~~~~~~~~~~~~~~~Sleeping for 3min to separate tests~~~~~~~~~~~~~~~~~~~~~~\n"
sleep 240

locust --headless --only-summary -u $USERS -r $RATE -t $TIMEOUT --jobs-per-min $JOBS_MIN --jobs-limit $JOBS_LIMIT 2>&1 | tee -a load-test-$(date -u +"%Y-%m-%dT%H:%M:%SZ").log

echo "\n~~~~~~~~~~~~~~~~~~~~~~~Sleeping for 3min to separate tests~~~~~~~~~~~~~~~~~~~~~~\\n"
sleep 240

locust --headless --only-summary -u $USERS -r $RATE -t $TIMEOUT --jobs-per-min $JOBS_MIN --jobs-limit $JOBS_LIMIT 2>&1 | tee -a load-test-$(date -u +"%Y-%m-%dT%H:%M:%SZ").log
```

to delete all of the nodes in the Spark ASG and start fresh you can run: 
```bash
for ID in $(aws autoscaling describe-auto-scaling-instances --output text \
--query "AutoScalingInstances[?AutoScalingGroupName=='eks-spark_benchmark_ebs-20250203215338743800000001-aeca66e7-0385-19a7-a895-d021a5f67933'].InstanceId");
do
aws ec2 terminate-instances --instance-ids $ID
done
```

```


### Docker image for SparkApplications

`public.ecr.aws/m8u6z8z4/manabu-test:pi-sleep`

See the [pi-sleep.py](./pi-sleep.py) for what it does. It adds the sleep duration parameter to the example pi script from upstream.
`Note: this image is currently only supported on amd64 based instances.`


You can then specify sleep duration like below.

```yaml
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
spec:
  mainApplicationFile: local:///opt/spark/examples/src/main/python/pi-sleep.py
  arguments: ["1", "1800"]
```

