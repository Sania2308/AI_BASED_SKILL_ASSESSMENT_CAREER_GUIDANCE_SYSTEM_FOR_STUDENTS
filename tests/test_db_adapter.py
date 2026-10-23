import unittest
import re

def translate_query_for_postgres(sql: str) -> str:
    """Translates SQLite-style queries with '?' placeholders to PostgreSQL '%s' placeholders,
    preserving '?' inside string literals."""
    tokens = []
    in_single_quote = False
    in_double_quote = False
    i = 0
    n = len(sql)
    while i < n:
        c = sql[i]
        if c == "'" and not in_double_quote:
            if i + 1 < n and sql[i+1] == "'":
                tokens.append("''")
                i += 2
                continue
            in_single_quote = not in_single_quote
            tokens.append(c)
        elif c == '"' and not in_single_quote:
            if i + 1 < n and sql[i+1] == '"':
                tokens.append('""')
                i += 2
                continue
            in_double_quote = not in_double_quote
            tokens.append(c)
        elif c == '?' and not in_single_quote and not in_double_quote:
            tokens.append('%s')
        else:
            tokens.append(c)
        i += 1
    return "".join(tokens)


class PostgresRow(dict):
    """Row object that acts as a dict and a sequence, matching sqlite3.Row."""
    def __init__(self, cols, vals):
        super().__init__(zip(cols, vals))
        self._vals = list(vals)
        self._cols = list(cols)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._vals[item]
        return super().__getitem__(item)

    def keys(self):
        return self._cols


class TestDBAdapter(unittest.TestCase):
    def test_query_translation(self):
        q1 = "SELECT * FROM users WHERE id = ? AND email = ?"
        self.assertEqual(translate_query_for_postgres(q1), "SELECT * FROM users WHERE id = %s AND email = %s")

        q2 = "SELECT * FROM feedback WHERE note = 'Is this working?' AND status = ?"
        self.assertEqual(translate_query_for_postgres(q2), "SELECT * FROM feedback WHERE note = 'Is this working?' AND status = %s")

    def test_row_compatibility(self):
        cols = ["id", "name", "email", "points"]
        vals = [101, "Test User", "test@domain.com", 50]
        row = PostgresRow(cols, vals)

        self.assertEqual(row[0], 101)
        self.assertEqual(row[1], "Test User")
        self.assertEqual(row["id"], 101)
        self.assertEqual(row["name"], "Test User")
        self.assertEqual(row["email"], "test@domain.com")
        self.assertEqual(row.get("points"), 50)
        self.assertEqual(row.get("nonexistent", "default"), "default")
        self.assertEqual(dict(row), {"id": 101, "name": "Test User", "email": "test@domain.com", "points": 50})
        self.assertEqual(list(row.keys()), cols)

if __name__ == "__main__":
    unittest.main()
