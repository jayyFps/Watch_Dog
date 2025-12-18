import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import os
import csv
from datetime import datetime
import requests

# ================== KONFIGURASI ==================

# Folder tempat Core Temp menyimpan file log (CT-Log*.csv)
CORETEMP_LOG_DIR = r"C:\CoreTempLogs"  # GANTI SESUAI PUNYAMU

# Telegram
TELEGRAM_BOT_TOKEN = "8299415824:AAGJugT88cP03PlsAIhzta6dHhglu5gJ6mI"
TELEGRAM_CHAT_ID = "7614098809"
TELEGRAM_ENABLED = True  # False kalau mau matikan notif


class SimpleMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PC / GPU Monitor with Telegram & App Watch")
        self.root.geometry("600x600")
        self.root.resizable(False, False)

        # status umum
        self.monitoring = False

        # flag per-alert (supaya tidak spam)
        self.cpu_load_alert_on = False
        self.gpu_load_alert_on = False
        self.cpu_temp_alert_on = False
        self.gpu_temp_alert_on = False

        # logging
        self.log_file = None
        self.log_writer = None
        self.log_filename = ""

        # history sesi (untuk jendela riwayat)
        self.history = []

        # pemantauan aplikasi target
        self.target_was_running = False

        # ====== FRAME UTAMA ======
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        # judul
        title_label = ttk.Label(
            main_frame,
            text="PC / GPU Monitor with Telegram & App Watch",
            font=("Segoe UI", 14, "bold"),
        )
        title_label.pack(pady=(0, 10))

        # ===== CPU USAGE =====
        cpu_frame = ttk.Frame(main_frame)
        cpu_frame.pack(fill="x", pady=5)

        self.cpu_label = tk.Label(cpu_frame, text="CPU Usage: 0 %", anchor="w")
        self.cpu_label.pack(anchor="w")

        self.cpu_bar = ttk.Progressbar(
            cpu_frame,
            orient="horizontal",
            length=560,
            mode="determinate",
            maximum=100,
        )
        self.cpu_bar.pack(fill="x")

        # ===== RAM =====
        ram_frame = ttk.Frame(main_frame)
        ram_frame.pack(fill="x", pady=5)

        self.ram_label = tk.Label(ram_frame, text="RAM Usage: 0 %", anchor="w")
        self.ram_label.pack(anchor="w")

        self.ram_bar = ttk.Progressbar(
            ram_frame,
            orient="horizontal",
            length=560,
            mode="determinate",
            maximum=100,
        )
        self.ram_bar.pack(fill="x")

        # ===== GPU LOAD (INFO) =====
        gpu_load_frame = ttk.Frame(main_frame)
        gpu_load_frame.pack(fill="x", pady=5)

        self.gpu_load_label = tk.Label(
            gpu_load_frame,
            text="GPU Load: N/A (pastikan Open/Libre HW Monitor berjalan)",
            anchor="w",
        )
        self.gpu_load_label.pack(anchor="w")

        self.gpu_load_bar = ttk.Progressbar(
            gpu_load_frame,
            orient="horizontal",
            length=560,
            mode="determinate",
            maximum=100,
        )
        self.gpu_load_bar.pack(fill="x")

        # ========== BAGIAN URUTAN BATAS & INFORMASI ==========
        # 1) Batas Load CPU
        cpu_limit_frame = ttk.Frame(main_frame)
        cpu_limit_frame.pack(fill="x", pady=2)

        ttk.Label(cpu_limit_frame, text="Batas Load CPU (%):").pack(side="left")
        self.cpu_limit_var = tk.StringVar(value="80")
        ttk.Entry(cpu_limit_frame, textvariable=self.cpu_limit_var, width=5).pack(
            side="left", padx=(5, 10)
        )
        ttk.Label(
            cpu_limit_frame, text="(Jika terlampaui → peringatan + Telegram)"
        ).pack(side="left")

        # 2) Batas Suhu CPU
        cpu_temp_limit_frame = ttk.Frame(main_frame)
        cpu_temp_limit_frame.pack(fill="x", pady=2)

        ttk.Label(cpu_temp_limit_frame, text="Batas Suhu CPU (°C):").pack(side="left")
        self.cpu_temp_limit_var = tk.StringVar(value="80")
        ttk.Entry(
            cpu_temp_limit_frame, textvariable=self.cpu_temp_limit_var, width=5
        ).pack(side="left", padx=(5, 10))

        # 3) Informasi Suhu CPU
        cpu_temp_frame = ttk.Frame(main_frame)
        cpu_temp_frame.pack(fill="x", pady=3)

        self.cpu_temp_label = tk.Label(
            cpu_temp_frame,
            text="Informasi Suhu CPU: N/A (Core Temp + logging wajib aktif)",
            anchor="w",
        )
        self.cpu_temp_label.pack(anchor="w")

        # 4) Batas Load GPU
        gpu_load_limit_frame = ttk.Frame(main_frame)
        gpu_load_limit_frame.pack(fill="x", pady=2)

        ttk.Label(gpu_load_limit_frame, text="Batas Load GPU (%):").pack(side="left")
        self.gpu_load_limit_var = tk.StringVar(value="80")
        ttk.Entry(
            gpu_load_limit_frame, textvariable=self.gpu_load_limit_var, width=5
        ).pack(side="left", padx=(5, 10))
        ttk.Label(
            gpu_load_limit_frame, text="(Jika terlampaui → peringatan + Telegram)"
        ).pack(side="left")

        # 5) Batas Suhu GPU
        gpu_limit_frame = ttk.Frame(main_frame)
        gpu_limit_frame.pack(fill="x", pady=2)

        ttk.Label(gpu_limit_frame, text="Batas Suhu GPU (°C):").pack(side="left")
        self.gpu_temp_limit_var = tk.StringVar(value="75")
        ttk.Entry(gpu_limit_frame, textvariable=self.gpu_temp_limit_var, width=5).pack(
            side="left", padx=(5, 10)
        )

        # 6) Informasi Suhu GPU
        gpu_frame = ttk.Frame(main_frame)
        gpu_frame.pack(fill="x", pady=3)

        self.gpu_temp_label = tk.Label(
            gpu_frame,
            text="Informasi Suhu GPU: N/A (butuh Open/Libre Hardware Monitor)",
            anchor="w",
        )
        self.gpu_temp_label.pack(anchor="w")

        # ===== APLIKASI TARGET =====
        target_frame = ttk.Frame(main_frame)
        target_frame.pack(fill="x", pady=5)

        ttk.Label(
            target_frame,
            text="Aplikasi target (proses), contoh: notepad.exe / game.exe:",
        ).pack(anchor="w")

        self.target_var = tk.StringVar(value="")

        self.target_combo = ttk.Combobox(
            target_frame, textvariable=self.target_var, width=40, state="normal"
        )
        self.target_combo.pack(anchor="w", pady=(2, 0))

        refresh_btn = ttk.Button(
            target_frame, text="Refresh daftar aplikasi", command=self.refresh_process_list
        )
        refresh_btn.pack(anchor="w", pady=(2, 0))

        ttk.Label(
            target_frame,
            text="Jika diisi: saat aplikasi berhenti → popup + notifikasi Telegram.",
            font=("Segoe UI", 8),
        ).pack(anchor="w")

        # ===== TOMBOL =====
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=8)

        self.start_button = ttk.Button(
            button_frame, text="Start Monitoring", command=self.start_monitoring
        )
        self.start_button.pack(side="left", padx=(0, 5))

        self.stop_button = ttk.Button(
            button_frame, text="Stop", command=self.stop_monitoring
        )
        self.stop_button.pack(side="left")

        history_button = ttk.Button(
            button_frame, text="Lihat Riwayat (Sesi Ini)", command=self.show_history_window
        )
        history_button.pack(side="left", padx=(10, 0))

        # ===== STATUS LOGGING =====
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill="x", pady=(8, 0))

        self.log_status_label = ttk.Label(
            log_frame, text="Logging: belum aktif", font=("Segoe UI", 8)
        )
        self.log_status_label.pack(anchor="w")

        # ===== STATUS TELEGRAM =====
        telegram_frame = ttk.Frame(main_frame)
        telegram_frame.pack(fill="x", pady=(2, 0))

        tele_status_text = "Telegram: AKTIF" if TELEGRAM_ENABLED else "Telegram: NONAKTIF"
        self.telegram_status_label = ttk.Label(
            telegram_frame, text=tele_status_text, font=("Segoe UI", 8)
        )
        self.telegram_status_label.pack(anchor="w")

        # ===== STATUS BAWAH =====
        self.status_label = ttk.Label(
            main_frame, text="Status: belum mulai monitoring", font=("Segoe UI", 8)
        )
        self.status_label.pack(anchor="w", pady=(10, 0))

        # event tutup window
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ========= UTIL BATAS =========
    def get_cpu_limit(self):
        try:
            v = float(self.cpu_limit_var.get())
            if v <= 0:
                raise ValueError
            return v
        except ValueError:
            return 80.0

    def get_cpu_temp_limit(self):
        try:
            v = float(self.cpu_temp_limit_var.get())
            if v <= 0:
                raise ValueError
            return v
        except ValueError:
            return 80.0

    def get_gpu_temp_limit(self):
        try:
            v = float(self.gpu_temp_limit_var.get())
            if v <= 0:
                raise ValueError
            return v
        except ValueError:
            return 75.0

    def get_gpu_load_limit(self):
        try:
            v = float(self.gpu_load_limit_var.get())
            if v <= 0:
                raise ValueError
            return v
        except ValueError:
            return 80.0

    # ========= BACA SUHU CPU DARI CORE TEMP (LOG) =========
    def get_cpu_temperature(self):
        """
        Baca suhu CPU dari file log Core Temp (CT-Log*.csv).
        Nilai log biasanya dalam skala besar, misal 55000 = 55.0 °C.
        """
        try:
            if not os.path.isdir(CORETEMP_LOG_DIR):
                return None

            files = [f for f in os.listdir(CORETEMP_LOG_DIR) if f.lower().endswith(".csv")]
            if not files:
                return None

            latest = max(
                files,
                key=lambda name: os.path.getmtime(os.path.join(CORETEMP_LOG_DIR, name)),
            )
            path = os.path.join(CORETEMP_LOG_DIR, latest)

            with open(path, encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                rows = [r for r in reader if r and any(c.strip() for c in r)]

            if len(rows) < 2:
                return None

            # cari baris header "Time"
            header_idx = None
            for i, row in enumerate(rows):
                if row[0].strip().lower() == "time":
                    header_idx = i
                    break
            if header_idx is None:
                return None

            header = rows[header_idx]

            data_rows = []
            for row in rows[header_idx + 1 :]:
                first = row[0].strip().lower()
                if first.startswith("session end"):
                    continue
                data_rows.append(row)
            if not data_rows:
                return None

            last = data_rows[-1]

            temp_indices = []
            for i, name in enumerate(header):
                n = (name or "").lower()
                if "cur." in n and "core" in n:
                    temp_indices.append(i)
            if not temp_indices:
                for i, name in enumerate(header):
                    n = (name or "").lower()
                    if "package" in n:
                        temp_indices.append(i)
            if not temp_indices:
                return None

            temps = []
            for idx in temp_indices:
                if idx >= len(last):
                    continue
                cell = last[idx]
                if cell in (None, ""):
                    continue
                s = str(cell).strip().replace(",", ".")
                try:
                    val = float(s)
                except ValueError:
                    continue
                while val > 150 and val > 0:
                    val = val / 10.0
                if 0 <= val <= 150:
                    temps.append(val)
            if not temps:
                return None

            return max(temps)
        except Exception:
            return None

    # ========= HELPER HW MONITOR (GPU TEMP & LOAD) =========
    def _read_temp_from_hwmonitor(self, keywords):
        try:
            import wmi
        except ImportError:
            return None

        namespaces = ["root\\OpenHardwareMonitor", "root\\LibreHardwareMonitor"]

        for ns in namespaces:
            try:
                ohm = wmi.WMI(namespace=ns)
            except Exception:
                continue

            try:
                for sensor in ohm.Sensor():
                    if getattr(sensor, "SensorType", "").lower() != "temperature":
                        continue
                    name = (getattr(sensor, "Name", "") or "").lower()
                    if any(k in name for k in keywords):
                        value = getattr(sensor, "Value", None)
                        if value is not None:
                            return float(value)
            except Exception:
                continue

        return None

    def _read_load_from_hwmonitor(self, keywords):
        try:
            import wmi
        except ImportError:
            return None

        namespaces = ["root\\OpenHardwareMonitor", "root\\LibreHardwareMonitor"]

        for ns in namespaces:
            try:
                ohm = wmi.WMI(namespace=ns)
            except Exception:
                continue

            try:
                for sensor in ohm.Sensor():
                    if getattr(sensor, "SensorType", "").lower() != "load":
                        continue
                    name = (getattr(sensor, "Name", "") or "").lower()
                    if any(k in name for k in keywords):
                        value = getattr(sensor, "Value", None)
                        if value is not None:
                            return float(value)
            except Exception:
                continue

        return None

    def get_gpu_temperature(self):
        return self._read_temp_from_hwmonitor(["gpu"])

    def get_gpu_load(self):
        return self._read_load_from_hwmonitor(["gpu core", "gpu", "graphics"])

    # ========= REFRESH DAFTAR PROSES =========
    def refresh_process_list(self):
        names = set()
        for proc in psutil.process_iter(["name"]):
            try:
                name = proc.info.get("name")
                if name:
                    names.add(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        self.target_combo["values"] = sorted(names)

    # ========= START / STOP =========
    def start_monitoring(self):
        if not self.monitoring:
            self.monitoring = True

            # reset flags alert
            self.cpu_load_alert_on = False
            self.gpu_load_alert_on = False
            self.cpu_temp_alert_on = False
            self.gpu_temp_alert_on = False

            self.status_label.config(text="Status: monitoring berjalan")
            self.history = []
            self.target_was_running = False

            self.refresh_process_list()
            self.start_logging()
            self.update_stats()

    def stop_monitoring(self):
        self.monitoring = False
        self.status_label.config(text="Status: monitoring berhenti")
        self.cpu_label.config(fg="black")
        self.stop_logging()

    # ========= LOOP MONITOR =========
    def update_stats(self):
        if not self.monitoring:
            return

        cpu_percent = psutil.cpu_percent(interval=None)
        ram_percent = psutil.virtual_memory().percent

        self.cpu_label.config(text=f"CPU Usage: {cpu_percent:.1f} %")
        self.ram_label.config(text=f"RAM Usage: {ram_percent:.1f} %")

        self.cpu_bar["value"] = cpu_percent
        self.ram_bar["value"] = ram_percent

        # GPU Load
        gpu_load = self.get_gpu_load()
        if gpu_load is not None:
            self.gpu_load_label.config(text=f"GPU Load: {gpu_load:.1f} %")
            self.gpu_load_bar["value"] = gpu_load
        else:
            self.gpu_load_label.config(
                text="GPU Load: N/A (pastikan Open/Libre HW Monitor berjalan)"
            )
            self.gpu_load_bar["value"] = 0

        # suhu CPU & GPU
        cpu_temp = self.get_cpu_temperature()
        if cpu_temp is not None:
            self.cpu_temp_label.config(text=f"Informasi Suhu CPU: {cpu_temp:.1f} °C")
        else:
            self.cpu_temp_label.config(
                text="Informasi Suhu CPU: N/A (Core Temp + logging aktif?)"
            )

        gpu_temp = self.get_gpu_temperature()
        if gpu_temp is not None:
            self.gpu_temp_label.config(text=f"Informasi Suhu GPU: {gpu_temp:.1f} °C")
        else:
            self.gpu_temp_label.config(
                text="Informasi Suhu GPU: N/A (Open/Libre HW Monitor tidak memberi suhu)"
            )

        cpu_limit = self.get_cpu_limit()
        gpu_load_limit = self.get_gpu_load_limit()
        cpu_temp_limit = self.get_cpu_temp_limit()
        gpu_temp_limit = self.get_gpu_temp_limit()

        cpu_over = cpu_percent >= cpu_limit
        gpu_load_over = gpu_load is not None and gpu_load >= gpu_load_limit
        cpu_temp_over = cpu_temp is not None and cpu_temp >= cpu_temp_limit
        gpu_temp_over = gpu_temp is not None and gpu_temp >= gpu_temp_limit

        any_alert = cpu_over or gpu_load_over or cpu_temp_over or gpu_temp_over
        if any_alert:
            self.cpu_label.config(fg="red")
            self.status_label.config(
                text="PERINGATAN: batas penggunaan / suhu terlampaui"
            )
        else:
            self.cpu_label.config(fg="black")
            self.status_label.config(text="Status: monitoring berjalan")

        # ========= ALERT PER-KONDISI =========
        # CPU suhu
        if cpu_temp_over and not self.cpu_temp_alert_on:
            self.cpu_temp_alert_on = True
            self.show_and_send_alert(
                "Peringatan Suhu CPU",
                [f"Suhu CPU {cpu_temp:.1f}°C ≥ batas {cpu_temp_limit:.1f}°C"],
                cpu_percent,
                ram_percent,
                gpu_load,
                cpu_temp,
                gpu_temp,
                cpu_limit,
                gpu_load_limit,
                cpu_temp_limit,
                gpu_temp_limit,
            )
        elif not cpu_temp_over:
            self.cpu_temp_alert_on = False

        # GPU suhu
        if gpu_temp_over and not self.gpu_temp_alert_on:
            self.gpu_temp_alert_on = True
            self.show_and_send_alert(
                "Peringatan Suhu GPU",
                [f"Suhu GPU {gpu_temp:.1f}°C ≥ batas {gpu_temp_limit:.1f}°C"],
                cpu_percent,
                ram_percent,
                gpu_load,
                cpu_temp,
                gpu_temp,
                cpu_limit,
                gpu_load_limit,
                cpu_temp_limit,
                gpu_temp_limit,
            )
        elif not gpu_temp_over:
            self.gpu_temp_alert_on = False

        # CPU load
        if cpu_over and not self.cpu_load_alert_on:
            self.cpu_load_alert_on = True
            self.show_and_send_alert(
                "Peringatan Load CPU",
                [f"CPU {cpu_percent:.1f}% ≥ batas {cpu_limit:.1f}%"],
                cpu_percent,
                ram_percent,
                gpu_load,
                cpu_temp,
                gpu_temp,
                cpu_limit,
                gpu_load_limit,
                cpu_temp_limit,
                gpu_temp_limit,
            )
        elif not cpu_over:
            self.cpu_load_alert_on = False

        # GPU load
        if gpu_load_over and not self.gpu_load_alert_on:
            self.gpu_load_alert_on = True
            self.show_and_send_alert(
                "Peringatan Load GPU",
                [f"GPU Load {gpu_load:.1f}% ≥ batas {gpu_load_limit:.1f}%"],
                cpu_percent,
                ram_percent,
                gpu_load,
                cpu_temp,
                gpu_temp,
                cpu_limit,
                gpu_load_limit,
                cpu_temp_limit,
                gpu_temp_limit,
            )
        elif not gpu_load_over:
            self.gpu_load_alert_on = False

        # PANTAU APLIKASI TARGET
        self.check_target_app(
            cpu_percent,
            cpu_temp,
            gpu_temp,
            cpu_limit,
            cpu_temp_limit,
            gpu_temp_limit,
        )

        # LOGGING
        self.write_log(
            cpu_percent,
            ram_percent,
            gpu_load,
            cpu_temp,
            gpu_temp,
            cpu_limit,
            gpu_load_limit,
            cpu_temp_limit,
            gpu_temp_limit,
            int(any_alert),
        )

        self.root.after(1000, self.update_stats)

    def show_and_send_alert(
        self,
        title,
        reason_lines,
        cpu_percent,
        ram_percent,
        gpu_load,
        cpu_temp,
        gpu_temp,
        cpu_limit,
        gpu_load_limit,
        cpu_temp_limit,
        gpu_temp_limit,
    ):
        """Tampilkan popup + kirim Telegram."""
        try:
            messagebox.showwarning(title, "\n".join(reason_lines))
        except Exception:
            pass

        self.send_telegram_alert_main(
            cpu_percent,
            ram_percent,
            gpu_load,
            cpu_temp,
            gpu_temp,
            cpu_limit,
            gpu_load_limit,
            cpu_temp_limit,
            gpu_temp_limit,
        )

    # ========= PANTAU APLIKASI TARGET =========
    def is_target_running(self):
        keyword = self.target_var.get().strip()
        if not keyword:
            return False

        keyword = keyword.lower()
        for proc in psutil.process_iter(["name", "cmdline"]):
            try:
                name = (proc.info.get("name") or "").lower()
                cmdline = " ".join(proc.info.get("cmdline") or []).lower()
                if keyword in name or keyword in cmdline:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def check_target_app(
        self,
        cpu_percent,
        cpu_temp,
        gpu_temp,
        cpu_limit,
        cpu_temp_limit,
        gpu_temp_limit,
    ):
        """Jika aplikasi target berhenti → popup + notifikasi Telegram."""
        keyword = self.target_var.get().strip()
        if not keyword:
            self.target_was_running = False
            return

        running_now = self.is_target_running()

        if running_now:
            if not self.target_was_running:
                self.target_was_running = True
            return
        else:
            if self.target_was_running:
                self.target_was_running = False

                try:
                    messagebox.showinfo(
                        "Aplikasi berhenti",
                        f"Aplikasi target '{keyword}' terdeteksi berhenti.",
                    )
                except Exception:
                    pass

                reasons = [f"CPU saat berhenti: {cpu_percent:.1f}%"]
                if cpu_temp is not None:
                    reasons.append(
                        f"Suhu CPU saat berhenti: {cpu_temp:.1f}°C (batas {cpu_temp_limit:.1f}°C)"
                    )
                else:
                    reasons.append("Suhu CPU saat berhenti: N/A")

                if gpu_temp is not None:
                    reasons.append(
                        f"Suhu GPU saat berhenti: {gpu_temp:.1f}°C (batas {gpu_temp_limit:.1f}°C)"
                    )
                else:
                    reasons.append("Suhu GPU saat berhenti: N/A")

                self.send_telegram_alert_app_stopped(keyword, reasons)

    # ========= TELEGRAM =========
    def send_telegram(self, text: str):
        if not TELEGRAM_ENABLED:
            return
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("Telegram belum dikonfigurasi.")
            return
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
            requests.post(url, data=data, timeout=5)
        except Exception as e:
            print("Gagal kirim Telegram:", e)

    def send_telegram_alert_main(
        self,
        cpu_percent,
        ram_percent,
        gpu_load,
        cpu_temp,
        gpu_temp,
        cpu_limit,
        gpu_load_limit,
        cpu_temp_limit,
        gpu_temp_limit,
    ):
        lines = [
            "[ALERT]",
            f"CPU: {cpu_percent:.1f}% (batas {cpu_limit:.1f}%)",
            f"RAM: {ram_percent:.1f}%",
        ]

        if gpu_load is not None:
            lines.append(f"GPU Load: {gpu_load:.1f}% (batas {gpu_load_limit:.1f}%)")
        else:
            lines.append("GPU Load: N/A")

        if cpu_temp is not None:
            lines.append(
                f"Suhu CPU: {cpu_temp:.1f}°C (batas {cpu_temp_limit:.1f}°C)"
            )
        else:
            lines.append("Suhu CPU: N/A")

        if gpu_temp is not None:
            lines.append(
                f"Suhu GPU: {gpu_temp:.1f}°C (batas {gpu_temp_limit:.1f}°C)"
            )
        else:
            lines.append("Suhu GPU: N/A")

        lines.append(f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.send_telegram("\n".join(lines))

    def send_telegram_alert_app_stopped(self, keyword, reasons):
        lines = [
            "[ALERT APLIKASI]",
            f"Aplikasi target: {keyword}",
            "Status: berhenti / tidak terdeteksi.",
            "",
            "Kondisi saat berhenti:",
        ]
        lines.extend(reasons)
        lines.append(f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.send_telegram("\n".join(lines))

    # ========= LOGGING =========
    def start_logging(self):
        os.makedirs("logs", exist_ok=True)
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = os.path.join("logs", f"log_{now}.csv")

        self.log_file = open(self.log_filename, mode="w", newline="", encoding="utf-8")
        self.log_writer = csv.writer(self.log_file)
        self.log_writer.writerow(
            [
                "timestamp",
                "cpu_percent",
                "ram_percent",
                "gpu_load",
                "cpu_temp",
                "gpu_temp",
                "cpu_limit",
                "gpu_load_limit",
                "cpu_temp_limit",
                "gpu_temp_limit",
                "alert_any",
            ]
        )
        self.log_status_label.config(text=f"Logging: {self.log_filename}")

    def write_log(
        self,
        cpu_percent,
        ram_percent,
        gpu_load,
        cpu_temp,
        gpu_temp,
        cpu_limit,
        gpu_load_limit,
        cpu_temp_limit,
        gpu_temp_limit,
        alert_flag,
    ):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cpu_temp_str = f"{cpu_temp:.1f}" if cpu_temp is not None else ""
        gpu_temp_str = f"{gpu_temp:.1f}" if gpu_temp is not None else ""
        gpu_load_str = f"{gpu_load:.1f}" if gpu_load is not None else ""

        if self.log_writer is not None:
            self.log_writer.writerow(
                [
                    timestamp,
                    f"{cpu_percent:.1f}",
                    f"{ram_percent:.1f}",
                    gpu_load_str,
                    cpu_temp_str,
                    gpu_temp_str,
                    f"{cpu_limit:.1f}",
                    f"{gpu_load_limit:.1f}",
                    f"{cpu_temp_limit:.1f}",
                    f"{gpu_temp_limit:.1f}",
                    alert_flag,
                ]
            )
            self.log_file.flush()

        self.history.append(
            (
                timestamp,
                cpu_percent,
                ram_percent,
                gpu_load,
                cpu_temp,
                gpu_temp,
                cpu_limit,
                gpu_load_limit,
                cpu_temp_limit,
                gpu_temp_limit,
                alert_flag,
            )
        )

    def stop_logging(self):
        if self.log_file is not None:
            self.log_file.close()
            self.log_file = None
            self.log_writer = None
            self.log_status_label.config(
                text=f"Logging: berhenti (file: {self.log_filename})"
            )

    # ========= RIWAYAT =========
    def show_history_window(self):
        if not self.history:
            messagebox.showinfo(
                "Riwayat Kosong", "Belum ada data riwayat pada sesi ini."
            )
            return

        win = tk.Toplevel(self.root)
        win.title("Riwayat Monitoring - Sesi Ini")
        win.geometry("980x380")

        columns = (
            "timestamp",
            "cpu",
            "ram",
            "gpu_load",
            "cpu_temp",
            "gpu_temp",
            "cpu_limit",
            "gpu_load_limit",
            "cpu_temp_limit",
            "gpu_temp_limit",
            "alert",
        )
        tree = ttk.Treeview(win, columns=columns, show="headings")

        tree.heading("timestamp", text="Waktu")
        tree.heading("cpu", text="CPU (%)")
        tree.heading("ram", text="RAM (%)")
        tree.heading("gpu_load", text="GPU Load (%)")
        tree.heading("cpu_temp", text="CPU (°C)")
        tree.heading("gpu_temp", text="GPU (°C)")
        tree.heading("cpu_limit", text="Batas CPU")
        tree.heading("gpu_load_limit", text="Batas Load GPU")
        tree.heading("cpu_temp_limit", text="Batas Suhu CPU")
        tree.heading("gpu_temp_limit", text="Batas Suhu GPU")
        tree.heading("alert", text="Alert")

        tree.column("timestamp", width=180)
        tree.column("cpu", width=70, anchor="center")
        tree.column("ram", width=70, anchor="center")
        tree.column("gpu_load", width=90, anchor="center")
        tree.column("cpu_temp", width=80, anchor="center")
        tree.column("gpu_temp", width=80, anchor="center")
        tree.column("cpu_limit", width=90, anchor="center")
        tree.column("gpu_load_limit", width=110, anchor="center")
        tree.column("cpu_temp_limit", width=110, anchor="center")
        tree.column("gpu_temp_limit", width=110, anchor="center")
        tree.column("alert", width=60, anchor="center")

        scrollbar = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for (
            ts,
            cpu,
            ram,
            gpu_load,
            cpu_temp,
            gpu_temp,
            cpu_limit,
            gpu_load_limit,
            cpu_temp_limit,
            gpu_temp_limit,
            alert_flag,
        ) in self.history:
            alert_text = "Ya" if alert_flag else "Tidak"
            cpu_temp_text = f"{cpu_temp:.1f}" if cpu_temp is not None else "N/A"
            gpu_temp_text = f"{gpu_temp:.1f}" if gpu_temp is not None else "N/A"
            gpu_load_text = f"{gpu_load:.1f}" if gpu_load is not None else "N/A"
            tree.insert(
                "",
                "end",
                values=(
                    ts,
                    f"{cpu:.1f}",
                    f"{ram:.1f}",
                    gpu_load_text,
                    cpu_temp_text,
                    gpu_temp_text,
                    f"{cpu_limit:.1f}",
                    f"{gpu_load_limit:.1f}",
                    f"{cpu_temp_limit:.1f}",
                    f"{gpu_temp_limit:.1f}",
                    alert_text,
                ),
            )

    # ========= TUTUP =========
    def on_close(self):
        self.monitoring = False
        self.stop_logging()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleMonitorApp(root)
    root.mainloop()
