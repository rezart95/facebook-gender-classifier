"""Options of the faithful extraction.

The defaults reproduce the 2019 data (12-month window, correct weekday labels), as chosen by
the golden check.
"""

from __future__ import annotations

from dataclasses import dataclass

from fbgc_pipeline.features.faithful.rhythms import WeekdayLabels
from fbgc_pipeline.window.observation import WindowPolicy


@dataclass(frozen=True)
class FaithfulOptions:
    window: WindowPolicy = WindowPolicy.LAST_12_MONTHS
    weekday_labels: WeekdayLabels = WeekdayLabels.CORRECT

    @property
    def label(self) -> str:
        return f"{self.window.value}_{self.weekday_labels.value}"
