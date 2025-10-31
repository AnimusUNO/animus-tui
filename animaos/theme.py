"""Theme definitions for animaOS TUI."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    """VS Code inspired dark palette."""

    background: str = "#1e1e1e"
    surface: str = "#252526"
    surface_alt: str = "#2d2d30"
    text_primary: str = "#cccccc"
    text_secondary: str = "#858585"
    accent: str = "#007acc"
    border: str = "#3e3e42"
    success: str = "#4ec9b0"
    warning: str = "#dcdcaa"


palette = Palette()

