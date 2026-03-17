"""
app/services/trace_service.py
Pure-logic service for trace JSON analysis.

No UI or framework dependencies — all methods deal only with plain
Python data structures so they can be tested independently of the GUI.
"""

import json
import re


class TraceService:
    """Business-logic layer for loading, filtering, and formatting trace data.

    Designed to be instantiated once per UI frame and reused across
    interactions.  All methods are stateless (no instance variables are
    modified between calls).
    """

    # ── Loading ──────────────────────────────────────────────────────────────

    def load_events(self, file_path: str) -> list[dict]:
        """Load and validate a trace JSON file.

        Args:
            file_path: Absolute or relative path to the ``.json`` file.

        Returns:
            A list of event dicts.

        Raises:
            json.JSONDecodeError: The file is not valid JSON.
            ValueError:           The JSON does not contain a non-empty
                                  list of dicts.
            OSError:              The file could not be opened.
        """
        with open(file_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        if (
            not isinstance(data, list)
            or not data
            or not all(isinstance(ev, dict) for ev in data)
        ):
            raise ValueError(
                "O JSON deve conter uma lista de eventos não vazia "
                "(cada elemento deve ser um objeto JSON)."
            )
        return data

    # ── Filtering ────────────────────────────────────────────────────────────

    def apply_filters(
        self,
        events: list[dict],
        filter_text: str = "",
        field: str = "selecionar",
        errors_only: bool = False,
    ) -> list[dict]:
        """Return a filtered subset of *events*.

        Filtering strategy:
        1. If *errors_only* is ``True``, only events that have a non-empty
           ``errorText`` are kept.
        2. If *field* is not ``"selecionar"`` and *filter_text* is not
           blank, events are kept only when the value of *field* contains
           *filter_text* (case-insensitive substring match).
        3. If *field* IS ``"selecionar"`` and *filter_text* is not blank,
           the search is performed across **all fields** (free-text search).

        Args:
            events:      List of event dicts.
            filter_text: Substring to look for.
            field:       Specific field name to search, or ``"selecionar"``
                         for all-fields search.
            errors_only: When ``True`` only return events with errors.

        Returns:
            Filtered list (may be empty; does not mutate the input).
        """
        q = (filter_text or "").strip().lower()
        result: list[dict] = []

        for ev in events:
            # 1 ── error filter
            if errors_only and not ev.get("errorText", ""):
                continue

            # 2 ── field-specific search
            if field != "selecionar" and q:
                field_val = str(ev.get(field, "")).strip().lower()
                if q not in field_val:
                    continue

            # 3 ── full-text search (when no specific field is chosen)
            elif field == "selecionar" and q:
                if not any(q in str(v).lower() for v in ev.values()):
                    continue

            result.append(ev)

        return result

    def get_slowest_event(self, events: list[dict]) -> dict | None:
        """Return the event with the highest ``execution`` value.

        Args:
            events: List of event dicts.

        Returns:
            The slowest event dict, or ``None`` if *events* is empty.
        """
        if not events:
            return None
        return max(events, key=lambda ev: ev.get("execution", 0))

    def get_field_names(self, events: list[dict]) -> list[str]:
        """Collect the union of all keys across *events*, sorted.

        Useful for populating a field-selector combo box.

        Returns:
            Sorted list of unique key strings.
        """
        keys: set[str] = set()
        for ev in events:
            keys.update(ev.keys())
        return sorted(keys)

    # ── SQL formatting ────────────────────────────────────────────────────────

    def format_sql(self, sql: str, params: list | None = None) -> str:
        """Return a formatted SQL string with parameters substituted.

        Args:
            sql:    Raw SQL string (may contain ``:PARAM`` placeholders).
            params: List of parameter dicts from the trace event, each
                    expected to have ``name``, and either ``outValue`` or
                    ``value`` keys.

        Returns:
            Formatted, human-readable SQL string.  Returns ``""`` if *sql*
            is blank.
        """
        if not sql:
            return ""
        substituted = self._substitute_params(sql, params or [])
        return self._pretty_sql(substituted)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _substitute_params(self, sql: str, params: list) -> str:
        """Replace ``:NAME`` placeholders with quoted values from *params*."""
        original = sql

        param_map: dict[str, object] = {}
        for p in params:
            name = str(p.get("name", "")).lstrip(":")
            value = p.get("outValue", p.get("value", None))
            if name:
                param_map[name] = value

        placeholder_re = re.compile(r":([A-Za-z_][\w$]*)")

        def _format_value(v) -> str:
            if v is None:
                return "NULL"
            if isinstance(v, str):
                s = v.strip()
                if s.upper() in {"NULL", "<NULL>"}:
                    return "NULL"
                # Already quoted by the trace exporter → return as-is
                if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
                    return s
                # Numeric → no quotes
                try:
                    float(s)
                    return s
                except ValueError:
                    pass
                return "'" + s.replace("'", "''") + "'"
            if isinstance(v, (int, float)):
                return str(v)
            return "'" + str(v).replace("'", "''") + "'"

        def _replace(m: re.Match) -> str:
            key = m.group(1)
            val = param_map.get(key)
            if val is None:
                # Case-insensitive fallback
                for k, v in param_map.items():
                    if k.lower() == key.lower():
                        val = v
                        break

            if val is None and key not in param_map:
                return m.group(0)  # no mapping → keep placeholder

            formatted = _format_value(val)

            # Avoid double-quoting when the placeholder already sits between
            # single quotes in the original SQL.
            start, end = m.start(), m.end()
            left  = original[start - 1] if start - 1 >= 0 else ""
            right = original[end]       if end < len(original) else ""
            if (
                left == "'"
                and right == "'"
                and formatted.startswith("'")
                and formatted.endswith("'")
            ):
                return formatted[1:-1]

            return formatted

        return placeholder_re.sub(_replace, original)

    def _pretty_sql(self, sql: str) -> str:
        """Add newlines before major SQL clauses and indent AND/OR."""
        s = sql.strip()
        s = re.sub(r"[ \t]+", " ", s)

        # Keywords that deserve their own line (longest first to avoid
        # partial matches — e.g. "LEFT JOIN" before "JOIN").
        clause_keywords = [
            "SELECT", "FROM", "WHERE",
            "GROUP BY", "HAVING", "ORDER BY",
            "UNION ALL", "UNION", "EXCEPT", "INTERSECT",
            "LEFT JOIN", "RIGHT JOIN", "FULL JOIN",
            "INNER JOIN", "OUTER JOIN", "JOIN",
            "UPDATE", "SET", "INSERT INTO", "VALUES",
            "DELETE FROM", "ON",
        ]
        for kw in sorted(clause_keywords, key=len, reverse=True):
            s = re.sub(
                r"(?i)\b" + kw + r"\b",
                lambda m: "\n" + m.group(0).upper(),
                s,
            )

        s = re.sub(r"(?i)\bAND\b", lambda _m: "\n  AND", s)
        s = re.sub(r"(?i)\bOR\b",  lambda _m: "\n  OR",  s)

        s = s.lstrip()
        s = re.sub(r"\n{2,}", "\n", s)
        return s
