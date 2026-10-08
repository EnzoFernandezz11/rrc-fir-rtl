"""Comprueba que el Gantt respete las dependencias del backlog."""

import re
import unittest
from datetime import date, timedelta

from scripts.validate_project import ROOT

TASK_ID = re.compile(r"[A-Z]\d\d")


def backlog_dependencies() -> dict[str, tuple[list[str], list[str]]]:
    deps = {}
    for line in (ROOT / "docs/backlog.md").read_text(encoding="utf-8").splitlines():
        match = re.match(r"\| \*\*\[([A-Z]\d\d) ", line)
        if match:
            cells = line.split(" | ")
            deps[match[1]] = (TASK_ID.findall(cells[2]), TASK_ID.findall(cells[3]))
    return deps


def gantt_schedule() -> dict[str, tuple[date, date]]:
    """Fechas (inicio, fin exclusivo) según la sintaxis Mermaid usada en docs/gantt.md."""
    text = (ROOT / "docs/gantt.md").read_text(encoding="utf-8")
    block = text.split("```mermaid", 1)[1].split("```", 1)[0]
    schedule = {}
    for task, start_spec, days in re.findall(r":(\w+), (.+?), (\d+)d$", block, re.M):
        if start_spec.startswith("after "):
            start = max(schedule[ref.upper()][1] for ref in start_spec.split()[1:])
        else:
            start = date.fromisoformat(start_spec)
        schedule[task.upper()] = (start, start + timedelta(days=int(days)))
    return schedule


class PlanChecks(unittest.TestCase):
    def test_gantt_respects_backlog_dependencies(self):
        deps = backlog_dependencies()
        schedule = gantt_schedule()
        self.assertEqual(len(deps), 24)
        self.assertEqual(deps.keys(), schedule.keys())
        for task, (to_start, to_close) in deps.items():
            start, end = schedule[task]
            for ref in to_start:
                self.assertLessEqual(schedule[ref][1], start, f"{task} empieza antes de que termine {ref}")
            for ref in to_close:
                self.assertLessEqual(schedule[ref][1], end, f"{task} termina antes que {ref}")


if __name__ == "__main__":
    unittest.main()
