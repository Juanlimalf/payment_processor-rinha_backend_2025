import asyncio
import threading

from services.worker import worker


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
    thread1 = threading.Thread(target=main, args=(1,), name="WorkerThread-1")
    thread2 = threading.Thread(target=main, args=(2,), name="WorkerThread-2")
    thread3 = threading.Thread(target=main, args=(3,), name="WorkerThread-3")

    thread1.start()
    thread2.start()
    thread3.start()

    thread1.join()
    thread2.join()
    thread3.join()
