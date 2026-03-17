"""
app/ui/components.py
Reusable UI component library — Linear-inspired design system.

Exports:
    Card              — Surface card with subtle border
    LabeledEntry      — Entry field with label above
    SectionHeader     — Page title + optional subtitle
    primary_button()  — Factory for a styled primary button
    StatusBadge       — Colored status chip (ok / error / warning / info)
    Divider           — Thin horizontal separator
    SearchBar         — Entry with placeholder + Enter callback
    NavItem           — Sidebar navigation button (used by shell)
"""

import customtkinter as ctk

from app.ui.theme import (
    COLOR_SURFACE,
    COLOR_BORDER,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_HOVER,
    COLOR_SUCCESS,
    COLOR_ERROR,
    COLOR_WARNING,
    RADIUS_LG,
    RADIUS_MD,
    SPACE_SM,
    SPACE_MD,
    FONT_XS,
    FONT_SM,
    FONT_MD,
    FONT_XL,
    c,
)


# ── Card ─────────────────────────────────────────────────────────────────────

class Card(ctk.CTkFrame):
    """Surface panel with Linear-style border and rounded corners.

    Drop-in replacement for ``ctk.CTkFrame`` with default token values.
    All CTkFrame kwargs are forwarded; the caller can override any default.
    """

    def __init__(self, parent, **kwargs):
        defaults: dict = dict(
            fg_color=COLOR_SURFACE,
            corner_radius=RADIUS_LG,
            border_width=1,
            border_color=c(COLOR_BORDER),
        )
        defaults.update(kwargs)
        super().__init__(parent, **defaults)


# ── LabeledEntry ─────────────────────────────────────────────────────────────

class LabeledEntry(ctk.CTkFrame):
    """Entry field with a small muted label positioned above it.

    Args:
        parent:       Parent widget.
        label:        Text shown above the entry.
        placeholder:  Optional placeholder text inside the entry.
        **kwargs:     Forwarded to the inner :class:`ctk.CTkEntry`.

    Accessor:
        ``.get()``  → current string value.
        ``.set(v)`` → replace entry contents.
    """

    def __init__(self, parent, label: str, placeholder: str = "", **kwargs):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(size=FONT_SM),
            text_color=c(COLOR_TEXT_MUTED),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        self._entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            font=ctk.CTkFont(size=FONT_MD),
            **kwargs,
        )
        self._entry.grid(row=1, column=0, sticky="ew")

    # public accessors ---------------------------------------------------

    def get(self) -> str:
        return self._entry.get()

    def set(self, value: str) -> None:
        self._entry.delete(0, "end")
        self._entry.insert(0, value)

    @property
    def entry(self) -> ctk.CTkEntry:
        """Direct access to the inner CTkEntry widget."""
        return self._entry


# ── SectionHeader ─────────────────────────────────────────────────────────────

class SectionHeader(ctk.CTkFrame):
    """Page-level title with an optional muted subtitle line.

    Args:
        parent:   Parent widget.
        title:    Bold large title text.
        subtitle: Optional smaller secondary line.
    """

    def __init__(self, parent, title: str, subtitle: str = "", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=FONT_XL, weight="bold"),
            text_color=c(COLOR_TEXT),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        if subtitle:
            ctk.CTkLabel(
                self,
                text=subtitle,
                font=ctk.CTkFont(size=FONT_SM),
                text_color=c(COLOR_TEXT_MUTED),
                anchor="w",
            ).grid(row=1, column=0, sticky="w", pady=(2, 0))


# ── primary_button ────────────────────────────────────────────────────────────

def primary_button(
    parent,
    text: str,
    command=None,
    **kwargs,
) -> ctk.CTkButton:
    """Factory that returns a styled primary action button.

    Merges sensible Linear defaults while allowing full override via **kwargs.

    Args:
        parent:  Parent widget.
        text:    Button label.
        command: Callback triggered on click.
        **kwargs: Forwarded to :class:`ctk.CTkButton`.

    Returns:
        Configured :class:`ctk.CTkButton` instance (not packed/gridded).
    """
    defaults: dict = dict(
        height=34,
        corner_radius=RADIUS_MD,
        fg_color=c(COLOR_ACCENT),
        hover_color=c(COLOR_ACCENT_HOVER),
        text_color="white",
        font=ctk.CTkFont(size=FONT_SM, weight="bold"),
    )
    defaults.update(kwargs)
    return ctk.CTkButton(parent, text=text, command=command, **defaults)


# ── StatusBadge ───────────────────────────────────────────────────────────────

class StatusBadge(ctk.CTkLabel):
    """Pill-shaped colored label indicating a state.

    Args:
        parent: Parent widget.
        status: One of ``"ok"``, ``"error"``, ``"warning"``, ``"info"``.
        text:   Custom label text; defaults to the uppercased status.

    Color mapping:
        ok      → green
        error   → red
        warning → amber
        info    → blue (accent)
    """

    _PALETTE: dict[str, tuple[str, str]] = {
        "ok":      (c(COLOR_SUCCESS), "black"),
        "error":   (c(COLOR_ERROR),   "white"),
        "warning": (c(COLOR_WARNING), "black"),
        "info":    (c(COLOR_ACCENT),  "white"),
    }

    def __init__(self, parent, status: str = "info", text: str = "", **kwargs):
        bg, fg = self._PALETTE.get(status.lower(), (c(COLOR_ACCENT), "white"))
        super().__init__(
            parent,
            text=text or status.upper(),
            fg_color=bg,
            text_color=fg,
            corner_radius=999,
            padx=8,
            pady=2,
            font=ctk.CTkFont(size=FONT_XS, weight="bold"),
            **kwargs,
        )


# ── Divider ───────────────────────────────────────────────────────────────────

class Divider(ctk.CTkFrame):
    """1 px horizontal separator using the border token color.

    Usage::

        Divider(parent).pack(fill="x", pady=SPACE_SM)
    """

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=c(COLOR_BORDER),
            height=1,
            corner_radius=0,
            **kwargs,
        )


# ── SearchBar ─────────────────────────────────────────────────────────────────

class SearchBar(ctk.CTkFrame):
    """Search entry with placeholder and an optional Enter-key callback.

    Args:
        parent:      Parent widget.
        placeholder: Gray hint text.
        on_search:   Called with the current text when the user presses Enter.
    """

    def __init__(self, parent, placeholder: str = "Pesquisar…", on_search=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._callback = on_search

        self._entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            font=ctk.CTkFont(size=FONT_MD),
            corner_radius=RADIUS_MD,
        )
        self._entry.grid(row=0, column=0, sticky="ew")
        self._entry.bind("<Return>", self._on_enter)

    def _on_enter(self, _event=None) -> None:
        if self._callback:
            self._callback(self._entry.get())

    def get(self) -> str:
        return self._entry.get()

    def set(self, value: str) -> None:
        self._entry.delete(0, "end")
        self._entry.insert(0, value)


# ── NavItem ───────────────────────────────────────────────────────────────────

class NavItem(ctk.CTkButton):
    """Sidebar navigation button.

    Designed to look like Linear's nav items: transparent background,
    muted text, hover highlight, and an active state with slightly
    brighter background.

    Typical use by the shell::

        item = NavItem(sidebar, "Gerador 207", icon="◻", command=...)
        item.set_active(True)
    """

    def __init__(self, parent, label: str, icon: str = "", command=None, **kwargs):
        from app.ui.theme import SIDEBAR_HOVER, SIDEBAR_ACTIVE

        text = f"  {icon}  {label}" if icon else f"  {label}"
        super().__init__(
            parent,
            text=text,
            anchor="w",
            height=34,
            corner_radius=RADIUS_MD,
            fg_color="transparent",
            hover_color=c(SIDEBAR_HOVER),
            text_color=c(COLOR_TEXT_MUTED),
            font=ctk.CTkFont(size=FONT_SM),
            command=command,
            **kwargs,
        )
        self._active = False

    def set_active(self, active: bool) -> None:
        from app.ui.theme import SIDEBAR_ACTIVE

        self._active = active
        if active:
            self.configure(fg_color=c(SIDEBAR_ACTIVE), text_color=c(COLOR_TEXT))
        else:
            self.configure(fg_color="transparent", text_color=c(COLOR_TEXT_MUTED))
