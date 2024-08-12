python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt




locust
locust -u 15 -t 60m --wait-time 12



locust -u 1 -t 30m --jobs-per-min 1


