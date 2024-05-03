from .message_channels import ROMessageChannel, WOMessageChannel, RWMessageChannel


def ro_message_channel_factory(
    stream, subject, durable_consumer=None, connection=None
) -> ROMessageChannel:
    """Create a Read Only Message Channel"""
    chan = ROMessageChannel(
        stream=stream,
        subject=subject,
        durable_consumer=durable_consumer,
        connection=connection,
    )
    return chan


def wo_message_channel_factory(
    stream, subject, durable_consumer=None, connection=None
) -> ROMessageChannel:
    """Create a Read Only Message Channel"""
    chan = WOMessageChannel(
        stream=stream,
        subject=subject,
        durable_consumer=durable_consumer,
        connection=connection,
    )
    return chan


def rw_message_channel_factory(
    stream, subject, durable_consumer=None, connection=None
) -> ROMessageChannel:
    """Create a Read Only Message Channel"""
    chan = RWMessageChannel(
        stream=stream,
        subject=subject,
        durable_consumer=durable_consumer,
        connection=connection,
    )
    return chan
