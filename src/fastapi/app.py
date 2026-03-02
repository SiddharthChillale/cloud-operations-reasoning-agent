import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Coroutine, Dict, Optional

import anyio
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from smolagents.memory import ActionStep, PlanningStep, FinalAnswerStep

from src.agents import SessionAgentFactory
from src.session.database import SessionDatabase
from src.session.manager import SessionManager
from src.session.models import MessageRole, SessionStatus
from src.utils.logging import setup_logging, get_logger
from src.utils.serializers import serialize_agent_output

load_dotenv()

setup_logging(log_file="webapp.log")
logger = get_logger(__name__)

_db: Optional[SessionDatabase] = None
_session_manager: Optional[SessionManager] = None
_agent_factory: Optional[SessionAgentFactory] = None
_step_queues: Dict[str, asyncio.Queue] = {}
_active_runs: Dict[str, dict] = {}


def get_db() -> SessionDatabase:
    if _db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return _db


def get_session_manager() -> SessionManager:
    if _session_manager is None:
        raise HTTPException(status_code=500, detail="Session manager not initialized")
    return _session_manager


def get_agent_factory() -> SessionAgentFactory:
    if _agent_factory is None:
        raise HTTPException(status_code=500, detail="Agent factory not initialized")
    return _agent_factory


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _db, _session_manager, _agent_factory

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable is missing")
        if os.getenv("VERCEL"):
            raise ValueError("DATABASE_URL is required for Vercel deployment")

    _db = SessionDatabase(db_url=db_url)
    await _db.init_db()

    _session_manager = SessionManager(db_url=db_url)
    await _session_manager.initialize()

    _agent_factory = SessionAgentFactory(_session_manager)
    logger.info("Web UI initialized with PostgreSQL database")
    yield
    logger.info("Web UI shutting down")


app = FastAPI(title="CORA Web API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


def create_step_callback(session_id: str, run_number: int):
    """Create a step callback that pushes events to queue and saves to DB."""
    step_counter = {"count": 0}
    try:
        app_loop = asyncio.get_running_loop()
    except RuntimeError:
        app_loop = None

    def callback(memory_step: Any) -> None:
        step_index = step_counter["count"]
        step_counter["count"] += 1
        step_number = step_index + 1
        step_type = type(memory_step).__name__

        event_data = {
            "session_id": session_id,
            "run_number": run_number,
            "step_number": step_number,
            "step_type": step_type,
        }

        if isinstance(memory_step, PlanningStep):
            event_data.update(
                {
                    "type": "planning",
                    "plan": str(memory_step.plan) if memory_step.plan else "",
                }
            )
        elif isinstance(memory_step, ActionStep):
            event_data.update(
                {
                    "type": "action",
                    "model_output": str(memory_step.model_output)
                    if memory_step.model_output
                    else "",
                    "code_action": str(memory_step.code_action)
                    if memory_step.code_action
                    else "",
                    "observations": str(memory_step.observations)
                    if memory_step.observations
                    else "",
                    "error": str(memory_step.error) if memory_step.error else None,
                    "is_final_answer": memory_step.is_final_answer,
                }
            )
        elif isinstance(memory_step, FinalAnswerStep):
            event_data.update(
                {
                    "type": "final",
                    "output": str(memory_step.output) if memory_step.output else "",
                }
            )
        else:
            return

        # Add token usage if available
        token_usage = getattr(memory_step, "token_usage", None)
        if token_usage:
            event_data["token_usage"] = {
                "input_tokens": getattr(token_usage, "input_tokens", 0),
                "output_tokens": getattr(token_usage, "output_tokens", 0),
                "total_tokens": getattr(token_usage, "total_tokens", 0),
            }

        # Safe queue push from thread
        if app_loop and session_id in _step_queues:
            app_loop.call_soon_threadsafe(
                _step_queues[session_id].put_nowait, event_data
            )

        # Safe DB save from thread
        session_manager = _session_manager
        if app_loop and session_manager:
            asyncio.run_coroutine_threadsafe(
                session_manager.save_step_token_from_step(
                    session_id, run_number, step_index, memory_step
                ),
                app_loop,
            )

    return callback


@app.options("/{full_path:path}")
async def handle_options(full_path: str, request: Request):
    return JSONResponse(content={}, status_code=200)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/sessions")
async def list_sessions():
    db = get_db()
    sessions = await db.get_all_sessions()
    return JSONResponse(
        content={
            "sessions": [
                {
                    "id": s.id,
                    "title": s.title,
                    "status": s.status.value
                    if hasattr(s.status, "value")
                    else s.status,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                }
                for s in sessions
            ]
        }
    )


@app.post("/sessions")
async def create_session(request: Request):
    db = get_db()
    body = await request.json()
    title = body.get("title", "New Chat")

    if not title or (isinstance(title, str) and title.strip() == ""):
        title = "New Chat"

    session = await db.create_session(title)

    return JSONResponse(
        content={
            "session_id": session.id,
            "redirect_url": f"/sessions/{session.id}",
        }
    )


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    db = get_db()
    session_manager = get_session_manager()
    session = await db.get_session(session_id)
    if not session:
        return JSONResponse(content={"error": "Session not found"}, status_code=404)

    tokens = await session_manager.get_session_tokens(session_id)

    return JSONResponse(
        content={
            "session": {
                "id": session.id,
                "title": session.title,
                "status": session.status.value
                if hasattr(session.status, "value")
                else session.status,
                "created_at": session.created_at.isoformat()
                if session.created_at
                else None,
                "updated_at": session.updated_at.isoformat()
                if session.updated_at
                else None,
            },
            "messages": [
                {
                    "id": m.id,
                    "role": m.role.value if hasattr(m.role, "value") else m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                }
                for m in session.messages
            ],
            "tokens": tokens,
        }
    )


@app.patch("/sessions/{session_id}")
async def update_session_title(request: Request, session_id: str):
    db = get_db()
    body = await request.json()
    title = body.get("title", "New Chat")

    await db.update_session_title(session_id, title)

    return JSONResponse(content={"success": True})


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    db = get_db()
    await db.delete_session(session_id)

    return JSONResponse(content={"success": True, "redirect_url": "/"})


@app.post("/sessions/{session_id}/interrupt")
async def interrupt_session(session_id: str):
    if session_id not in _active_runs:
        return JSONResponse(
            content={"error": "No active run found for this session"},
            status_code=404,
        )

    run_info = _active_runs[session_id]
    agent = run_info.get("agent")
    task = run_info.get("task")
    queue = run_info.get("queue")

    if agent:
        try:
            agent.interrupt()
            logger.info(f"Interrupted agent for session {session_id}")
        except Exception as e:
            logger.warning(f"Failed to interrupt agent: {e}")

    if task and not task.done():
        try:
            task.cancel()
            logger.info(f"Cancelled task for session {session_id}")
        except Exception as e:
            logger.warning(f"Failed to cancel task: {e}")

    if queue:
        try:
            await queue.put({"type": "cancelled"})
            logger.info(f"Sent cancellation signal to queue for session {session_id}")
        except Exception as e:
            logger.warning(f"Failed to send cancellation signal: {e}")

    return JSONResponse(content={"success": True, "message": "Agent interrupted"})


@app.get("/sessions/{session_id}/stream")
async def stream_chat(request: Request, session_id: str, query: str = ""):
    db = get_db()
    session_manager = get_session_manager()
    agent_factory = get_agent_factory()

    if not query:
        return JSONResponse(
            content={"error": "Query parameter is required"}, status_code=400
        )

    session = await db.get_session(session_id)
    if not session:
        return JSONResponse(content={"error": "Session not found"}, status_code=404)

    # Check if this is the first user message
    existing_user_messages = [m for m in session.messages if m.role == MessageRole.USER]
    if not existing_user_messages:
        # First user message - set title (27 chars + "..." = 30 chars)
        title = query[:27] + "..." if len(query) > 30 else query
        await db.update_session_title(session_id, title)

    await db.add_message(session_id, MessageRole.USER, query)
    await db.update_session_status(session_id, SessionStatus.RUNNING)

    run_number = await session_manager.get_next_run_number(session_id)

    step_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _step_queues[session_id] = step_queue

    step_callback = create_step_callback(session_id, run_number)

    agent_task = None

    async def event_generator():
        nonlocal session, agent_task
        agent = None
        agent_task = None
        response = None
        agent_completed = False
        agent_exception = None
        is_cancelled = False

        _active_runs[session_id] = {
            "agent": None,
            "task": None,
            "queue": step_queue,
        }

        yield {
            "data": json.dumps(
                {
                    "type": "message",
                    "role": "user",
                    "content": query,
                }
            ),
        }

        try:
            agent = await agent_factory.get_agent(session_id, step_callback)
            _active_runs[session_id]["agent"] = agent

            def run_agent():
                try:
                    return agent.run(query, reset=False)
                except Exception as e:
                    logger.exception(f"Error in agent.run for session {session_id}")
                    return e

            async def run_agent_async():
                nonlocal response, agent_completed, agent_exception
                try:
                    # Run agent in thread pool to avoid blocking event loop
                    response = await anyio.to_thread.run_sync(run_agent)
                    if isinstance(response, Exception):
                        agent_exception = response
                except Exception as e:
                    logger.exception(
                        f"Exception in run_agent_async for session {session_id}"
                    )
                    agent_exception = e
                finally:
                    agent_completed = True

            async def read_queue():
                nonlocal agent_completed, is_cancelled, agent_exception
                while not agent_completed or not step_queue.empty():
                    # If an exception occurred, we want to stop reading and let the main loop handle it
                    if agent_exception:
                        break

                    try:
                        event_data = await asyncio.wait_for(
                            step_queue.get(), timeout=0.2
                        )
                        event_type = event_data.get("type", "step")

                        if event_type == "cancelled":
                            is_cancelled = True
                            break
                        elif event_type in ["planning", "action"]:
                            yield {"data": json.dumps(event_data)}
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        logger.error(f"Error reading from step queue: {e}")
                        break

            agent_task = asyncio.create_task(run_agent_async())
            _active_runs[session_id]["task"] = agent_task

            async for event in read_queue():
                if is_cancelled:
                    break
                yield event

            if is_cancelled:
                if agent_task and not agent_task.done():
                    agent_task.cancel()
                yield {"data": json.dumps({"type": "cancelled"})}
            else:
                await agent_task

                if agent_exception:
                    raise agent_exception

                for step in agent.memory.steps:
                    agent_factory.save_agent(agent, session_id, run_number)

                serialized = serialize_agent_output(
                    response, session_id, str(request.base_url)
                )
                final_output = serialized.output

                await db.add_message(session_id, MessageRole.AGENT, final_output)

                yield {
                    "data": json.dumps(
                        {
                            "type": "final",
                            "output": serialized.output,
                            "output_type": serialized.output_type,
                            "url": serialized.url,
                            "mime_type": serialized.mime_type,
                        }
                    ),
                }

                await db.update_session_status(session_id, SessionStatus.COMPLETED)
                agent_factory.save_agent(agent, session_id, run_number)

        except Exception as e:
            logger.exception(f"Agent error: {e}")
            yield {
                "data": json.dumps(
                    {
                        "type": "error",
                        "error": str(e),
                    }
                ),
            }
            await db.update_session_status(session_id, SessionStatus.IDLE)

        finally:
            if session_id in _step_queues:
                del _step_queues[session_id]
            if session_id in _active_runs:
                del _active_runs[session_id]

        if not is_cancelled:
            yield {"data": json.dumps({"type": "done"})}

    return EventSourceResponse(event_generator())


@app.get("/sessions/{session_id}/tokens")
async def get_tokens(session_id: str):
    session_manager = get_session_manager()
    tokens = await session_manager.get_session_tokens(session_id)

    return JSONResponse(content={"tokens": tokens})


def main():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
