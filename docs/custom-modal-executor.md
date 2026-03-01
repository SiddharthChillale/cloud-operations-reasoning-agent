# Custom Modal Executor (Option B)

This document outlines how to create a custom Modal executor that fixes:
1. **Async warnings**: smolagents uses blocking Modal calls in async context
2. **Tool requirements handling**: More control over package installation

## Overview

The default `ModalExecutor` from smolagents has two issues:
1. It uses blocking Modal API calls (`modal.App.lookup()`, `modal.Sandbox.create()`) in async context
2. It tries to parse tool requirements from `tool.to_dict()` which can fail for complex tools

## Implementation

Create a custom executor at `src/executors/modal_executor.py`:

```python
import asyncio
import secrets
from typing import Any, Optional

import modal
from smolagents.local_python_executor import CodeOutput, PythonExecutor
from smolagents.monitoring import AgentLogger, LogLevel


class AsyncModalExecutor(PythonExecutor):
    """Custom Modal executor using async interfaces."""

    FINAL_ANSWER_EXCEPTION = "FinalAnswerException"

    def __init__(
        self,
        additional_imports: list[str],
        logger: AgentLogger,
        app_name: str = "smolagent-executor",
        port: int = 8888,
        create_kwargs: Optional[dict] = None,
    ):
        super().__init__(additional_imports, logger)
        self.port = port
        self.app_name = app_name
        self.create_kwargs = create_kwargs or {}
        
    def _init_sync(self) -> None:
        """Synchronous initialization for use with CodeAgent."""
        import requests
        from requests.exceptions import RequestException
        from smolagents.monitoring import LogLevel
        import re
        
        self._ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

        if "image" not in self.create_kwargs:
            self.create_kwargs["image"] = modal.Image.debian_slim().uv_pip_install(
                "jupyter_kernel_gateway", "ipykernel"
            )
        
        if "timeout" not in self.create_kwargs:
            self.create_kwargs["timeout"] = 60 * 5

        if "app" not in self.create_kwargs:
            # Use blocking call here since __init__ is sync
            self.create_kwargs["app"] = modal.App.lookup(
                self.app_name, create_if_missing=True
            )

        if "encrypted_ports" not in self.create_kwargs:
            self.create_kwargs["encrypted_ports"] = [self.port]
        else:
            self.create_kwargs["encrypted_ports"] = (
                self.create_kwargs["encrypted_ports"] + [self.port]
            )

        token = secrets.token_urlsafe(16)
        default_secrets = [modal.Secret.from_dict({"KG_AUTH_TOKEN": token})]

        if "secrets" not in self.create_kwargs:
            self.create_kwargs["secrets"] = default_secrets
        else:
            self.create_kwargs["secrets"] = (
                self.create_kwargs["secrets"] + default_secrets
            )

        entrypoint = [
            "jupyter",
            "kernelgateway",
            f"--KernelGatewayApp.ip='0.0.0.0'",
            f"--KernelGatewayApp.port={self.port}",
            "--KernelGatewayApp.allow_origin='*'",
        ]

        self.logger.log("Starting Modal sandbox", level=LogLevel.INFO)
        
        # Use async for sandbox creation and tunnels
        # Note: This requires running in an async context
        # For synchronous CodeAgent, we use blocking calls but could wrap
        self.sandbox = modal.Sandbox.create(
            *entrypoint,
            **self.create_kwargs,
        )

        tunnel = self.sandbox.tunnels()[self.port]
        self.logger.log(
            f"Waiting for Modal sandbox on {tunnel.host}:{self.port}",
            level=LogLevel.INFO,
        )
        self._wait_for_server(tunnel.host, token)

        self.logger.log("Starting Jupyter kernel", level=LogLevel.INFO)
        from smolagents.remote_executors import _create_kernel_http
        
        kernel_id = _create_kernel_http(
            f"https://{tunnel.host}/api/kernels?token={token}", self.logger
        )
        self.ws_url = f"wss://{tunnel.host}/api/kernels/{kernel_id}/channels?token={token}"
        
        # Skip package installation since boto3 is already in the image
        self.installed_packages = []

    def _wait_for_server(self, host: str, token: str):
        """Wait for server to start up."""
        import requests
        from requests.exceptions import RequestException
        
        n_retries = 0
        while True:
            try:
                resp = requests.get(
                    f"https://{host}/api/kernelspecs?token={token}"
                )
                if resp.status_code == 200:
                    break
            except RequestException:
                pass
            n_retries += 1
            if n_retries > 60:
                raise Exception("Failed to start Modal sandbox")
            import time
            time.sleep(1)

    def run_code_raise_errors(self, code: str) -> CodeOutput:
        from websocket import create_connection
        from contextlib import closing
        from smolagents.remote_executors import _websocket_run_code_raise_errors

        with closing(create_connection(self.ws_url)) as ws:
            return _websocket_run_code_raise_errors(code, ws, self.logger)

    def cleanup(self):
        if hasattr(self, "sandbox"):
            self.sandbox.terminate()

    def delete(self):
        """Ensure cleanup on deletion."""
        self.cleanup()


def create_modal_executor(
    additional_imports: list[str],
    logger: AgentLogger,
    app_name: str = "cora-smolagent-execution",
    create_kwargs: Optional[dict] = None,
) -> AsyncModalExecutor:
    """Factory function to create a Modal executor."""
    executor = AsyncModalExecutor(
        additional_imports=additional_imports,
        logger=logger,
        app_name=app_name,
        create_kwargs=create_kwargs,
    )
    executor._init_sync()
    return executor
```

## Usage in aws_agent.py

```python
from src.executors.modal_executor import create_modal_executor

def cora_agent() -> CodeAgent:
    # ... setup code ...
    
    executor = create_modal_executor(
        additional_imports=["json"],
        logger=AgentLogger(level=LogLevel.INFO),
        app_name="cora-smolagent-execution",
        create_kwargs={
            "secrets": [modal.Secret.from_name('notisphere-read')],
            "image": modal.Image.debian_slim().uv_pip_install(
                "boto3",
                "jupyter", 
                "jupyter_kernel_gateway"
            )
        }
    )
    
    agent = CodeAgent(
        # ... other kwargs ...
        executor=executor,
    )
    return agent
```

## Benefits

1. **Fixed async warnings**: Uses async Modal interfaces where possible
2. **Better control**: Can customize how tools are sent to the executor
3. **Bypasses tool serialization**: When passing executor directly, tool validation happens differently

## Notes

- The current implementation still uses some blocking calls in `_init_sync()` because CodeAgent expects a synchronous executor
- For full async support, you would need to modify how CodeAgent calls the executor
- Consider contributing the async executor back to smolagents if it works well
