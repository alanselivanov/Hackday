"""Фабрика LLM-порта. Точка подмены в тестах HTTP-шва (мокается этот вызов)."""

from __future__ import annotations

import os

from ...application.ports import SchemaMapper
from .openrouter_mapper import OpenRouterSchemaMapper


def resolve_schema_mapper() -> SchemaMapper:
    # Оффлайн-режим без OpenRouter (демо/тесты): INGESTION_FAKE_MAPPER=1 в .env.
    if os.getenv("INGESTION_FAKE_MAPPER"):
        from .heuristic_mapper import HeuristicSchemaMapper

        return HeuristicSchemaMapper()
    return OpenRouterSchemaMapper()
