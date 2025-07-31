import duckdb
from typing import Dict, Any, Optional
from datetime import datetime

# Caminho para o arquivo do banco de dados
DB_PATH = "payments.duckdb"

# Criar conexão com arquivo persistente
conn_duckdb = duckdb.connect(DB_PATH)


def init_database():
    try:
        conn_duckdb.execute("""
            CREATE TABLE IF NOT EXISTS default_payments (
                id VARCHAR PRIMARY KEY,
                amount DECIMAL(15,2),
                requested_at TIMESTAMP
            )
        """)

        conn_duckdb.execute("""
            CREATE TABLE IF NOT EXISTS fallback_payments (
                id VARCHAR PRIMARY KEY,
                amount DECIMAL(15,2),
                requested_at TIMESTAMP
            )
        """)

    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {e}")


def insert_payment(table_name: str, payment_data: Dict[str, Any]) -> bool:
    try:
        if table_name not in ["default_payments", "fallback_payments"]:
            return False

        conn_duckdb.execute(
            f"""
            INSERT INTO {table_name} (id, amount, requested_at)
            VALUES (?, ?, ?)
        """,
            [payment_data.get("id"), payment_data.get("amount"), payment_data.get("requested_at")],
        )

        return True

    except Exception as e:
        print(f"Erro ao inserir pagamento: {e}")
        return False


def get_payments_summary(date_from: Optional[str] = None, date_to: Optional[str] = None) -> Dict[str, Any]:
    try:
        result = {"default": {"totalRequests": 0, "totalAmount": 0.0}, "fallback": {"totalRequests": 0, "totalAmount": 0.0}}

        default_query = "SELECT COUNT(*) as total_requests, COALESCE(SUM(amount), 0) as total_amount FROM default_payments"
        fallback_query = "SELECT COUNT(*) as total_requests, COALESCE(SUM(amount), 0) as total_amount FROM fallback_payments"

        params = []

        if date_from or date_to:
            where_clause = " WHERE"
            conditions = []

            if date_from:
                conditions.append(" requested_at >= ?")
                params.append(date_from)

            if date_to:
                conditions.append(" requested_at <= ?")
                params.append(date_to)

            where_clause += " AND".join(conditions)
            default_query += where_clause
            fallback_query += where_clause

        default_result = conn_duckdb.execute(default_query, params).fetchone()
        fallback_result = conn_duckdb.execute(fallback_query, params).fetchone()

        if default_result:
            result["default"]["totalRequests"] = default_result[0]
            result["default"]["totalAmount"] = float(default_result[1])

        if fallback_result:
            result["fallback"]["totalRequests"] = fallback_result[0]
            result["fallback"]["totalAmount"] = float(fallback_result[1])

        return result

    except Exception as e:
        print(f"Erro ao consultar pagamentos: {e}")
        return {"default": {"totalRequests": 0, "totalAmount": 0.0}, "fallback": {"totalRequests": 0, "totalAmount": 0.0}}


def purge_payments() -> bool:
    try:
        conn_duckdb.execute("DELETE FROM default_payments")
        conn_duckdb.execute("DELETE FROM fallback_payments")
        return True
    except Exception as e:
        print(f"Erro ao purgar pagamentos: {e}")
        return False
