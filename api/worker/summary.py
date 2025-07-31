import duckdb
from tinydb import Query

from ..config import conn_duckdb, default_tbl, fallback_tbl

pay = Query()


def get_summary(init, end):
    data = duckdb.read_json("payments.json")
    print(data)

    result = duckdb.sql("""SELECT * FROM 'payments.json'""")

    print(result)

    return {}


def purge_summary():
    default_tbl.truncate()
    fallback_tbl.truncate()

    return {"message": "Payment summary data purged", "status": "success"}
