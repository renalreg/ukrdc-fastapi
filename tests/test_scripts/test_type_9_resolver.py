# tests/test_process_workitem.py
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, call

import scripts.type_9_resolver.process as script

def test_process_workitem_submits_corrections_and_reprocesses(monkeypatch):
    workitem_id = 123
    incoming_id = "OLD123"
    current_id = "NEW456"

    workitem = SimpleNamespace(
        id=workitem_id,
        type=9,
        incoming=SimpleNamespace(
            master_records=[SimpleNamespace(nationalid="1111111111")]
        ),
        master_record=SimpleNamespace(nationalid="2222222222"),
        attributes=SimpleNamespace(
            localid=incoming_id,
            sending_extract="UKRDC",
            sending_facility="TEST",
        ),
        destination=SimpleNamespace(
            persons=[
                SimpleNamespace(
                    xref_entries=[
                        SimpleNamespace(
                            sending_extract="UKRDC",
                            sending_facility="TEST",
                            localid=current_id,
                        )
                    ]
                )
            ]
        ),
    )

    messages = [
        SimpleNamespace(
            message_id=101,
            channel_id=script.RDA_INBOUND_FILE,
        ),
        SimpleNamespace(
            message_id=202,
            channel_id=script.PV_INBOUND,
        )
    ]

    # Mock the database sessions and query helpers.
    jtrace_session = MagicMock()
    jtrace = jtrace_session.return_value.__enter__.return_value
    db_workitem = Mock()
    jtrace.get.return_value = db_workitem

    errors_session = MagicMock()
    errorsdb = errors_session.return_value.__enter__.return_value
    errorsdb.scalars.return_value.all.return_value = messages

    extend_workitem = Mock(return_value=workitem)
    select_messages = Mock()
    message_schema = Mock()
    message_schema.model_validate.side_effect = lambda message: message

    monkeypatch.setattr(script, "jtrace_session", jtrace_session)
    monkeypatch.setattr(script, "errors_session", errors_session)
    monkeypatch.setattr(script, "extend_workitem", extend_workitem)
    monkeypatch.setattr(script, "select_messages", select_messages)
    monkeypatch.setattr(script, "MessageSchema", message_schema)

    raw_xml = """
    <MirthDocument>
        <PatientNumbers>
            <PatientNumber>
                <Number>
                    OLD123
                </Number>
                <Organization>
                    LOCALHOSP
                </Organization>
                <NumberType>
                    MRN
                </NumberType>
                <OptionalField/>
            </PatientNumber>
        </PatientNumbers>
        <EmptyData>
            <ImportantData>
                <Information>NEW456\nVERY IMPORTANT</Information>
            </ImportantData>
            <EmptyNumber></EmptyNumber>
        </EmptyData>
    </MirthDocument>"""

    channels = {}
    for message in messages:
        channel = Mock()
        channel.get_message = AsyncMock(
            return_value=SimpleNamespace(
                connector_messages=[
                    SimpleNamespace(
                        raw=SimpleNamespace(content=raw_xml),
                        meta_data_map={"FILE": f"{message.message_id}.xml"},
                    )
                ]
            )
        )
        channel.post_message = AsyncMock()
        channel.reprocess_message = AsyncMock()
        channels[message.channel_id] = channel

    api = Mock()
    api.channel.side_effect = channels.__getitem__

    mirth_session = MagicMock()
    mirth_session.return_value.__aenter__.return_value = api
    monkeypatch.setattr(script, "mirth_session", mirth_session)

    # The real script waits for 5 seconds between sending corrections and reprocessing the original message. 
    # We can just mock it so that the test runs without delay.
    sleep = Mock()
    monkeypatch.setattr(script.time, "sleep", sleep)

    asyncio.run(script.process_workitem(workitem_id))

    jtrace.get.assert_called_once_with(script.WorkItem, workitem_id)
    extend_workitem.assert_called_once_with(db_workitem, jtrace)
    select_messages.assert_called_once_with(
        statuses=["ERROR"],
        nis=["1111111111", "2222222222"],
    )
    errorsdb.scalars.assert_called_once_with(select_messages.return_value)

    assert api.channel.call_args_list == [
        call(script.RDA_INBOUND_FILE),
        call(script.PV_INBOUND),
    ]

    expected_xml = (
        "<MirthDocument>"
        "<PatientNumbers><PatientNumber>"
        "<Number>NEW456</Number>"
        "<Organization>LOCALHOSP</Organization>"
        "<NumberType>MRN</NumberType>"
        "<OptionalField/>"
        "</PatientNumber></PatientNumbers>"
        "<EmptyData><ImportantData><Information>NEW456\nVERY IMPORTANT</Information></ImportantData><EmptyNumber/></EmptyData>"
        "</MirthDocument>"
    )

    for message in messages[:2]:
        channel = channels[message.channel_id]

        channel.get_message.assert_awaited_once_with(message.message_id)
        channel.post_message.assert_awaited_once_with(
            expected_xml,
            source_map={"originalFilename": f"{message.message_id}.xml"},
        )
        channel.reprocess_message.assert_awaited_once_with(
            message.message_id,
            replace=True,
        )

        # Verify the the new message is submitted and the original is reprocessed.
        assert channel.mock_calls == [
            call.get_message(message.message_id),
            call.post_message(
                expected_xml,
                source_map={"originalFilename": f"{message.message_id}.xml"},
            ),
            call.reprocess_message(message.message_id, replace=True),
        ]