import datetime
import json
from decimal import Decimal

from fastapi.encoders import jsonable_encoder


class JsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return {"val": str(o), "_spec_type": "datetime"}
        if isinstance(o, datetime.date):
            return {"val": str(o), "_spec_type": "date"}
        if isinstance(o, Decimal):
            return {"val": str(o), "_spec_type": "decimal"}
        return jsonable_encoder(o)
