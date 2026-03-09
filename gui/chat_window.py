import tkinter as tk
from datetime import datetime

from PIL import Image, ImageTk

from gui.theme import get_theme
from gui.drag_drop import setup_drag_drop, open_file_dialog


class ChatWindow:
    def __init__(self, root: tk.Tk, on_file_received: callable, theme_name: str = "light"):
        self.root = root
        self.on_file_received = on_file_received
        self.theme_name = theme_name
        self.theme = get_theme(theme_name)

        # Keep references to PhotoImages so they aren't garbage-collected
        self._image_refs: list[ImageTk.PhotoImage] = []
        # Track message widgets for theme refresh
        self._message_widgets: list[dict] = []
        self._loading_counter = 0

        self.root.title("\u0424\u0438\u043d\u0430\u043d\u0441\u043e\u0432\u044b\u0439 \u0430\u0441\u0441\u0438\u0441\u0442\u0435\u043d\u0442")
        self.root.geometry("700x800")

        self._build_ui()
        self._try_setup_dnd()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        theme = self.theme

        # --- Top bar ---
        self.top_frame = tk.Frame(self.root, bg=theme["bg"])
        self.top_frame.pack(fill=tk.X)

        self.theme_btn = tk.Button(
            self.top_frame,
            text=self._theme_icon(),
            command=self.toggle_theme,
            bg=theme["bg"],
            fg=theme["text_color"],
            bd=0,
            font=("Segoe UI Emoji", 14),
        )
        self.theme_btn.pack(side=tk.LEFT, padx=8, pady=6)

        self.title_label = tk.Label(
            self.top_frame,
            text="\u0424\u0438\u043d\u0430\u043d\u0441\u043e\u0432\u044b\u0439 \u0430\u0441\u0441\u0438\u0441\u0442\u0435\u043d\u0442",
            bg=theme["bg"],
            fg=theme["text_color"],
            font=("Arial", 14, "bold"),
        )
        self.title_label.pack(side=tk.LEFT, padx=4, pady=6)

        # --- Chat area (Canvas + scrollbar) ---
        self.chat_container = tk.Frame(self.root, bg=theme["chat_bg"])
        self.chat_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.chat_container, bg=theme["chat_bg"], highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.chat_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.messages_frame = tk.Frame(self.canvas, bg=theme["chat_bg"])
        self.canvas_window = self.canvas.create_window((0, 0), window=self.messages_frame, anchor="nw")

        self.messages_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # --- Bottom bar ---
        self.bottom_frame = tk.Frame(self.root, bg=theme["bg"])
        self.bottom_frame.pack(fill=tk.X)

        self.upload_btn = tk.Button(
            self.bottom_frame,
            text="\U0001f4ce \u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0444\u0430\u0439\u043b",
            command=self._on_upload_click,
            bg=theme["button_bg"],
            fg=theme["button_fg"],
            font=("Arial", 11),
            relief=tk.FLAT,
            padx=12,
            pady=6,
        )
        self.upload_btn.pack(pady=8)

    # ------------------------------------------------------------------
    # Drag-and-drop
    # ------------------------------------------------------------------

    def _try_setup_dnd(self):
        try:
            setup_drag_drop(self.root, self._handle_file)
        except (ImportError, Exception):
            pass  # fallback: user clicks "Upload" button

    def _on_upload_click(self):
        open_file_dialog(self._handle_file)

    def _handle_file(self, file_path: str):
        self.add_message(f"\U0001f4c4 {file_path}", sender="user")
        if self.on_file_received:
            self.on_file_received(file_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_message(self, text: str, sender: str = "bot"):
        theme = self.theme
        timestamp = datetime.now().strftime("%H:%M")

        anchor = tk.E if sender == "user" else tk.W
        bg = theme["user_msg_bg"] if sender == "user" else theme["bot_msg_bg"]

        row = tk.Frame(self.messages_frame, bg=theme["chat_bg"])
        row.pack(fill=tk.X, padx=10, pady=4, anchor=anchor)

        bubble = tk.Frame(row, bg=bg, padx=10, pady=6)
        if sender == "user":
            bubble.pack(side=tk.RIGHT)
        else:
            bubble.pack(side=tk.LEFT)

        msg_label = tk.Label(
            bubble,
            text=text,
            bg=bg,
            fg=theme["text_color"],
            wraplength=450,
            justify=tk.LEFT,
            font=("Arial", 11),
        )
        msg_label.pack(anchor=tk.W)

        ts_label = tk.Label(
            bubble,
            text=timestamp,
            bg=bg,
            fg=theme["timestamp_color"],
            font=("Arial", 8),
        )
        ts_label.pack(anchor=tk.E)

        self._message_widgets.append({
            "row": row,
            "bubble": bubble,
            "msg_label": msg_label,
            "ts_label": ts_label,
            "sender": sender,
        })

        self._scroll_to_bottom()

    def add_image(self, image_path: str, caption: str = ""):
        theme = self.theme

        img = Image.open(image_path)
        max_w = 500
        if img.width > max_w:
            ratio = max_w / img.width
            img = img.resize((max_w, int(img.height * ratio)), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self._image_refs.append(photo)

        row = tk.Frame(self.messages_frame, bg=theme["chat_bg"])
        row.pack(fill=tk.X, padx=10, pady=4, anchor=tk.W)

        bubble = tk.Frame(row, bg=theme["bot_msg_bg"], padx=10, pady=6)
        bubble.pack(side=tk.LEFT)

        img_label = tk.Label(bubble, image=photo, bg=theme["bot_msg_bg"])
        img_label.pack()

        if caption:
            cap_label = tk.Label(
                bubble,
                text=caption,
                bg=theme["bot_msg_bg"],
                fg=theme["text_color"],
                wraplength=450,
                justify=tk.LEFT,
                font=("Arial", 10),
            )
            cap_label.pack(anchor=tk.W, pady=(4, 0))

        timestamp = datetime.now().strftime("%H:%M")
        ts_label = tk.Label(
            bubble,
            text=timestamp,
            bg=theme["bot_msg_bg"],
            fg=theme["timestamp_color"],
            font=("Arial", 8),
        )
        ts_label.pack(anchor=tk.E)

        self._message_widgets.append({
            "row": row,
            "bubble": bubble,
            "msg_label": img_label,
            "ts_label": ts_label,
            "sender": "bot",
        })

        self._scroll_to_bottom()

    def show_loading(self, message: str = "\u041e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0430...") -> int:
        self._loading_counter += 1
        loading_id = self._loading_counter

        theme = self.theme
        row = tk.Frame(self.messages_frame, bg=theme["chat_bg"], name=f"loading_{loading_id}")
        row.pack(fill=tk.X, padx=10, pady=4, anchor=tk.W)

        bubble = tk.Frame(row, bg=theme["bot_msg_bg"], padx=10, pady=6)
        bubble.pack(side=tk.LEFT)

        label = tk.Label(
            bubble,
            text=f"\u23f3 {message}",
            bg=theme["bot_msg_bg"],
            fg=theme["text_color"],
            font=("Arial", 11),
        )
        label.pack()

        self._scroll_to_bottom()
        return loading_id

    def hide_loading(self, loading_id: int):
        target_name = f"loading_{loading_id}"
        for child in self.messages_frame.winfo_children():
            if str(child).endswith(target_name):
                child.destroy()
                break

    def toggle_theme(self):
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self.theme = get_theme(self.theme_name)
        self._apply_theme()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _theme_icon(self) -> str:
        return "\u2600\ufe0f" if self.theme_name == "light" else "\U0001f319"

    def _apply_theme(self):
        theme = self.theme

        self.root.configure(bg=theme["bg"])
        self.top_frame.configure(bg=theme["bg"])
        self.theme_btn.configure(text=self._theme_icon(), bg=theme["bg"], fg=theme["text_color"])
        self.title_label.configure(bg=theme["bg"], fg=theme["text_color"])
        self.chat_container.configure(bg=theme["chat_bg"])
        self.canvas.configure(bg=theme["chat_bg"])
        self.messages_frame.configure(bg=theme["chat_bg"])
        self.bottom_frame.configure(bg=theme["bg"])
        self.upload_btn.configure(bg=theme["button_bg"], fg=theme["button_fg"])

        for w in self._message_widgets:
            sender = w["sender"]
            bg = theme["user_msg_bg"] if sender == "user" else theme["bot_msg_bg"]
            w["row"].configure(bg=theme["chat_bg"])
            w["bubble"].configure(bg=bg)
            w["msg_label"].configure(bg=bg, fg=theme["text_color"])
            w["ts_label"].configure(bg=bg, fg=theme["timestamp_color"])

    def _on_frame_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def _scroll_to_bottom(self):
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
