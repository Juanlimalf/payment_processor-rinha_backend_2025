from asyncio import Queue

queue_payments = Queue(maxsize=60_000)
