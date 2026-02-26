import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import anyio
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse
from smolagents.memory import ActionStep, PlanningStep, FinalAnswerStep

from src.agents import SessionAgentFactory
from src.session.database import SessionDatabase
from src.session.manager import SessionManager
from src.session.models import MessageRole, SessionStatus
from src.utils.logging import setup_logging, get_logger

load_dotenv()

setup_logging(log_file="webapp.log")
logger = get_logger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

_db: SessionDatabase | None = None
_session_manager: SessionManager | None = None
_agent_factory: SessionAgentFactory | None = None
_step_queues: dict[str, asyncio.Queue] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _db, _session_manager, _agent_factory
    _db = SessionDatabase()
    await _db.init_db()
    _session_manager = SessionManager()
    await _session_manager.initialize()
    _agent_factory = SessionAgentFactory(_session_manager)
    logger.info("Web UI initialized")
    yield
    logger.info("Web UI shutting down")


app = FastAPI(title="CORA Web UI", lifespan=lifespan)


def is_htmx_request(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


def create_step_callback(session_id: str, run_number: int):
    """Create a step callback that pushes events to queue and saves to DB."""
    step_counter = {"count": 0}

    def callback(memory_step: Any, agent: Any) -> None:
        step_index = step_counter["count"]
        step_counter["count"] += 1
        step_number = step_index + 1
        step_type = type(memory_step).__name__

        if isinstance(memory_step, PlanningStep):
            event_data = {
                "type": "planning",
                "step_number": step_number,
                "step_type": step_type,
                "plan": str(memory_step.plan) if memory_step.plan else "",
            }

            if hasattr(memory_step, "token_usage") and memory_step.token_usage:
                tu = memory_step.token_usage
                event_data["token_usage"] = {
                    "step_number": step_number,
                    "step_type": step_type,
                    "input_tokens": getattr(tu, "input_tokens", 0),
                    "output_tokens": getattr(tu, "output_tokens", 0),
                    "total_tokens": getattr(tu, "total_tokens", 0),
                }
        elif isinstance(memory_step, ActionStep):
            event_data = {
                "type": "action",
                "step_number": step_number,
                "step_type": step_type,
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

            if hasattr(memory_step, "token_usage") and memory_step.token_usage:
                tu = memory_step.token_usage
                event_data["token_usage"] = {
                    "step_number": step_number,
                    "step_type": step_type,
                    "input_tokens": getattr(tu, "input_tokens", 0),
                    "output_tokens": getattr(tu, "output_tokens", 0),
                    "total_tokens": getattr(tu, "total_tokens", 0),
                }
        elif isinstance(memory_step, FinalAnswerStep):
            event_data = {
                "type": "final",
                "step_number": step_number,
                "step_type": step_type,
                "output": str(memory_step.output) if memory_step.output else "",
            }
        else:
            return

        if session_id in _step_queues:
            try:
                _step_queues[session_id].put_nowait(event_data)
            except asyncio.QueueFull:
                logger.warning(f"Queue full for session {session_id}")

        if _session_manager:
            try:
                asyncio.create_task(
                    _session_manager.save_step_token_from_step(
                        session_id, run_number, step_index, memory_step
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to schedule DB save for step: {e}")

    return callback


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    sessions = await _db.get_all_sessions()
    is_htmx = is_htmx_request(request)

    if is_htmx:
        return templates.TemplateResponse(
            "main_content.html", {"request": request, "sessions": sessions}
        )

    return templates.TemplateResponse(
        "base.html",
        {
            "request": request,
            "sessions": sessions,
            "current_session": None,
        },
    )


@app.get("/sessions", response_class=HTMLResponse)
async def list_sessions(request: Request):
    sessions = await _db.get_all_sessions()
    return templates.TemplateResponse(
        "sidebar.html", {"request": request, "sessions": sessions}
    )


@app.post("/sessions", response_class=HTMLResponse)
async def create_session(request: Request):
    form_data = await request.form()
    title = form_data.get("title", "New Chat")
    if not title or title.strip() == "":
        title = "New Chat"

    session = await _db.create_session(title)
    return RedirectResponse(url=f"/sessions/{session.id}", status_code=303)


@app.get("/sessions/{session_id}", response_class=HTMLResponse)
async def get_session(request: Request, session_id: str):
    session = await _db.get_session(session_id)
    if not session:
        return RedirectResponse(url="/", status_code=303)

    sessions = await _db.get_all_sessions()
    is_htmx = is_htmx_request(request)

    tokens = await _session_manager.get_session_tokens(session_id)

    if is_htmx:
        return templates.TemplateResponse(
            "main_content.html",
            {
                "request": request,
                "sessions": sessions,
                "current_session": session,
                "tokens": tokens,
            },
        )

    return templates.TemplateResponse(
        "base.html",
        {
            "request": request,
            "sessions": sessions,
            "current_session": session,
            "tokens": tokens,
        },
    )


@app.patch("/sessions/{session_id}", response_class=HTMLResponse)
async def update_session_title(request: Request, session_id: str):
    form_data = await request.form()
    title = form_data.get("title", "New Chat")
    await _db.update_session_title(session_id, title)
    sessions = await _db.get_all_sessions()
    return templates.TemplateResponse(
        "sidebar.html", {"request": request, "sessions": sessions}
    )


@app.delete("/sessions/{session_id}", response_class=HTMLResponse)
async def delete_session(request: Request, session_id: str):
    await _db.delete_session(session_id)
    return RedirectResponse(url="/", status_code=303)


@app.post("/sessions/{session_id}/stream")
async def stream_chat(request: Request, session_id: str):
    form_data = await request.form()
    query = form_data.get("query", "")

    if not query:
        return {"error": "Query is required"}

    session = await _db.get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    await _db.add_message(session_id, MessageRole.USER, query)
    await _db.update_session_status(session_id, SessionStatus.RUNNING)

    run_number = await _session_manager.get_next_run_number(session_id)

    step_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _step_queues[session_id] = step_queue

    step_callback = create_step_callback(session_id, run_number)

    async def event_generator():
        nonlocal session
        agent = None
        agent_task = None
        response = None
        agent_completed = False
        agent_exception = None

        yield {
            "data": templates.get_template("message.html").render(
                role="user", content=query
            ),
        }

        try:
            agent = await _agent_factory.get_agent(session_id, step_callback)

            def run_agent():
                try:
                    return agent.run(query)
                except Exception as e:
                    return e

            async def run_agent_async():
                nonlocal response, agent_completed, agent_exception
                try:
                    response = await anyio.to_thread.run_sync(run_agent)
                    if isinstance(response, Exception):
                        agent_exception = response
                    agent_completed = True
                except Exception as e:
                    agent_exception = e
                    agent_completed = True

            async def read_queue():
                nonlocal agent_completed
                while not agent_completed or not step_queue.empty():
                    try:
                        event_data = await asyncio.wait_for(
                            step_queue.get(), timeout=0.5
                        )
                        event_type = event_data.get("type", "step")

                        if event_type == "planning":
                            html = templates.get_template("step_planning.html").render(
                                step_number=event_data.get("step_number"),
                                plan=event_data.get("plan"),
                                token_usage=event_data.get("token_usage"),
                            )
                            yield {"data": html}
                        elif event_type == "action":
                            html = templates.get_template("step_action.html").render(
                                step_number=event_data.get("step_number"),
                                model_output=event_data.get("model_output"),
                                code_action=event_data.get("code_action"),
                                observations=event_data.get("observations"),
                                error=event_data.get("error"),
                                token_usage=event_data.get("token_usage"),
                            )
                            yield {"data": html}
                    except asyncio.TimeoutError:
                        pass

            agent_task = asyncio.create_task(run_agent_async())

            async for event in read_queue():
                yield event

            await agent_task

            if agent_exception:
                raise agent_exception

            for step in agent.memory.steps:
                _agent_factory.save_agent(agent, session_id, run_number)

            final_output = response if isinstance(response, str) else str(response)

            await _db.add_message(session_id, MessageRole.AGENT, final_output)

            yield {
                "data": templates.get_template("step_final.html").render(
                    output=final_output
                ),
            }

            await _db.update_session_status(session_id, SessionStatus.COMPLETED)
            _agent_factory.save_agent(agent, session_id, run_number)

        except Exception as e:
            logger.exception(f"Agent error: {e}")
            yield {
                "data": f'<div class="alert alert-error"><span>Error: {str(e)}</span></div>',
            }
            await _db.update_session_status(session_id, SessionStatus.IDLE)

        finally:
            if session_id in _step_queues:
                del _step_queues[session_id]

    return EventSourceResponse(event_generator())


@app.get("/sessions/{session_id}/tokens", response_class=HTMLResponse)
async def get_tokens(request: Request, session_id: str):
    tokens = await _session_manager.get_session_tokens(session_id)
    return templates.TemplateResponse(
        "token_usage.html", {"request": request, "tokens": tokens}
    )


def main():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
