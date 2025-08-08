import asyncio
import json
import time
from datetime import datetime
from typing import Optional

import redis

from schemas.schema import Payment, PaymentsTotals, Summary

queue_payments = asyncio.Queue(maxsize=5_000)

redis_client = redis.Redis(host="redis", port=6379, db=0)


class PaymentService:
    def _iso_to_timestamp(self, iso_str: str) -> int:
        dt = datetime.strptime(iso_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")

        return int(time.mktime(dt.timetuple()))

    async def insert_payment(self, data: Payment):
        queue_payments.put_nowait(data)

    async def get_summary(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Summary:
        if from_date and to_date:
            from_ts = self._iso_to_timestamp(from_date)
            to_ts = self._iso_to_timestamp(to_date)

            payments_default = redis_client.zrangebyscore("payment_processed_default", from_ts, to_ts)
            payments_fallback = redis_client.zrangebyscore("payment_processed_fallback", from_ts, to_ts)
        else:
            payments_default = redis_client.zrange("payment_processed_default", 0, -1)
            payments_fallback = redis_client.zrange("payment_processed_fallback", 0, -1)

        return Summary(
            default=PaymentsTotals(
                totalRequests=len(payments_default),
                totalAmount=round(sum(json.loads(item.decode())["amount"] for item in payments_default), 2),
            ),
            fallback=PaymentsTotals(
                totalRequests=len(payments_fallback),
                totalAmount=round(sum(json.loads(item.decode())["amount"] for item in payments_fallback), 2),
            ),
        )

    async def purge_database(self) -> None:
        redis_client.flushdb()


class PublishService:
    async def start_processing(self):
        while True:
            try:
                data = await queue_payments.get()

                if data:
                    await self.insert_payment(data)

                queue_payments.task_done()
            except Exception as e:
                print(e)

    async def insert_payment(self, data: Payment):
        try:
            redis_client.lpush("payment_queue", data.model_dump_json())
        except Exception as e:
            raise e
