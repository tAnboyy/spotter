"""ASGI entrypoint for a backend-only checkout or deployment root."""
if __package__:
    from .spotter.app import CATALOG, app, create_app
else:
    from spotter.app import CATALOG, app, create_app

__all__ = ["app", "create_app", "CATALOG"]
