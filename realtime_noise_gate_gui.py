import numpy as np
import pyaudio
import tkinter as tk
from tkinter import ttk
import threading
import os
import sys
import pystray
from PIL import Image, ImageDraw

# Set parameters
threshold = 0.02
low_level_noise = 0.001  # Low-level noise to prevent low power state
chunk_size = 1024
sample_format = pyaudio.paInt16  # 16-bit resolution
channels = 2  # Stereo
sample_rate = 44100  # 44.1kHz sampling rate

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open audio stream for output
stream = p.open(format=sample_format,
                channels=channels,
                rate=sample_rate,
                output=True,
                frames_per_buffer=chunk_size)

# Global variables
noise_gate_active = False
run_on_startup = False

# Function to process audio
def process_audio():
    global noise_gate_active
    try:
        while noise_gate_active:
            # Generate low-level noise to prevent low power state
            noise = (np.random.rand(chunk_size) * 2 - 1) * low_level_noise
            noise_audio = (noise * np.iinfo(np.int16).max).astype(np.int16)
            
            # Output low-level noise to speakers/headphones
            stream.write(noise_audio.tobytes())
    except KeyboardInterrupt:
        print("Stopping real-time audio processing.")

# Function to toggle noise gate
def toggle_noise_gate():
    global noise_gate_active
    noise_gate_active = not noise_gate_active
    if noise_gate_active:
        status_label.config(text="Noise Gate: Enabled")
        audio_thread = threading.Thread(target=process_audio)
        audio_thread.start()
    else:
        status_label.config(text="Noise Gate: Disabled")

# Function to toggle run on startup
def toggle_run_on_startup():
    global run_on_startup
    run_on_startup = not run_on_startup
    if run_on_startup:
        enable_startup()
        startup_status_label.config(text="Run on Startup: Enabled")
    else:
        disable_startup()
        startup_status_label.config(text="Run on Startup: Disabled")

# Function to enable run on startup
def enable_startup():
    startup_file = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup\realtime_noise_gate.lnk')
    if not os.path.exists(startup_file):
        create_shortcut(startup_file)

# Function to disable run on startup
def disable_startup():
    startup_file = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup\realtime_noise_gate.lnk')
    if os.path.exists(startup_file):
        os.remove(startup_file)

# Function to create a shortcut
def create_shortcut(target_path):
    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(target_path)
    shortcut.TargetPath = sys.executable
    shortcut.Arguments = os.path.abspath(__file__)
    shortcut.WorkingDirectory = os.path.dirname(os.path.abspath(__file__))
    shortcut.save()

# Function to minimize to tray
def minimize_to_tray():
    window.withdraw()
    create_tray_icon()

# Function to create the tray icon
def create_tray_icon():
    image = Image.new('RGB', (64, 64), color='blue')
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, 48, 48), fill='white')

    icon = pystray.Icon('name', image, 'Real-Time Noise Gate', menu=pystray.Menu(
        pystray.MenuItem('Restore', restore_window),
        pystray.MenuItem('Quit', quit_application)
    ))

    icon.run()

# Function to restore the window
def restore_window(icon, item):
    icon.stop()
    window.deiconify()

# Function to quit the application
def quit_application(icon, item):
    icon.stop()
    on_closing()

# Function to ensure clean exit
def on_closing():
    global noise_gate_active
    noise_gate_active = False
    window.destroy()

# Create the GUI window
window = tk.Tk()
window.title("Real-Time Noise Gate")
window.geometry("400x250")  # Adjusted the window size

# Create the minimize to tray button
minimize_button = ttk.Button(window, text="Minimize to Tray", command=minimize_to_tray)
minimize_button.pack(pady=10)

# Create the toggle button for noise gate
toggle_button = ttk.Button(window, text="Toggle Noise Gate", command=toggle_noise_gate)
toggle_button.pack(pady=10)

# Create a label to show the noise gate status
status_label = tk.Label(window, text="Noise Gate: Disabled")
status_label.pack(pady=10)

# Create the toggle button for run on startup
startup_button = ttk.Button(window, text="Toggle Run on Startup", command=toggle_run_on_startup)
startup_button.pack(pady=10)

# Create a label to show the startup status
startup_status_label = tk.Label(window, text="Run on Startup: Disabled")
startup_status_label.pack(pady=10)

# Add extra padding at the bottom
padding_label = tk.Label(window, text="")
padding_label.pack(pady=10)

# Set the close protocol to ensure clean exit
window.protocol("WM_DELETE_WINDOW", on_closing)

# Run the GUI main loop
window.mainloop()

# Cleanup
stream.stop_stream()
stream.close()
p.terminate()
