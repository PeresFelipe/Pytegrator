"""
app/ui/theme.py
Design tokens for Pytegrator — strongly inspired by Linear's dark interface.

Usage:
    from app.ui.theme import COLOR_BG, COLOR_ACCENT, SPACE_LG, c
    frame.configure(fg_color=c(COLOR_SURFACE))
"""

# ── Background & Surface ────────────────────────────────────────────────────
COLOR_BG          = ("#0F1115", "#0F1115")   # Root window / page background
COLOR_SURFACE     = ("#151922", "#151922")   # Card / panel surface
COLOR_SURFACE_ALT = ("#0F1115", "#0F1115")   # Alternate depth (softer)
COLOR_HOVER       = ("#1D2330", "#1D2330")   # Row / item hover state
COLOR_BORDER      = ("#2A2F3A", "#2A2F3A")   # Dividers and card edges

# ── Text ────────────────────────────────────────────────────────────────────
COLOR_TEXT        = ("#E2E8F0", "#E2E8F0")   # Primary text
COLOR_TEXT_MUTED  = ("#8892A4", "#8892A4")   # Secondary / hint text
COLOR_TEXT_FAINT  = ("#4B5563", "#4B5563")   # Disabled / label hint

# ── Accent & Semantic ───────────────────────────────────────────────────────
COLOR_ACCENT      = ("#3B82F6", "#3B82F6")   # Primary blue (Linear accent)
COLOR_ACCENT_HOVER= ("#2563EB", "#2563EB")   # Accent hover state
COLOR_SUCCESS     = ("#10B981", "#10B981")   # Green — success / ok
COLOR_WARNING     = ("#F59E0B", "#F59E0B")   # Amber — warning
COLOR_ERROR       = ("#EF4444", "#EF4444")   # Red — error / critical
COLOR_PRIMARY     = COLOR_ACCENT             # Alias

# ── Sidebar ─────────────────────────────────────────────────────────────────
SIDEBAR_BG        = ("#111418", "#111418")   # Sidebar background (darkest)
SIDEBAR_HOVER     = ("#1A1F2B", "#1A1F2B")   # Nav item hover
SIDEBAR_ACTIVE    = ("#1D2535", "#1D2535")   # Nav item selected (active)
SIDEBAR_WIDTH     = 220                      # Fixed pixel width

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
    """Resolve a CTk color tuple to a plain hex string (light/dark aware).

    CTk stores colors as (light_value, dark_value) tuples.
    In dark mode we always use index 0 (dark theme default).

    Args:
        color: Either a ``(str, str)`` tuple or a plain ``str``.

    Returns:
        The resolved hex string.
    """
    return color[0] if isinstance(color, tuple) else color
