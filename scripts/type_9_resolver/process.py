import asyncio
from ukrdc_fastapi.dependencies.mirth import mirth_session
from ukrdc_fastapi.query.workitems import extend_workitem
from ukrdc_fastapi.query.messages import select_messages
from ukrdc_fastapi.dependencies.database import jtrace_session, errors_session
from ukrdc_fastapi.schemas.message import MessageSchema
from ukrdc_sqla.empi import WorkItem
import time
import argparse

PV_INBOUND = "3cdefad2-bf10-49ee-81c9-8ac6fd2fed67"
RDA_INBOUND_FILE = "ed8216c6-cc25-45ad-adcc-e3dd4359e37a"
CHANNEL_IDS = [RDA_INBOUND_FILE, PV_INBOUND]


async def process_workitem(workitem_id: int):
    # Find workitem and related messages
    with jtrace_session() as jtrace, errors_session() as errorsdb:
        workitem_obj = extend_workitem(jtrace.query(WorkItem).get(workitem_id), jtrace)

        assert workitem_obj.type == 9

        print(f"Working on workitem {workitem_obj.id}...")

        workitem_nis: list[str] = [
            record.nationalid for record in workitem_obj.incoming.master_records
        ]
        if workitem_obj.master_record:
            workitem_nis.append(workitem_obj.master_record.nationalid.strip())

        print(f"nis: {workitem_nis}")

        messages = [
            MessageSchema.from_orm(msg)
            for msg in select_messages(
                errorsdb,
                statuses=["ERROR"],
                nis=workitem_nis,
            )
        ]

    for CHANNEL_ID in CHANNEL_IDS:
        # Get message IDs
        messages_to_process = [msg for msg in messages if msg.channel_id == CHANNEL_ID]
        message_ids = [m.message_id for m in messages_to_process]
        print(f"message_ids: {message_ids}")

        # Find incoming and current local IDs
        if workitem_obj.attributes:
            incoming_id = workitem_obj.attributes.localid
            print(f"incoming id: {incoming_id}")

            sending_extract = workitem_obj.attributes.sending_extract
            sending_facility = workitem_obj.attributes.sending_facility

            destination_persons = [
                person
                for person in workitem_obj.destination.persons
                if person.xref_entries[0].sending_extract == sending_extract
                and person.xref_entries[0].sending_facility == sending_facility
            ]

            if len(destination_persons) != 1:
                raise RuntimeError(
                    f"Ambiguous destination person records. Expected 1, got {len(destination_persons)}"
                )
            assert len(destination_persons) == 1

            destination_person = destination_persons[0]
            current_id = destination_person.xref_entries[0].localid

            print(f"current id: {current_id}")

            # Start sending messages to Mirth
            if incoming_id and current_id:
                async with mirth_session() as api:
                    ch = api.channel(CHANNEL_ID)

                    for message_id in message_ids:
                        msg = await ch.get_message(message_id)

                        # Calculate correctional message content
                        if msg and msg.connector_messages[0].raw:
                            content = msg.connector_messages[0].raw.content
                            original_filename = msg.connector_messages[0].meta_data_map[
                                "FILE"
                            ]

                            if content:
                                content_current_id = content.replace(
                                    incoming_id, current_id
                                )

                                # Send correctional message
                                print(
                                    f"Sending correctional message for {message_id}..."
                                )
                                await ch.post_message(
                                    content_current_id,
                                    source_map={"originalFilename": original_filename},
                                )

                                time.sleep(5)

                                # Reprocess original message
                                print(f"Reprocessing original message {message_id}...")
                                await ch.reprocess_message(message_id, replace=True)

    print("Done!")
    print("NOTE: This script does not close workitems. Please close them manually.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Attempt to automatically resolve and reprocess type-9 JTRACE work items",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("workitem_id", type=int, help="ID of the type-9 work item.")

    args = parser.parse_args()

    asyncio.run(process_workitem(args.workitem_id))
