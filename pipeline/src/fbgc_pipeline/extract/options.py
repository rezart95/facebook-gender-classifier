"""Options of the faithful extraction. The golden test decides the defaults (Task 20)."""

from __future__ import annotations

from dataclasses import dataclass

from fbgc_pipeline.features.faithful.rhythms import WeekdayLabels
from fbgc_pipeline.window.observation import WindowPolicy


@dataclass(frozen=True)
class FaithfulOptions:
    window: WindowPolicy = WindowPolicy.LAST_6_MONTHS
    weekday_labels: WeekdayLabels = WeekdayLabels.CORRECT

    @property
    def label(self) -> str:
        return f"{self.window.value}_{self.weekday_labels.value}"
