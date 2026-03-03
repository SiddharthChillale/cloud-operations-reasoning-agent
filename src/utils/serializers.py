import base64
import uuid
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

from smolagents.agent_types import AgentImage, AgentText

from src.config import get_config


@dataclass
class MultimodalOutput:
    output: str
    output_type: str
    url: Optional[str]
    mime_type: Optional[str]


def serialize_agent_output(
    response: Any,
    session_id: str,
    base_url: str,
) -> MultimodalOutput:
    """Serialize agent output to structured format with image support."""
    if isinstance(response, AgentImage):
        return _serialize_image(response, session_id, base_url)
    elif isinstance(response, AgentText):
        return MultimodalOutput(
            output=str(response),
            output_type="text",
            url=None,
            mime_type="text/plain",
        )
    else:
        return MultimodalOutput(
            output=str(response),
            output_type="text",
            url=None,
            mime_type=None,
        )


def _serialize_image(
    agent_image: AgentImage,
    session_id: str,
    base_url: str,
) -> MultimodalOutput:
    """Convert AgentImage to URL (Supabase if available, otherwise base64 data URL)."""
    config = get_config()
    image = getattr(agent_image, "value", agent_image)

    if config.has_supabase:
        try:
            from src.storage.supabase_storage import get_storage_service

            storage = get_storage_service()
            public_url = storage.upload_image(
                image=image,
                folder=f"sessions/{session_id}",
            )
            return MultimodalOutput(
                output=str(agent_image),
                output_type="image",
                url=public_url,
                mime_type="image/png",
            )
        except Exception as e:
            import logging

            logging.warning(
                f"Failed to upload to Supabase, falling back to base64: {e}"
            )

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()
    base64_str = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:image/png;base64,{base64_str}"

    return MultimodalOutput(
        output=str(agent_image),
        output_type="image",
        url=data_url,
        mime_type="image/png",
    )


def get_uploads_dir() -> Path:
    return Path("uploads")
