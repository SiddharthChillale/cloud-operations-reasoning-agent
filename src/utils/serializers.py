import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from smolagents.agent_types import AgentImage, AgentText

UPLOADS_DIR = Path("clients/web_ui/static/uploads")


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
    """Save AgentImage to disk and return URL."""
    image = getattr(agent_image, "value", agent_image)

    session_dir = UPLOADS_DIR / f"session-{session_id}"
    session_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{timestamp}_{unique_id}.png"
    filepath = session_dir / filename

    image.save(filepath, format="PNG")

    url = f"{base_url}/uploads/session-{session_id}/{filename}"

    return MultimodalOutput(
        output=str(agent_image),
        output_type="image",
        url=url,
        mime_type="image/png",
    )


def get_uploads_dir() -> Path:
    return UPLOADS_DIR
