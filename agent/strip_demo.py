"""Spec 003: a demo strip, to check on the owner's Linux that a small window can sit on top of the game window and
draw smooth text. It shows a sample line at the bottom left of the screen for 90 seconds and quits (Ctrl-C quits at once).

It runs with the system Python, which has GTK, and not with uv's Python: the Tk that comes with uv's Python draws X11
bitmap fonts (seen on the owner's Linux, 2026-10-11). From the root of the repo:

    DISPLAY=:0 python3 agent/strip_demo.py
"""

import os
import signal
import sys

SECONDS_SHOWN = 90
MARGIN_PX = 24
SAMPLE_MARKUP = ('<span foreground="#8c8c8c">Jev</span>  <b>KITE</b>'
                 '        <span foreground="#8c8c8c">rules</span>  <b>KITE</b>')
STYLE = b"""
window { background-color: #121212; }
label { color: #ececec; font-family: Ubuntu, sans-serif; font-size: 26px; padding: 14px 28px; }
"""
INSTALL_HINT = "sudo apt install python3-gi gir1.2-gtk-3.0"


def bottom_left(area_x: int, area_y: int, area_height: int, strip_height: int, margin: int = MARGIN_PX) -> tuple[int, int]:
    """The top left corner that puts the strip `margin` pixels in from the bottom left corner of the area."""
    return area_x + margin, area_y + area_height - strip_height - margin


def main() -> int:
    # Only X11 lets a window that no window manager handles (a popup) be put at a given place and stay above the
    # others; GNOME on Wayland runs X11 programs, the game among them, through Xwayland. It must be set before GTK loads.
    os.environ["GDK_BACKEND"] = "x11"
    try:
        import gi
        gi.require_version("Gdk", "3.0")
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gdk, GLib, Gtk
    except (ImportError, ValueError) as error:
        print(f"strip_demo: GTK 3 for Python is not available ({error}); install it with: {INSTALL_HINT}", file=sys.stderr)
        return 1
    if not Gtk.init_check(sys.argv)[0]:
        print(f"strip_demo: cannot open the display {os.environ.get('DISPLAY')!r}; run it as: DISPLAY=:0 python3 agent/strip_demo.py",
              file=sys.stderr)
        return 1

    style = Gtk.CssProvider()
    style.load_from_data(STYLE)
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    label = Gtk.Label()
    label.set_markup(SAMPLE_MARKUP)
    strip = Gtk.Window(type=Gtk.WindowType.POPUP)
    strip.add(label)
    _, natural = strip.get_preferred_size()
    display = Gdk.Display.get_default()
    area = (display.get_primary_monitor() or display.get_monitor(0)).get_workarea()
    strip.move(*bottom_left(area.x, area.y, area.height, natural.height))
    strip.show_all()

    GLib.timeout_add_seconds(SECONDS_SHOWN, Gtk.main_quit)
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # GTK's loop would not see Ctrl-C otherwise
    print(f"strip_demo: a sample strip at the bottom left for {SECONDS_SHOWN} s; start the game in the other terminal now",
          file=sys.stderr)
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
