"""
app/ui/theme.py
Design tokens for Pytegrator — strongly inspired by Linear's dark interface.
Tuples follow CTk convention: (light_value, dark_value).

Usage:
    from app.ui.theme import COLOR_BG, COLOR_ACCENT, SPACE_LG, c
    frame.configure(fg_color=COLOR_SURFACE)   # pass tuple directly to CTk
    frame.configure(fg_color=c(COLOR_SURFACE))  # or resolve to current string
"""

# ── Background & Surface ────────────────────────────────────────────────────
#                                  light          dark
COLOR_BG          = ("#F8F9FA",  "#0F1115")   # Root window / page background
COLOR_SURFACE     = ("#FFFFFF",  "#151922")   # Card / panel surface
COLOR_SURFACE_ALT = ("#F1F3F5",  "#0F1115")   # Alternate depth (softer)
COLOR_HOVER       = ("#E9ECEF",  "#1D2330")   # Row / item hover state
COLOR_BORDER      = ("#DEE2E6",  "#2A2F3A")   # Dividers and card edges

# ── Text ────────────────────────────────────────────────────────────────────
COLOR_TEXT        = ("#0D1117",  "#E2E8F0")   # Primary text
COLOR_TEXT_MUTED  = ("#6B7280",  "#8892A4")   # Secondary / hint text
COLOR_TEXT_FAINT  = ("#9CA3AF",  "#4B5563")   # Disabled / label hint

# ── Accent & Semantic ───────────────────────────────────────────────────────
COLOR_ACCENT      = ("#3B82F6",  "#3B82F6")   # Primary blue (Linear accent)
COLOR_ACCENT_HOVER= ("#2563EB",  "#2563EB")   # Accent hover state
COLOR_SUCCESS     = ("#10B981",  "#10B981")   # Green — success / ok
COLOR_WARNING     = ("#F59E0B",  "#F59E0B")   # Amber — warning
COLOR_ERROR       = ("#EF4444",  "#EF4444")   # Red — error / critical
COLOR_PRIMARY     = COLOR_ACCENT              # Alias

# ── Sidebar ─────────────────────────────────────────────────────────────────
#                                  light          dark
SIDEBAR_BG        = ("#FFFFFF",  "#111418")   # Sidebar background
SIDEBAR_HOVER     = ("#F1F3F5",  "#1A1F2B")   # Nav item hover
SIDEBAR_ACTIVE    = ("#E7F0FE",  "#1D2535")   # Nav item selected (active)
SIDEBAR_WIDTH     = 220                       # Fixed pixel width

# ── Spacing (px) ────────────────────────────────────────────────────────────
SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 20
SPACE_XL = 32

# ── Corner Radius (px) ──────────────────────────────────────────────────────
RADIUS_SM = 4
RADIUS_MD = 8
RADIUS_LG = 12

# ── Font Sizes (pt) ─────────────────────────────────────────────────────────
FONT_XS  = 10
FONT_SM  = 11
FONT_MD  = 13
FONT_LG  = 15
FONT_XL  = 18
FONT_2XL = 22


# ── Helper ──────────────────────────────────────────────────────────────────
def c(color) -> str:
    """Resolve a CTk color tuple to a plain hex string respecting current mode.

    CTk stores colors as (light_value, dark_value) tuples.
    We inspect the current appearance mode to pick the right index.

    Args:
        color: Either a ``(str, str)`` tuple or a plain ``str``.

    Returns:
        The resolved hex string.
    """
    import customtkinter as ctk
    if isinstance(color, tuple):
        return color[0] if ctk.get_appearance_mode() == "Light" else color[1]
    return color
