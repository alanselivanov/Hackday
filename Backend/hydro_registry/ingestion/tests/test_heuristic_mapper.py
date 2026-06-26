"""Чистые тесты оффлайн-маппера по ключевым словам — без Django/сети."""

import unittest

from ingestion.domain.types import ColumnSample
from ingestion.infrastructure.llm.heuristic_mapper import HeuristicSchemaMapper


def _cols(*names):
    return [ColumnSample(i, n) for i, n in enumerate(names)]


class HeuristicMapperTests(unittest.TestCase):
    def test_detects_canal_and_maps_columns(self):
        columns = _cols(
            "Наименование каналов", "Водоисточник", "Год ввода в эксплуатацию",
            "Пропускная способность, м3/с", "из них / землян., км", "Широта", "Долгота",
        )
        result = HeuristicSchemaMapper().map(facility_hint="каналы", columns=columns)

        self.assertEqual(result.facility_type, "canal")
        self.assertEqual(result.mapping[0], "name")
        self.assertEqual(result.mapping[1], "water_source")
        self.assertEqual(result.mapping[2], "year_built")
        self.assertEqual(result.mapping[3], "capacity")
        self.assertEqual(result.mapping[4], "earth_length")
        self.assertEqual(result.mapping[5], "latitude")
        self.assertEqual(result.mapping[6], "longitude")

    def test_detects_sluice_type_and_specific_fields(self):
        columns = _cols("Наименование", "Тип затвора", "Количество затворов", "Привод затвора")
        result = HeuristicSchemaMapper().map(facility_hint="Шлюзы филиала", columns=columns)

        self.assertEqual(result.facility_type, "sluice")
        self.assertEqual(result.mapping[1], "gate_type")
        self.assertEqual(result.mapping[2], "gates_count")
        self.assertEqual(result.mapping[3], "drive_type")

    def test_subclass_field_not_assigned_for_wrong_type(self):
        # Для канала поле «затворы» (шлюзовое) не должно маппиться.
        columns = _cols("Наименование", "Количество затворов")
        result = HeuristicSchemaMapper().map(facility_hint="каналы", columns=columns)

        self.assertEqual(result.facility_type, "canal")
        self.assertNotIn(1, result.mapping)


if __name__ == "__main__":
    unittest.main()
