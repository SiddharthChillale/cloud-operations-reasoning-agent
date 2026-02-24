from .app import ChatApp, main

__all__ = ["ChatApp", "main"]


def cora():
    """Launch the TUI application."""
    from clients.tui.app import ChatApp

    app = ChatApp()
    app.run()
