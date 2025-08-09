import asyncio
import threading

from services.worker import worker

NUM_WORKERS = 10


def main(thread_id: int):
    try:
        print(f"Iniciando worker {thread_id}")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(worker())
    except Exception as e:
        print(e)
    finally:
        print(f"worker {thread_id} finalizado")


if __name__ == "__main__":
    threads = []
    for i in range(NUM_WORKERS):
        thread = threading.Thread(target=main, args=(i,), name=f"WorkerThread-{i}")
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
