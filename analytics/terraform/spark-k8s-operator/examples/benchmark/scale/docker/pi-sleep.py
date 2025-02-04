import sys
from random import random
from operator import add
from time import sleep

from pyspark.sql import SparkSession


if __name__ == "__main__":
    """
        Usage: pi [partitions] [sleep_seconds]
    """
    spark = SparkSession\
        .builder\
        .appName("PythonPi")\
        .getOrCreate()

    partitions = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    sleep_seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 0

    def f(_: int) -> float:
        print(f'sleeping for {sleep_seconds} seconds')
        sleep(sleep_seconds)
        x = random() * 2 - 1
        y = random() * 2 - 1
        return 1 if x ** 2 + y ** 2 <= 1 else 0

    count = spark.sparkContext.parallelize(range(1, partitions + 1), partitions).map(f).reduce(add)
    print("Pi is roughly %f" % (4.0 * count / partitions))

    spark.stop()

