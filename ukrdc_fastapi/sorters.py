from ukrdc_sqla.errorsdb import Message

from ukrdc_fastapi.utils.sort import make_sqla_sorter

ERROR_SORTER = make_sqla_sorter(
    [Message.id, Message.received, Message.ni], default_sort_by=Message.received
)
