"""Thin hooks share runtime state even when Crew reloads individual hook modules."""
from .runtime import on_startup, on_shutdown, register_routes
