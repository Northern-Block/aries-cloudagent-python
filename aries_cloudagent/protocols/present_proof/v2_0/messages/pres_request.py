"""A presentation request content message."""

import base64
from typing import Sequence

from marshmallow import EXCLUDE, ValidationError, fields, validates_schema

from .....messaging.agent_message import AgentMessage, AgentMessageSchema
from .....messaging.decorators.attach_decorator import (
    AttachDecorator,
    AttachDecoratorSchema,
)
from ..message_types import PRES_20_REQUEST, PROTOCOL_PACKAGE
from .pres_format import V20PresFormat, V20PresFormatSchema

HANDLER_CLASS = (
    f"{PROTOCOL_PACKAGE}.handlers.pres_request_handler.V20PresRequestHandler"
)


class V20PresRequest(AgentMessage):
    """Class representing a presentation request."""

    class Meta:
        """V20PresRequest metadata."""

        handler_class = HANDLER_CLASS
        schema_class = "V20PresRequestSchema"
        message_type = PRES_20_REQUEST

    def __init__(
        self,
        _id: str = None,
        *,
        comment: str = None,
        verifier_did: str = None,
        will_confirm: bool = None,
        formats: Sequence[V20PresFormat] = None,
        signature: bytes = None,
        request_presentations_attach: Sequence[AttachDecorator] = None,
        **kwargs,
    ):
        """Initialize presentation request object.

        Args:
            _id (str, optional): The ID of the presentation request.
            comment (str, optional): An optional comment.
            verifier_did (str, optional): The DID of the verifier.
            will_confirm (bool, optional): A flag indicating whether the presentation
                request will be confirmed.
            formats (Sequence[V20PresFormat], optional): A sequence of presentation
                formats.
            signature (dict, optional): signature object for verifier did.
            request_presentations_attach (Sequence[AttachDecorator], optional): A
                sequence of proof request attachments.
            kwargs: Additional keyword arguments.

        """
        super().__init__(_id=_id, **kwargs)
        self.comment = comment
        self.verifier_did = verifier_did
        self.will_confirm = will_confirm or False
        self.formats = list(formats) if formats else []
        self.signature = signature
        self.request_presentations_attach = (
            list(request_presentations_attach) if request_presentations_attach else []
        )

    def attachment(self, fmt: V20PresFormat.Format = None) -> dict:
        """Return attached presentation request item.

        Args:
            fmt: format of attachment in list to decode and return

        """
        target_format = (
            fmt
            if fmt
            else next(
                filter(
                    lambda ff: ff,
                    [V20PresFormat.Format.get(f.format) for f in self.formats],
                ),
                None,
            )
        )
        return (
            target_format.get_attachment_data(
                self.formats,
                self.request_presentations_attach,
            )
            if target_format
            else None
        )

    def add_signature(self, sign: bytes):
        """Add signature to request."""
        self.signature = base64.b64encode(sign).decode("utf-8")


class V20PresRequestSchema(AgentMessageSchema):
    """Presentation request schema."""

    class Meta:
        """V20PresRequest schema metadata."""

        model_class = V20PresRequest
        unknown = EXCLUDE

    comment = fields.Str(
        required=False, metadata={"description": "Human-readable comment"}
    )
    will_confirm = fields.Bool(
        required=False,
        metadata={"description": "Whether verifier will send confirmation ack"},
    )
    verifier_did = fields.Str(
        required=False,
        metadata={"description": "DID of the verifier"},
    )
    formats = fields.Nested(
        V20PresFormatSchema,
        many=True,
        required=True,
        metadata={"description": "Acceptable attachment formats"},
    )
    signature = fields.Str(
        required=False,
        metadata={"description": "signature for verifier did"},
    )
    request_presentations_attach = fields.Nested(
        AttachDecoratorSchema,
        many=True,
        required=True,
        data_key="request_presentations~attach",
        metadata={
            "description": (
                "Attachment per acceptable format on corresponding identifier"
            )
        },
    )

    @validates_schema
    def validate_fields(self, data, **kwargs):
        """Validate proposal attachment per format."""

        def get_attach_by_id(attach_id):
            """Return attachment with input attachment identifier."""
            for atch in attachments:
                if atch.ident == attach_id:
                    return atch
            raise ValidationError(f"No attachment for attach_id {attach_id} in formats")

        formats = data.get("formats") or []
        attachments = data.get("request_presentations_attach") or []
        if len(formats) != len(attachments):
            raise ValidationError("Formats/attachments length mismatch")

        for fmt in formats:
            atch = get_attach_by_id(fmt.attach_id)

            pres_format = V20PresFormat.Format.get(fmt.format)
            if pres_format:
                pres_format.validate_fields(PRES_20_REQUEST, atch.content)
