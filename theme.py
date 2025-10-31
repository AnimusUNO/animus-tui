"""
Enhanced color palette for animaOS TUI
Multiple professional themes

Copyright (C) 2024 AnimusUNO
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class Palette:
    """Professional color palette for the TUI interface."""
    
    # Theme colors
    background: str = "#1e1e1e"
    surface: str = "#252526"
    surface_alt: str = "#2d2d30"
    
    # Text colors
    text_primary: str = "#cccccc"
    text_secondary: str = "#969696"
    
    # Accent colors
    accent: str = "#007acc"
    success: str = "#4ec9b0"
    warning: str = "#dcdcaa"
    error: str = "#f44747"
    
    # UI elements
    border: str = "#3e3e42"


# Available theme palettes
THEMES: Dict[str, Dict[str, str]] = {
    "vscode-dark": {
        "background": "#1e1e1e",
        "surface": "#252526",
        "surface_alt": "#2d2d30",
        "text_primary": "#cccccc",
        "text_secondary": "#969696",
        "accent": "#007acc",
        "success": "#4ec9b0",
        "warning": "#dcdcaa",
        "error": "#f44747",
        "border": "#3e3e42"
    },
    "vscode-light": {
        "background": "#ffffff",
        "surface": "#f3f3f3",
        "surface_alt": "#e8e8e8",
        "text_primary": "#1e1e1e",
        "text_secondary": "#616161",
        "accent": "#0066cc",
        "success": "#008000",
        "warning": "#b58900",
        "error": "#d73a49",
        "border": "#d1d1d1"
    },
    "nord": {
        "background": "#2e3440",
        "surface": "#3b4252",
        "surface_alt": "#434c5e",
        "text_primary": "#eceff4",
        "text_secondary": "#d8dee9",
        "accent": "#88c0d0",
        "success": "#a3be8c",
        "warning": "#ebcb8b",
        "error": "#bf616a",
        "border": "#4c566a"
    },
    "dracula": {
        "background": "#282a36",
        "surface": "#44475a",
        "surface_alt": "#6272a4",
        "text_primary": "#f8f8f2",
        "text_secondary": "#6272a4",
        "accent": "#bd93f9",
        "success": "#50fa7b",
        "warning": "#f1fa8c",
        "error": "#ff5555",
        "border": "#44475a"
    },
    "gruvbox-dark": {
        "background": "#282828",
        "surface": "#3c3836",
        "surface_alt": "#504945",
        "text_primary": "#ebdbb2",
        "text_secondary": "#a89984",
        "accent": "#458588",
        "success": "#b8bb26",
        "warning": "#fabd2f",
        "error": "#fb4934",
        "border": "#665c54"
    },
    "gruvbox-light": {
        "background": "#fbf1c7",
        "surface": "#f2e5bc",
        "surface_alt": "#ebdbb2",
        "text_primary": "#3c3836",
        "text_secondary": "#665c54",
        "accent": "#076678",
        "success": "#79740e",
        "warning": "#b57614",
        "error": "#9d0006",
        "border": "#d5c4a1"
    },
    "monokai": {
        "background": "#272822",
        "surface": "#3e3d32",
        "surface_alt": "#49483e",
        "text_primary": "#f8f8f2",
        "text_secondary": "#75715e",
        "accent": "#66d9ef",
        "success": "#a6e22e",
        "warning": "#e6db74",
        "error": "#f92672",
        "border": "#49483e"
    },
    "solarized-dark": {
        "background": "#002b36",
        "surface": "#073642",
        "surface_alt": "#586e75",
        "text_primary": "#839496",
        "text_secondary": "#586e75",
        "accent": "#268bd2",
        "success": "#859900",
        "warning": "#b58900",
        "error": "#dc322f",
        "border": "#073642"
    },
    "solarized-light": {
        "background": "#fdf6e3",
        "surface": "#eee8d5",
        "surface_alt": "#93a1a1",
        "text_primary": "#657b83",
        "text_secondary": "#93a1a1",
        "accent": "#268bd2",
        "success": "#859900",
        "warning": "#b58900",
        "error": "#dc322f",
        "border": "#eee8d5"
    },
    "tokyo-night": {
        "background": "#1a1b26",
        "surface": "#24283b",
        "surface_alt": "#414868",
        "text_primary": "#c0caf5",
        "text_secondary": "#565f89",
        "accent": "#7aa2f7",
        "success": "#9ece6a",
        "warning": "#e0af68",
        "error": "#f7768e",
        "border": "#414868"
    },
    "catppuccin-mocha": {
        "background": "#1e1e2e",
        "surface": "#313244",
        "surface_alt": "#45475a",
        "text_primary": "#cdd6f4",
        "text_secondary": "#bac2de",
        "accent": "#89b4fa",
        "success": "#a6e3a1",
        "warning": "#f9e2af",
        "error": "#f38ba8",
        "border": "#45475a"
    }
}

# Global palette instance
_palette = Palette()
_current_theme = "vscode-dark"
_dark_mode = True

def get_palette() -> Palette:
    """Get the current palette based on selected theme."""
    global _palette, _current_theme
    
    # Get theme colors
    theme_colors = THEMES.get(_current_theme, THEMES["vscode-dark"])
    
    # Apply to palette
    for key, value in theme_colors.items():
        setattr(_palette, key, value)
    
    return _palette

def set_theme(theme_name: str) -> None:
    """Set the active theme by name."""
    global _current_theme, _dark_mode
    if theme_name in THEMES:
        _current_theme = theme_name
        # Update dark mode based on theme name
        _dark_mode = "light" not in theme_name.lower()
    
def get_available_themes() -> list:
    """Get list of available theme names."""
    return list(THEMES.keys())

def get_current_theme() -> str:
    """Get the current theme name."""
    return _current_theme

def set_dark_mode(dark: bool) -> None:
    """Set the dark/light mode for the palette."""
    global _dark_mode, _current_theme
    _dark_mode = dark
    # Switch to appropriate variant if available
    if dark and _current_theme.endswith("-light"):
        base = _current_theme.replace("-light", "-dark")
        if base in THEMES:
            _current_theme = base
    elif not dark and _current_theme.endswith("-dark"):
        base = _current_theme.replace("-dark", "-light")
        if base in THEMES:
            _current_theme = base
    elif not dark and "light" not in _current_theme:
        # Default to vscode-light if no light variant
        if "vscode-light" in THEMES:
            _current_theme = "vscode-light"

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