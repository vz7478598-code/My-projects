import re
import tkinter as tk
from tkinter import filedialog


def setup_drag_drop(widget, callback):
    """Register *widget* as a file drop zone using tkinterdnd2.

    When a file is dropped the extracted path is passed to *callback(file_path)*.
    Raises ImportError if tkinterdnd2 is not installed.
    """
    from tkinterdnd2 import DND_FILES  # noqa: WPS433

    widget.drop_target_register(DND_FILES)

    def _on_drop(event):
        raw = event.data
        # Windows wraps paths that contain spaces in curly braces:
        #   {C:/path/to file.pdf}
        match = re.match(r"^\{(.+)\}$", raw)
        file_path = match.group(1) if match else raw
        callback(file_path)

    widget.dnd_bind("<<Drop>>", _on_drop)


def open_file_dialog(callback):
    """Open a native file-picker dialog (fallback when drag-drop is unavailable)."""
    file_path = filedialog.askopenfilename(
        title="Select a file",
        filetypes=[
            ("PDF files", "*.pdf"),
            ("Images", "*.png *.jpg *.jpeg"),
            ("All files", "*.*"),
        ],
    )
    if file_path:
        callback(file_path)
