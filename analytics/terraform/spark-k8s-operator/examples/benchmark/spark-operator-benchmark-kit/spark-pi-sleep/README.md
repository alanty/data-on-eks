## Test Spark Application

Source code for the Spark Application used for testing is available in this directory.

You can build your Docker image by following steps below.

### Compile

From the [spark-pi-sleep](./spark-pi-sleep/) directory:

```bash
./gradlew build
```

### Build Docker image

From the [docker](./docker/) directory:

```bash
cp ../spark-pi-sleep/build/libs/spark-pi-sleep-1.0.jar spark-pi-sleep.jar
docker build .
```

### Using the Docker image

You can then specify sleep duration like below in the Spark Application:

```yaml
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
spec:
  mainApplicationFile: local:///opt/spark/examples/src/main/python/pi-sleep.py
  arguments: ["1", "1800"] # sleep for 1800 seconds
```