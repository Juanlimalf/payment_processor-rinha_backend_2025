from tinydb import TinyDB

db = TinyDB("payments.json")

default_tbl = db.table("default")

fallback_tbl = db.table("fallback")
