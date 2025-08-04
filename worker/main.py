import redis
from rq import SimpleWorker

from config import settings

redis_conn = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
worker = SimpleWorker(["worker"], connection=redis_conn, log_job_description=False)

if __name__ == "__main__":
    worker.work()
