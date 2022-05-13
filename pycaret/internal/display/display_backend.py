from abc import ABC, abstractmethod
from pprint import pprint
from typing import Any, Optional

import pandas as pd
from IPython import get_ipython
from IPython.display import HTML, DisplayHandle, clear_output, display
from pandas.io.formats.style import Styler


class DisplayBackend(ABC):
    id: str
    can_update: bool

    @abstractmethod
    def display(self, obj: Any) -> None:
        """Display obj."""
        pass

    @abstractmethod
    def clear_display(self) -> None:
        """Clear current display (not entire cell)."""
        pass

    @abstractmethod
    def clear_output(self) -> None:
        """Clear entire cell."""
        pass


class SilentBackend(DisplayBackend):
    id: str = "silent"
    can_update: bool = False

    def display(self, obj: Any) -> None:
        pass

    def clear_display(self) -> None:
        pass

    def clear_output(self) -> None:
        pass


class CLIBackend(DisplayBackend):
    id: str = "cli"
    can_update: bool = False

    def display(self, obj: Any) -> None:
        obj = self._handle_input(obj)
        if obj is not None:
            if hasattr(obj, "show"):
                obj.show()
                return
            pprint(obj)

    def clear_display(self) -> None:
        pass

    def clear_output(self) -> None:
        pass

    def _handle_input(self, obj: Any) -> Any:
        if isinstance(obj, Styler):
            obj = obj.data
        if isinstance(obj, (pd.Series, pd.DataFrame)) and obj.empty:
            return None
        return obj


class JupyterBackend(DisplayBackend):
    id: str = "jupyter"
    can_update: bool = True

    def __init__(self) -> None:
        self._display_ref: Optional[DisplayHandle] = None

    def display(self, obj: Any) -> None:
        if not self._display_ref:
            self._display_ref = display(display_id=True)
        obj = self._handle_input(obj)
        if obj is not None:
            self._display_ref.update(obj)

    def clear_display(self) -> None:
        if self._display_ref:
            self._display_ref.update()

    def clear_output(self) -> None:
        clear_output(wait=True)

    def _handle_input(self, obj: Any) -> Any:
        return obj


class ColabBackend(JupyterBackend):
    id: str = "colab"

    def _handle_input(self, obj: Any) -> Any:
        if isinstance(obj, Styler):
            return HTML(obj.to_html())
        return obj


backends = [CLIBackend, JupyterBackend, ColabBackend, SilentBackend]
backends = {b.id: b for b in backends}


def detect_backend(backend) -> DisplayBackend:
    if backend is None:
        class_name = ""
        try:
            ipython = get_ipython()
            assert ipython
            class_name = ipython.__class__.__name__
            is_notebook = True if "Terminal" not in class_name else False
        except Exception:
            is_notebook = False

        if not is_notebook:
            return CLIBackend()
        if "google.colab" in class_name:
            return ColabBackend()
        return JupyterBackend()

    if isinstance(backend, str):
        backend_id = backend.lower()
        backend = backends.get(backend_id, None)
        if not backend:
            raise ValueError(
                f"Wrong backend id. Got {backend_id}, expected one of {list(backends.keys())}."
            )
        return backend()

    if isinstance(backend, DisplayBackend):
        return backend

    raise TypeError(
        f"Wrong backend type. Expected None, str or DisplayBackend, got {type(backend)}."
    )
