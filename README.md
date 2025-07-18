# Frame Conductor

A standalone application for sending sACN frame numbers to Universe 999. This application can be run independently of the Interaction framework.

---

## Port Numbers

- **Backend API (FastAPI):** http://localhost:9000
- **Frontend (React/Vite):** http://localhost:5173

When you run `python main.py`, the backend API will start on port 9000 and the React frontend will start on port 5173. The main script will also open the frontend in your default web browser automatically.

---

## Features

- **Configurable Frame Numbers**: Send frame numbers from 0 to 65535
- **Adjustable Frame Rate**: Set custom FPS (1-120) or use presets (15, 24, 25, 30, 60)
- **Real-time Progress**: Visual progress bar and status updates
- **Configuration Persistence**: Settings are automatically saved and loaded
- **Playback Controls**: Start, pause/resume, and reset functionality

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python main.py
   ```
   - The backend API will be available at http://localhost:9000
   - The web GUI will be available at http://localhost:5173 (opened automatically)

## Project Structure

```
Frame Conductor/
├── main.py              # Application entry point
├── gui.py               # GUI components and user interface
├── sacn_sender.py       # sACN communication logic
├── config_manager.py    # Configuration loading and saving
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── sacn_sender_config.json  # Configuration file (auto-generated)
```

## Modules

### main.py
The application entry point that creates the main window and starts the GUI.

### gui.py
Contains the `FrameConductorGUI` class that handles all user interface components:
- Configuration panel with frame number and FPS settings
- Status display showing current frame and target
- Control buttons (Start, Pause, Reset)
- Progress bar
- Information panel

### sacn_sender.py
Contains the `SACNSender` class that handles sACN communication:
- sACN library initialization and management
- Frame encoding (MSB/LSB in DMX channels 1 and 2)
- Threaded frame sending with configurable frame rate
- Status tracking and callback system

### config_manager.py
Contains the `ConfigManager` class that handles configuration:
- JSON file loading and saving
- Configuration validation
- Default value management

## Configuration

The application automatically creates a `sacn_sender_config.json` file with your settings:

```json
{
  "target_frame": 1000,
  "frame_rate": 30
}
```

## sACN Frame Encoding

Frame numbers are encoded using 2 DMX channels:
- **Channel 1**: MSB (Most Significant Byte)
- **Channel 2**: LSB (Least Significant Byte)
- **Full frame number**: `(MSB << 8) | LSB` (0-65535)

The application sends to **Universe 999** by default.

## Usage

1. **Set Target Frame**: Enter the number of frames to send (0-65535)
2. **Set Frame Rate**: 
   - Type a custom FPS value (1-120)
   - Or click preset buttons (15, 24, 25, 30, 60)
3. **Start Sending**: Click "▶ Start" to begin sending frames
4. **Control Playback**: Use "⏸ Pause" and "🔄 Reset" as needed
5. **Save Settings**: Click "💾 Save Config" to manually save configuration

## Dependencies

- **sacn**: sACN (Streaming ACN) library for DMX over Ethernet
- **tkinter**: GUI framework (included with Python)

## Troubleshooting

### sACN Library Not Available
If you see "sACN library not available", install it with:
```bash
pip install sacn
```

### Configuration Issues
If the configuration file becomes corrupted, delete `sacn_sender_config.json` and restart the application to use default settings.

## Development

This application is designed to be modular and maintainable:
- Each module has a single responsibility
- Clear separation between GUI, business logic, and configuration
- Type hints for better code documentation
- Comprehensive error handling 

# Headless Mode (No GUI)

Frame Conductor can be run in headless (no-GUI) mode for use in terminals or scripts. This mode provides interactive keyboard controls and a real-time progress bar in the terminal.

## Launching Headless Mode

Run with the `--headless` flag:

```
python main.py --headless [--target-frame N] [--fps X]
```

- `--headless` : Run without the GUI, in terminal mode
- `--target-frame N` : Set the target frame number (default: 1000)
- `--fps X` : Set the frame rate in frames per second (default: 30)

## Example

```
python main.py --headless --target-frame 5000 --fps 24
```

## Keyboard Controls (while running)

When running in headless mode, you can control the sender interactively:

- `p` : Play/Pause
- `r` : Reset (sets frame to 0 and pauses)
- `q` : Quit

A real-time progress bar will show:
- Current progress as a percentage
- Current frame and target frame
- Current status (Running, Paused, Reset, Stopped)

## Notes
- The program starts in Paused state. Press `p` to begin sending frames.
- All settings available in the GUI (target frame, FPS) can be set via command-line arguments in headless mode.
- The headless mode uses the same backend logic as the GUI, so results are consistent between both modes. 