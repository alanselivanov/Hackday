"""Чистые тесты устойчивости разбора ответа LLM — без сети и Django."""

import unittest

from ingestion.infrastructure.llm.openrouter_mapper import OpenRouterSchemaMapper

_parse = OpenRouterSchemaMapper._parse


class ParseTests(unittest.TestCase):
    def test_parses_plain_json(self):
        result = _parse('{"facility_type": "canal", "mapping": {"0": "name"}}')
        self.assertEqual(result.facility_type, "canal")
        self.assertEqual(result.mapping, {0: "name"})

    def test_strips_markdown_fences_and_prose(self):
        raw = 'Вот результат:\n```json\n{"facility_type": "sluice", "mapping": {"1": "gate_type"}}\n```'
        result = _parse(raw)
        self.assertEqual(result.facility_type, "sluice")
        self.assertEqual(result.mapping, {1: "gate_type"})

    def test_missing_facility_type_yields_empty_not_crash(self):
        result = _parse('{"mapping": {}}')
        self.assertEqual(result.facility_type, "")
        self.assertEqual(result.mapping, {})

    def test_non_json_raises_valueerror(self):
        with self.assertRaises(ValueError):
            _parse("извините, не смог")


if __name__ == "__main__":
    unittest.main()
