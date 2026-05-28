import json
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from ws_client import WebSocketManager
from http_client import HttpClient
from utilities import AppLogger, DEFAULT_COMMANDS


class AppUI:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Tkinter WebSocket + HTTP Client")
        self.root.geometry("980x760")
        self.root.minsize(900, 680)

        self.selected_option = tk.IntVar(value=0)
        self.ws_url_var = tk.StringVar(value="ws://localhost:8765/ws")
        self.http_url_var = tk.StringVar(value="http://localhost:8765")

        self.request_text = None
        self.log_text = None

        self.logger = AppLogger(self._append_log)
        self.http_client = HttpClient(self.logger)
        self.ws_manager = WebSocketManager(
            logger=self.logger,
            on_message=self._handle_ws_message,
            on_status_change=self._handle_ws_status_change,
        )
        self.ws_connected = False

        self._configure_style()
        self._build_ui()
        self._load_default_command(0)

    def _configure_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(5, weight=1)

        title = ttk.Label(
            self.root,
            text="IoT Device Simulator",
            font=("Segoe UI", 15, "bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 8))

        self._build_default_commands_section()
        self._build_server_config_section()
        self._build_request_section()
        self._build_action_buttons()
        self._build_log_section()

    def _build_default_commands_section(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Default commands")
        frame.grid(row=1, column=0, sticky="ew", padx=12, pady=6)
        for col_idx in range(len(DEFAULT_COMMANDS)):
            frame.columnconfigure(col_idx, weight=1)

        for index, command in enumerate(DEFAULT_COMMANDS, start=1):
            checkbox = ttk.Checkbutton(
                frame,
                text=command["name"],
                variable=self.selected_option,
                onvalue=index,
                offvalue=0,
                command=self._on_option_toggle,
            )
            checkbox.grid(row=0, column=index - 1, sticky="w", padx=8, pady=8)

    def _build_server_config_section(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Server configuration")
        frame.grid(row=2, column=0, sticky="ew", padx=12, pady=6)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="WebSocket URL:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(frame, textvariable=self.ws_url_var).grid(row=0, column=1, sticky="ew", padx=8, pady=6)

        ttk.Label(frame, text="HTTP Base URL:").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(frame, textvariable=self.http_url_var).grid(row=1, column=1, sticky="ew", padx=8, pady=6)

    def _build_request_section(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Command / Request")
        frame.grid(row=3, column=0, sticky="nsew", padx=12, pady=6)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        req_label = (
            "Paste JSON command for WebSocket, or HTTP request JSON.\n"
            "HTTP example: {\"method\":\"POST\",\"path\":\"/api/demo\",\"headers\":{},\"body\":{...}}"
        )
        ttk.Label(frame, text=req_label, justify="left").grid(row=0, column=0, sticky="nw", padx=8, pady=8)

        self.request_text = ScrolledText(frame, wrap="word", height=16)
        self.request_text.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

    def _build_action_buttons(self) -> None:
        frame = ttk.Frame(self.root)
        frame.grid(row=4, column=0, sticky="ew", padx=12, pady=6)
        for idx in range(4):
            frame.columnconfigure(idx, weight=1)

        ttk.Button(frame, text="Connect", command=self.connect).grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        ttk.Button(frame, text="Disconnect", command=self.disconnect).grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        ttk.Button(frame, text="Send", command=self.send_websocket).grid(row=0, column=2, sticky="ew", padx=6, pady=6)
        ttk.Button(frame, text="Send HTTP", command=self.send_http).grid(row=0, column=3, sticky="ew", padx=6, pady=6)

    def _build_log_section(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Logs")
        frame.grid(row=5, column=0, sticky="nsew", padx=12, pady=(6, 12))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.log_text = ScrolledText(frame, wrap="word", height=14, state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    def _append_log(self, message: str) -> None:
        def append() -> None:
            self.log_text.configure(state="normal")
            self.log_text.insert(tk.END, message)
            self.log_text.see(tk.END)
            self.log_text.configure(state="disabled")

        self.root.after(0, append)

    def _on_option_toggle(self) -> None:
        selected = self.selected_option.get()
        if selected == 0:
            self.logger.log("Default command selection cleared.")
            return
        self._load_default_command(selected - 1)

    def _load_default_command(self, index: int) -> None:
        payload = DEFAULT_COMMANDS[index]["payload"]
        self.request_text.delete("1.0", tk.END)
        self.request_text.insert("1.0", json.dumps(payload, indent=2))
        self.logger.log(f'Loaded default command: {DEFAULT_COMMANDS[index]["name"]}')

    def _get_request_text(self) -> str:
        return self.request_text.get("1.0", tk.END).strip()

    def _parse_request_json(self):
        raw_text = self._get_request_text()
        if not raw_text:
            self.logger.log("Request textbox is empty.")
            return None
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as exc:
            self.logger.log(f"Invalid JSON: {exc}")
            return None

    def _handle_ws_message(self, message: str) -> None:
        self.logger.log(f"WebSocket received: {message}")

    def _handle_ws_status_change(self, connected: bool) -> None:
        self.ws_connected = connected

    def connect(self) -> None:
        self.ws_manager.connect(self.ws_url_var.get().strip())

    def disconnect(self) -> None:
        self.ws_manager.disconnect()

    def send_websocket(self) -> None:
        payload = self._parse_request_json()
        if payload is None:
            return
        self.ws_manager.send_json(payload)

    def send_http(self) -> None:
        request_data = self._parse_request_json()
        if request_data is None:
            return
        self.http_client.send_request(
            base_url=self.http_url_var.get().strip(),
            request_data=request_data,
        )

    def run(self) -> None:
        self.root.mainloop()
