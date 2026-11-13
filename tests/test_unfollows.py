import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import unfollows  # noqa: E402
from unfollows import Account  # noqa: E402

SAMPLE = ROOT / "sample"


def entry(value=None, title="", href=None, timestamp=0):
    data = {"timestamp": timestamp}
    if value is not None:
        data["value"] = value
    if href is not None:
        data["href"] = href
    return {"title": title, "string_list_data": [data]}


class ExtractAccountsTest(unittest.TestCase):
    def test_old_followers_shape(self):
        data = [entry(value="alice", href="https://www.instagram.com/alice", timestamp=5)]
        self.assertEqual(unfollows.extract_accounts(data), [Account("alice", 5)])

    def test_new_following_shape_uses_title(self):
        data = {"relationships_following": [entry(title="bob", href="https://www.instagram.com/_u/bob")]}
        self.assertEqual(unfollows.extract_accounts(data), [Account("bob")])

    def test_falls_back_to_href(self):
        data = [entry(href="https://www.instagram.com/_u/carol?igsh=x")]
        self.assertEqual(unfollows.extract_accounts(data), [Account("carol")])

    def test_skips_garbage(self):
        data = [None, 3, {"string_list_data": []}, entry()]
        self.assertEqual(unfollows.extract_accounts(data), [])

    def test_unknown_shape_is_empty(self):
        self.assertEqual(unfollows.extract_accounts("nope"), [])


class CompareTest(unittest.TestCase):
    def test_not_following_back_is_case_insensitive_and_deduped(self):
        followers = [Account("Alice")]
        following = [Account("alice"), Account("Bob"), Account("bob")]
        self.assertEqual(unfollows.not_following_back(followers, following), [Account("Bob")])

    def test_sort_modes(self):
        people = [Account("b", 2), Account("a", 1), Account("c", 3)]
        names = lambda mode: [a.username for a in unfollows.sort_accounts(people, mode)]
        self.assertEqual(names("recent"), ["c", "b", "a"])
        self.assertEqual(names("oldest"), ["a", "b", "c"])
        self.assertEqual(names("az"), ["a", "b", "c"])
        with self.assertRaises(ValueError):
            unfollows.sort_accounts(people, "nope")

    def test_sample_files(self):
        followers = json.loads((SAMPLE / "followers_1.json").read_text())
        following = json.loads((SAMPLE / "following.json").read_text())
        result = unfollows.compare([followers], [following])
        self.assertEqual(result["followers"], 3)
        self.assertEqual(result["following"], 5)
        self.assertEqual(
            [p["username"] for p in result["not_following_back"]],
            ["coffee.daily", "mira.designs", "nasa"],
        )

    def test_empty_files_raise(self):
        with self.assertRaises(ValueError):
            unfollows.compare([[]], [[entry(value="x")]])
        with self.assertRaises(ValueError):
            unfollows.compare([[entry(value="x")]], [{}])


class CompareJsonTest(unittest.TestCase):
    def test_round_trip(self):
        files = lambda name: json.dumps([{"name": name, "text": (SAMPLE / name).read_text()}])
        out = json.loads(unfollows.compare_json(files("followers_1.json"), files("following.json"), "az"))
        self.assertEqual(len(out["not_following_back"]), 3)

    def test_invalid_json_message(self):
        bad = json.dumps([{"name": "broken.json", "text": "{"}])
        with self.assertRaisesRegex(ValueError, "broken.json"):
            unfollows.compare_json(bad, bad)


class CliTest(unittest.TestCase):
    def test_cli_json(self):
        import contextlib
        import io

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = unfollows.main([str(SAMPLE / "followers_1.json"), str(SAMPLE / "following.json"), "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(buf.getvalue())["not_following_back"]), 3)


if __name__ == "__main__":
    unittest.main()
