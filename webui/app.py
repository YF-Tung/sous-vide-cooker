# webui/app.py

from flask import Flask, jsonify, render_template
import threading


class WebUI:
    def __init__(self, controller, host="0.0.0.0", port=5000):
        self.controller = controller
        self.system_status = controller.system_status
        self.host = host
        self.port = port
        self.app = Flask(__name__, template_folder="templates", static_folder="static")
        self._register_routes()

    def _register_routes(self):
        @self.app.route("/")
        def index():
            return render_template("index.html")

        @self.app.route("/status")
        def get_status():
            return self.system_status.snapshot()

        @self.app.route("/temperature_history")
        def get_temperature_history():
            history = self.system_status.get_temperature_history()
            return jsonify(history)
        # 更多 routes 可以在這裡註冊...

    def run(self):
        self.app.run(host=self.host, port=self.port)

    def run_in_background(self):
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
