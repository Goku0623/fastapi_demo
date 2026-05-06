from pydantic import BaseModel as PydanticBaseModel, field_serializer
from datetime import datetime, date


class BaseModel(PydanticBaseModel):
    @field_serializer("*", mode="wrap")
    def _serialize(self, value, handler, _info):
        result = handler(value)
        if isinstance(result, datetime):
            return result.isoformat() + "Z"
        if isinstance(result, date):
            return result.isoformat()
        return result
