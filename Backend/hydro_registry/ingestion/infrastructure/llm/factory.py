"""Фабрика LLM-порта. Точка подмены в тестах HTTP-шва (мокается этот вызов)."""

from __future__ import annotations

from ...application.ports import SchemaMapper
from .openrouter_mapper import OpenRouterSchemaMapper


def resolve_schema_mapper() -> SchemaMapper:
    return OpenRouterSchemaMapper()
