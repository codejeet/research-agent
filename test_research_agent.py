import json
import os
import tempfile
import unittest
from unittest import mock

import research_agent


def make_result(title):
    return {
        "title": title,
        "url": f"https://example.com/{title.lower()}",
        "description": f"{title} description",
    }


class SaveSearchDataTests(unittest.TestCase):
    def test_normalize_search_data_includes_all_expected_keys(self):
        normalized = research_agent.normalize_search_data(
            {"market_size": [make_result("Market")], "statistics": [make_result("Stat")]}
        )

        self.assertEqual(list(normalized.keys()), list(research_agent.SEARCH_DATA_KEYS))
        self.assertEqual(normalized["market_size"], [make_result("Market")])
        self.assertEqual(normalized["trends"], [])
        self.assertEqual(normalized["competitors"], [])
        self.assertEqual(normalized["statistics"], [make_result("Stat")])

    def test_save_search_data_writes_pretty_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "search-data.json")

            research_agent.save_search_data(output_path, {"trends": [make_result("Trend")]})

            with open(output_path, encoding="utf-8") as f:
                content = f.read()

            self.assertIn('\n  "market_size": []', content)
            self.assertTrue(content.endswith("\n"))

            payload = json.loads(content)
            self.assertEqual(list(payload.keys()), list(research_agent.SEARCH_DATA_KEYS))
            self.assertEqual(payload["trends"], [make_result("Trend")])


class MainTests(unittest.TestCase):
    @mock.patch.dict(os.environ, {"BRAVE_API_KEY": "test-api-key"}, clear=True)
    @mock.patch("research_agent.call_llm", return_value="# Research Brief: Acme")
    @mock.patch("research_agent.brave_search")
    def test_main_saves_json_with_all_expected_keys(self, mock_brave_search, _mock_call_llm):
        mock_brave_search.side_effect = [
            [make_result("Market")],
            [make_result("Trend")],
            [make_result("Competitor")],
            [make_result("Stat")],
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "search-data.json")
            output_path = os.path.join(tmpdir, "brief.md")
            argv = [
                "research_agent.py",
                "--company",
                "Acme",
                "--industry",
                "cloud computing",
                "--audience",
                "enterprise CTOs",
                "--save-search-json",
                json_path,
                "--output",
                output_path,
            ]

            with mock.patch("sys.argv", argv):
                research_agent.main()

            with open(json_path, encoding="utf-8") as f:
                payload = json.load(f)

            self.assertEqual(list(payload.keys()), list(research_agent.SEARCH_DATA_KEYS))
            self.assertEqual(payload["market_size"], [make_result("Market")])
            self.assertEqual(payload["trends"], [make_result("Trend")])
            self.assertEqual(payload["competitors"], [make_result("Competitor")])
            self.assertEqual(payload["statistics"], [make_result("Stat")])

            with open(output_path, encoding="utf-8") as f:
                self.assertEqual(f.read(), "# Research Brief: Acme")


if __name__ == "__main__":
    unittest.main()
