import datetime
from typing import Optional

from mirth_client import MirthAPI
from mirth_client.models import ConnectorMessageData, ConnectorMessageModel
from pydantic import Field
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.errorsdb import Message
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.exceptions import ResourceNotFoundError
from ukrdc_fastapi.query.masterrecords import get_masterrecords_related_to_masterrecord
from ukrdc_fastapi.schemas.base import OrmModel


class MessageSourceSchema(OrmModel):
    """A message source file"""

    content: Optional[str] = Field(None, description="Message content")
    content_type: Optional[str] = Field(None, description="Message content type")


def get_messages(
    errorsdb: Session,
    statuses: Optional[list[str]] = None,
    channels: Optional[list[str]] = None,
    nis: Optional[list[str]] = None,
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
) -> Query:
    """Get a list of error messages from the errorsdb

    Args:
        errorsdb (Session): SQLAlchemy session
        statuses (Optional[list[str]], optional: Status code to filter by. Defaults to "ERROR".
        channels (Optional[list[str]], optional: Channel ID to filter by. Defaults to all channels.
        nis (Optional[list[str]], optional): List of pateint NIs to filer by. Defaults to None.
        facility (Optional[str], optional): Unit/facility code to filter by. Defaults to None.
        since (Optional[datetime.datetime], optional): Show records since datetime. Defaults to 365 days ago.
        until (Optional[datetime.datetime], optional): Show records until datetime. Defaults to None.

    Returns:
        Query: SQLAlchemy query
    """
    query = errorsdb.query(Message)

    # Default to showing last 365 days
    since_datetime: datetime.datetime = (
        since or datetime.datetime.utcnow() - datetime.timedelta(days=365)
    )
    query = query.filter(Message.received >= since_datetime)

    # Optionally filter out messages newer than `untildays`
    if until:
        query = query.filter(Message.received <= until)

    # Optionally filter by facility
    if facility:
        query = query.filter(Message.facility == facility)

    # Optionally filter by message status
    if statuses is not None:
        query = query.filter(Message.msg_status.in_(statuses))

    # Optionally filter by channels
    if channels is not None:
        query = query.filter(Message.channel_id.in_(channels))

    if nis:
        query = query.filter(Message.ni.in_(nis))

    return query


async def get_message_source(message: Message, mirth: MirthAPI) -> MessageSourceSchema:
    """Retreive a messages source file via the Mirth API

    Args:
        message (Message): Message to retrieve source for
        mirth (MirthAPI): Mirth API client

    Raises:
        ResourceNotFoundError: Message not found in Mirth

    Returns:
        MessageSourceSchema: Message source data
    """
    message_src = (
        await mirth.channel(message.channel_id).get_message(
            str(message.message_id), include_content=True
        )
        if message.channel_id and message.message_id
        else None
    )

    if not message_src:
        raise ResourceNotFoundError("Message not found in Mirth")

    connector_messages: list[ConnectorMessageModel] = list(
        message_src.connector_messages.values()
    )

    first_connector_message = connector_messages[0] if connector_messages else None

    message_data: Optional[ConnectorMessageData] = None

    if first_connector_message:
        # Prioritise encoded message over raw
        if first_connector_message.encoded:
            message_data = first_connector_message.encoded
        elif first_connector_message.raw:
            message_data = first_connector_message.raw

    # If no data is available, return a valid but empty MessageSourceSchema
    if not message_data:
        return MessageSourceSchema(content=None, content_type=None)

    return MessageSourceSchema(
        content=message_data.content, content_type=message_data.data_type
    )


def get_messages_related_to_masterrecord(
    record: MasterRecord,
    errorsdb: Session,
    jtrace: Session,
    statuses: Optional[list[str]] = None,
    channels: Optional[list[str]] = None,
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
) -> Query:
    """Get a list of error messages from the errorsdb

    Args:
        errorsdb (Session): SQLAlchemy session
        jtrace (Session): JTRACE SQLAlchemy session
        record_id (int): MasterRecord ID
        statuses (str, optional): Status codes to filter by. Defaults to all.
        channels (Optional[list[str]], optional: Channel ID to filter by. Defaults to all channels.
        facility (Optional[str], optional): Unit/facility code to filter by. Defaults to None.
        since (Optional[datetime.datetime], optional): Show records since datetime. Defaults to 365 days ago.
        until (Optional[datetime.datetime], optional): Show records until datetime. Defaults to None.

    Returns:
        Query: SQLAlchemy query
    """
    related_master_records = get_masterrecords_related_to_masterrecord(record, jtrace)

    related_national_ids: list[str] = [
        record.nationalid for record in related_master_records.all()
    ]

    return get_messages(
        errorsdb,
        statuses=statuses,
        channels=channels,
        nis=related_national_ids,
        facility=facility,
        since=since,
        until=until,
    )


def get_messages_related_to_patientrecord(
    record: PatientRecord,
    errorsdb: Session,
    statuses: Optional[list[str]] = None,
    channels: Optional[list[str]] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
) -> Query:
    national_ids: list[str] = [
        number.patientid
        for number in record.patient.numbers
        if number.numbertype == "NI"
    ]

    return get_messages(
        errorsdb,
        statuses=statuses,
        channels=channels,
        nis=national_ids,
        facility=record.sendingfacility,
        since=since,
        until=until,
    )
