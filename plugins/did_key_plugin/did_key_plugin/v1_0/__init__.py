import logging

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.wallet.did_method import DIDMethod, DIDMethods
from aries_cloudagent.wallet.key_type import ED25519, BLS12381G2
from aries_cloudagent.core.event_bus import EventBus
from aries_cloudagent.core.plugin_registry import PluginRegistry
from aries_cloudagent.core.protocol_registry import ProtocolRegistry

LOGGER = logging.getLogger(__name__)


async def setup(context: InjectionContext):
    LOGGER.info("> DID key plugin setup...")
    KEY = DIDMethod(
        name="key",
        key_types=[ED25519, BLS12381G2],
        rotation=False,
    )
    did_methods = context.injector.inject_or(DIDMethods)
    did_methods.register(KEY)

    protocol_registry = context.inject(ProtocolRegistry)
    if not protocol_registry:
        raise ValueError("ProtocolRegistry missing in context")

    plugin_registry = context.inject(PluginRegistry)
    if not plugin_registry:
        raise ValueError("PluginRegistry missing in context")

    bus = context.inject(EventBus)
    if not bus:
        raise ValueError("EventBus missing in context")
    
    LOGGER.info("< DID key plugin setup complete")
