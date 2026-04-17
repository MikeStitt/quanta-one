from abc import ABC, abstractmethod
from typing import Any

import matplotlib
matplotlib.use("Agg")  # non-interactive backend; safe for tests and headless environments
import matplotlib.pyplot as plt

from quanta_analysis.analyzer import AnalysisResult


class Plot(ABC):
    """
    Base class for all quanta plots.

    Subclasses implement ``render()`` to produce a matplotlib Figure.

    Testing strategy: call ``get_data()`` to assert on the underlying arrays without
    inspecting rendered images.
    """

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def get_data(self) -> dict[str, Any]:
        """
        Returns the data that was fed to matplotlib on the last ``render()`` call.
        Use this in tests instead of inspecting images.
        """
        return self._data

    @abstractmethod
    def render(self, result: AnalysisResult) -> plt.Figure:
        """
        Render the AnalysisResult to a matplotlib Figure.

        Implementations must populate ``self._data`` with the arrays passed to the
        plot so that ``get_data()`` can be used for assertions in tests.

        :param result: The AnalysisResult to visualize.
        :return: A matplotlib Figure.
        """
        ...
