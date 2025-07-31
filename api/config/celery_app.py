from celery import Celery

from .config import settings

REDIS_URL = settings.REDIS_URL

app_celery = Celery(
    "worker",
    broker=f"{REDIS_URL}/0",
    backend=f"{REDIS_URL}/1",
)

app_celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,  # Acknowledge apenas após conclusão
    worker_prefetch_multiplier=4,  # Prefetch mais tarefas por worker
    task_reject_on_worker_lost=True,  # Rejeitar tarefas se worker morrer
    # Pool de conexões otimizado
    broker_pool_limit=50,
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    # Configurações de timeout
    task_soft_time_limit=30,  # Soft timeout de 30s
    task_time_limit=60,  # Hard timeout de 60s
    # Otimizações de resultado
    result_expires=300,  # Resultados expiram em 5 minutos
    result_persistent=False,  # Não persistir resultados
    # Configurações de worker
    worker_disable_rate_limits=True,  # Desabilitar rate limits
    worker_max_tasks_per_child=1000,
)
