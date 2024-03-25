import os
from pathlib import Path

GLOBUS_INDEX_NAME = "schema-org-index"
OLD_GLOBUS_INDEX_NAME = "schema-org-index-v1"

RMQ_NAME = "geoedf-all"
RMQ_HOST = 'rabbitmq-service'
RMQ_HOST_IP = '172.17.0.3'
# RMQ_HOST = 'some-rabbit'
RMQ_USER = 'guest'
RMQ_PASS = 'guest'

BASE_DIR = Path(__file__).resolve().parent.parent
FILES_ROOT = os.path.join(BASE_DIR, 'data', 'files')