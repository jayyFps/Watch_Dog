MANUAL SINGKAT

PC / GPU Monitor with Telegram & App Watch

1. Deskripsi Aplikasi

Aplikasi ini merupakan program desktop berbasis Python yang dipakai untuk:

memantau pemakaian CPU dan RAM,

membaca suhu CPU dari Core Temp,

membaca load / suhu GPU dari Open/Libre Hardware Monitor (jika sensor tersedia),

mengirim peringatan ke layar dan Telegram bila melewati batas,

mengawasi aplikasi target (misalnya game/miner); jika aplikasi itu berhenti, akan muncul notifikasi.

Cocok untuk presentasi tema monitoring PC, overclocking ringan, atau tugas akhir yang berkaitan dengan hardware.

2. Fitur Utama

Monitoring realtime

CPU usage (%)

RAM usage (%)

GPU load (%)

Suhu CPU (°C)

Suhu GPU (°C) – bila tersedia di sensor

Batas dan Alert

Batas load CPU (%)

Batas suhu CPU (°C)

Batas load GPU (%)

Batas suhu GPU (°C)
Saat nilai lewat batas:

Muncul popup peringatan di Windows.

Terkirim pesan ke Telegram (jika bot diaktifkan).

App Watch

Pengguna memilih proses target dari daftar (contoh: game.exe).

Saat proses tersebut berhenti:

Aplikasi memberi popup.

Telegram menerima ringkasan kondisi CPU & suhu saat itu.

Logging

Semua data per detik disimpan ke file .csv di folder logs.

Data bisa dibuka di Excel untuk grafik/analisis.

3. Kebutuhan Sistem

Perangkat & OS

Windows 10 atau 11

Koneksi internet (untuk notifikasi Telegram)

Software

Python 3.x

Library Python:

pip install psutil requests wmi


Core Temp (untuk suhu CPU, dengan logging aktif)

OpenHardwareMonitor atau LibreHardwareMonitor (untuk GPU, bila ingin)

Akun Telegram + Bot + Chat ID

4. Instalasi Singkat

Clone / download repo GitHub ke folder, contoh C:\monitor.

Buka Command Prompt di folder tersebut lalu jalankan:

pip install -r requirements.txt
# atau
pip install psutil requests wmi


Core Temp

Jalankan Core Temp → Options → Settings → Logging.

Aktifkan Enable logging on startup.

Pilih folder log, misalnya C:\CoreTempLogs.

Di file monitor_final_fix.py, sesuaikan:

CORETEMP_LOG_DIR = r"C:\CoreTempLogs"


Open/Libre Hardware Monitor (opsional)

Jalankan sebagai Administrator.

Pastikan sensor GPU (load/temperature) muncul.

Telegram

Buat bot via @BotFather, ambil TOKEN.

Dapatkan chat ID via getUpdates.

Sesuaikan di kode:

TELEGRAM_BOT_TOKEN = "TOKEN_BOT_ANDA"
TELEGRAM_CHAT_ID   = "CHAT_ID_ANDA"
TELEGRAM_ENABLED   = True

5. Cara Menggunakan

Jalankan Core Temp (+ HWMonitor bila ingin membaca GPU).

Buka Command Prompt di folder proyek:

python monitor_final_fix.py


Atur parameter di jendela utama:

Batas Load CPU (%)

Batas Suhu CPU (°C)

Batas Load GPU (%)

Batas Suhu GPU (°C)

Jika ingin mengawasi aplikasi:

Klik Refresh daftar aplikasi.

Pilih proses target di combo box (misalnya notepad.exe / game.exe).

Tekan Start Monitoring.

Ketika:

CPU/GPU atau suhu melewati batas → popup + pesan Telegram.

Aplikasi target berhenti → popup + pesan Telegram khusus “aplikasi berhenti”.

Tekan Stop untuk mengakhiri pemantauan.

Klik Lihat Riwayat (Sesi Ini) bila ingin melihat tabel data monitoring saat itu.

6. Log Data

Setiap sesi membuat file baru di folder logs, dengan nama:

log_YYYYMMDD_HHMMSS.csv


Kolom utama:

timestamp

cpu_percent, ram_percent

gpu_load

cpu_temp, gpu_temp

cpu_limit, gpu_load_limit

cpu_temp_limit, gpu_temp_limit

alert_any (1 = ada kondisi lewat batas, 0 = normal)

7. Masalah Umum (Singkat)

Suhu CPU N/A
→ Core Temp belum logging atau folder CORETEMP_LOG_DIR salah.

GPU N/A
→ Open/Libre HWMonitor belum jalan, atau hardware tidak punya sensor yang bisa dibaca.

Tidak ada pesan Telegram
→ Token/chat ID salah, bot belum di-Start, atau tidak ada koneksi internet.
