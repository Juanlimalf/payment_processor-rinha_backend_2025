from typing import Optional, Dict, Any
from ..config.duck_db import get_payments_summary, purge_payments


def get_summary(init: Optional[str] = None, end: Optional[str] = None) -> Dict[str, Any]:
    return get_payments_summary(date_from=init, date_to=end)


def purge_summary() -> Dict[str, Any]:
    try:
        success = purge_payments()

        if success:
            return {"message": "Payment summary data purged successfully", "status": "success"}
        else:
            return {"message": "Failed to purge payment summary data", "status": "error"}

    except Exception as e:
        return {"message": f"Error purging data: {str(e)}", "status": "error"}
