"""Демо-кейс целиком: пример CSV → оффлайн-endpoint → оба расчётных модуля.

Проверяет, что заготовленный demo_facilities.csv проходит весь конвейер импорта и
для каждого объекта получаются ожидаемые статусы ремонта (модуль 6) и заполняется
период осмотра (модуль 5), а дубль/конфликт отрабатывают как задумано (ADR-0004).

Требует тестовой БД PostGIS (как и test_import_endpoint).
"""

import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

_SAMPLE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "demo", "sample_data", "demo_facilities.csv",
)


class DemoSampleTests(TestCase):
    def _run(self):
        with open(_SAMPLE, "rb") as handle:
            upload = SimpleUploadedFile("demo_facilities.csv", handle.read())
        response = Client().post("/demo/import/run/", {"file": upload})
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_demo_cases_produce_expected_verdicts(self):
        body = self._run()

        # 5 уникальных объектов создаются, 1 дубль пропущен, 1 конфликт не записан.
        self.assertEqual(body["created"], 5)
        self.assertEqual(body["skipped_duplicates"], 1)
        self.assertEqual(len(body["conflicts"]), 2)  # wear + technical_condition
        self.assertEqual(body["unmapped_columns"], [])

        by_name = {f["name"]: f for f in body["facilities"]}

        # Тип объекта берётся из колонки «Тип объекта» (per-row, ADR-0004).
        self.assertEqual(by_name["Канал Магистральный-1"]["facility_type"], "canal")
        self.assertEqual(by_name["Шлюз Степной-2"]["facility_type"], "sluice")
        self.assertEqual(by_name["Насосная Прибрежная-3"]["facility_type"], "pumping")
        self.assertEqual(by_name["Плотина Озёрная-4"]["facility_type"], "dam_dyke")
        self.assertEqual(by_name["Водозабор Северный-7"]["facility_type"], "intake")

        # Модуль 6 — статусы ремонта по findings:
        self.assertEqual(by_name["Канал Магистральный-1"]["repair_status"], "critical")
        self.assertEqual(by_name["Шлюз Степной-2"]["repair_status"], "repair_required")
        self.assertEqual(by_name["Насосная Прибрежная-3"]["repair_status"], "inspection_required")
        self.assertEqual(by_name["Плотина Озёрная-4"]["repair_status"], "normal")
        self.assertEqual(by_name["Водозабор Северный-7"]["repair_status"], "normal")

        # Координаты — в пределах заданного бокса (52.27–52.32, 76.83–76.88).
        for f in body["facilities"]:
            lat = float(f["loaded"]["latitude"])
            lon = float(f["loaded"]["longitude"])
            self.assertTrue(52.27 <= lat <= 52.32, lat)
            self.assertTrue(76.83 <= lon <= 76.88, lon)

        # Критическое пришло через эскалацию напорного фронта на фильтрации.
        crit_reasons = by_name["Канал Магистральный-1"]["repair_reasons"]
        self.assertTrue(any(r.get("pressure_front_escalation") for r in crit_reasons))

        # Объект без осмотра требует первичного осмотра и проверки.
        intake = by_name["Водозабор Северный-7"]
        self.assertTrue(intake["needs_first_inspection"])
        self.assertTrue(intake["requires_verification"])
        self.assertFalse(intake["has_inspection"])

        # Модуль 5 — у всех заполнен период осмотра и разбивка коэффициентов.
        for f in body["facilities"]:
            self.assertGreaterEqual(f["inspection_interval_days"], 30)
            self.assertIsNotNone(f["next_inspection_date"])
            self.assertIn("factors", f["inspection_factors"])

        # У деградирующего объекта I класса коэффициенты износа/состояния > 1.
        mag_factors = by_name["Канал Магистральный-1"]["inspection_factors"]["factors"]
        self.assertGreater(mag_factors["k_wear"], 1.0)
        self.assertGreater(mag_factors["k_condition"], 1.0)
