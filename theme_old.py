"""
Enhanced color palette for animaOS TUI
VS Code-inspired professional theme

Copyright (C) 2024 AnimusUNO
"""
from dataclasses import dataclass


@dataclass
class Palette:
    """Professional color palette for the TUI interface."""
    
    # VS Code-inspired dark theme colors
    background: str = "#1e1e1e"      # Dark background
    surface: str = "#252526"         # Input fields, panels
    surface_alt: str = "#2d2d30"     # Alternative surface
    
    # Text colors
    text_primary: str = "#cccccc"    # Primary text
    text_secondary: str = "#969696"  # Secondary text, timestamps
    
    # Accent colors
    accent: str = "#007acc"          # VS Code blue
    success: str = "#4ec9b0"         # Success messages
    warning: str = "#dcdcaa"         # Warnings
    error: str = "#f44747"           # Errors
    
    # UI elements
    border: str = "#3e3e42"          # Borders, separators


# Global palette instance
_palette = Palette()

def get_palette() -> Palette:
    """Get the current palette."""
    return _palette

def set_theme_colors(background: str = None, accent: str = None, **kwargs) -> None:
    """Update theme colors dynamically."""
    global _palette
    if background:
        _palette.background = background
    if accent:
        _palette.accent = accent
    
    # Update any other provided colors
    for key, value in kwargs.items():
        if hasattr(_palette, key):
            setattr(_palette, key, value)