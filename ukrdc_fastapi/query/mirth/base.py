from mirth_client import Channel, MirthAPI
from redis import Redis

from ukrdc_fastapi.exceptions import ResourceNotFoundError
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema, get_channel_from_name


async def safe_send_mirth_message(
    channel: Channel, message: str
) -> MirthMessageResponseSchema:
    """Send a message to a Mirth channel

    Args:
        channel (Channel): Mirth API channel
        message (str): Message to send

    Returns:
        MirthMessageResponseSchema: Mirth response status
    """
    await channel.post_message(message)
    return MirthMessageResponseSchema(status="success", message=message)


async def safe_send_mirth_message_to_name(
    channel_name: str, message: str, mirth: MirthAPI, redis: Redis
) -> MirthMessageResponseSchema:
    """Get a channel by name and send a message

    Args:
        channel_name (str): Mirth channel name
        message (str): Message to send
        mirth (MirthAPI): Mirth API instance
        redis (Redis): Redis instance for cached name lookup

    Returns:
        MirthMessageResponseSchema: Mirth response status
    """
    channel = await get_channel_from_name(channel_name, mirth, redis)
    if not channel:
        raise ResourceNotFoundError(f"ID for {channel_name} channel not found")

    return await safe_send_mirth_message(channel, message)
