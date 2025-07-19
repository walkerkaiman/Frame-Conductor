# Frame Conductor

A modern web application for sending sACN frame numbers to Universe 999. Built with React frontend and FastAPI backend, this application provides real-time control and monitoring of sACN frame transmission with network accessibility.

---

## Features

- **Modern Web Interface**: React-based GUI accessible from any web browser
- **Network Accessibility**: Accessible from any device on your local network
- **Network Singleton Protection**: Only one instance can run per network
- **Real-time Synchronization**: Multiple browsers stay in sync automatically
- **Configurable Frame Numbers**: Send frame numbers from 0 to 65535
- **Adjustable Frame Rate**: Set custom FPS (1-120)
- **Real-time Progress**: Live progress updates via WebSocket
- **Configuration Persistence**: Settings are automatically saved and loaded
- **Playback Controls**: Start, pause/resume, and reset functionality
- **Multi-browser Support**: Control from multiple devices simultaneously

## Quick Start

1. **Install Dependencies**:
   ```bash
   # Backend dependencies
   pip install -r requirements.txt
   
   # Frontend dependencies
   cd frontend
   npm install
   ```

2. **Run the Application**:
   ```bash
   python main.py
   ```
   
   This will:
   - Start the FastAPI backend on port 9000
   - Start the React frontend on port 5173
   - Open the web interface in your default browser
   - Display network access URLs for other devices

## Network Access

The application is designed for network accessibility:

- **Local Access**: http://localhost:5173
- **Network Access**: http://[YOUR_IP]:5173 (displayed when starting)
- **Backend API**: http://[YOUR_IP]:9000

Other computers on your local network can access the interface using the displayed network URL.

## Project Structure

```
Frame-Conductor/
├── main.py                 # Application entry point
├── api_server.py           # FastAPI backend server
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── App.tsx        # Main React component
│   │   └── ...
│   ├── package.json       # Frontend dependencies
│   └── vite.config.ts     # Vite configuration
├── utils/
│   ├── sacn_sender.py     # sACN communication logic
│   ├── config_manager.py  # Configuration management
│   └── headless_utils.py  # Headless mode utilities
├── Tests/                 # Backend test suite
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Architecture

### Backend (FastAPI)
- **Port**: 9000
- **Framework**: FastAPI with uvicorn
- **Features**:
  - RESTful API endpoints for configuration and control
  - WebSocket for real-time progress updates
  - sACN frame transmission management
  - Configuration persistence

### Frontend (React)
- **Port**: 5173
- **Framework**: React with TypeScript
- **Build Tool**: Vite
- **Features**:
  - Modern, responsive web interface
  - Real-time WebSocket communication
  - Network-accessible design
  - Multi-browser synchronization

## API Endpoints

### HTTP Endpoints
- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration
- `POST /api/start` - Start frame transmission
- `POST /api/pause` - Pause/resume transmission
- `POST /api/reset` - Reset to frame 0

### WebSocket
- `ws://[HOST]:9000/ws/progress` - Real-time progress updates

## Configuration

The application automatically creates a `sacn_sender_config.json` file:

```json
{
  "total_frames": 1000,
  "frame_rate": 30,
  "universe": 999,
  "frame_length": 512
}
```

## sACN Frame Encoding

Frame numbers are encoded using 2 DMX channels:
- **Channel 1**: MSB (Most Significant Byte)
- **Channel 2**: LSB (Least Significant Byte)
- **Full frame number**: `(MSB << 8) | LSB` (0-65535)

The application sends to **Universe 999** by default.

## Usage

1. **Start the Application**:
   ```bash
   python main.py
   ```
   
   **Note**: Only one instance of Frame Conductor can run on your network at a time. If another instance is detected, the application will exit with an error.

2. **Access the Interface**: Open the web interface in any browser
3. **Configure Settings**:
   - Set Total Frames (1-65535)
   - Set Frame Rate (1-120 fps)
   - Click "💾 Save Config" to save settings
4. **Control Transmission**:
   - Click "▶ Start" to begin sending frames
   - Use "⏸ Pause" to pause/resume
   - Use "🔄 Reset" to reset to frame 0
5. **Monitor Progress**: Watch real-time progress bar and frame counter

### Advanced Options

**Disable Network Singleton Protection** (for development/testing):
```bash
python main.py --no-singleton
```

**Other Command Line Options**:
```bash
python main.py --target-frame 2000 --fps 60
```

## Network Singleton Protection

Frame Conductor includes a network-wide singleton mechanism to prevent multiple instances from running simultaneously:

### How It Works
- **UDP Broadcasting**: Uses UDP broadcasts on port 9001 to detect other instances
- **Instance Detection**: Checks for existing instances before starting
- **Heartbeat Messages**: Sends periodic heartbeats to announce presence
- **Automatic Exit**: Exits gracefully if another instance is detected

### Benefits
- **Prevents Conflicts**: Avoids multiple sACN transmissions on the same network
- **Resource Management**: Ensures only one instance uses network resources
- **Clear Error Messages**: Provides clear feedback when another instance is running

### Disabling Protection
For development or testing, you can disable the singleton protection:
```bash
python main.py --no-singleton
```

## Multi-browser Features

- **Real-time Sync**: Configuration changes sync across all connected browsers
- **Shared Control**: Any browser can control the frame transmission
- **Live Updates**: Progress updates appear on all connected devices
- **Network Access**: Access from any device on your local network

## Dependencies

### Backend
- **fastapi**: Modern web framework
- **uvicorn**: ASGI server
- **sacn**: sACN (Streaming ACN) library for DMX over Ethernet
- **websockets**: WebSocket support

### Frontend
- **react**: UI framework
- **typescript**: Type safety
- **vite**: Build tool and dev server
- **tailwindcss**: Styling

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm

### Setup
```bash
# Clone the repository
git clone [repository-url]
cd Frame-Conductor

# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..

# Run the application
python main.py
```

## Development

### Running in Development Mode
```bash
# Terminal 1: Backend
python main.py

# Terminal 2: Frontend (optional, main.py starts it automatically)
cd frontend
npm run dev
```

### Testing
```bash
# Backend tests
python -m pytest Tests/

# Frontend tests
cd frontend
npm test
```

## Troubleshooting

### sACN Library Not Available
```bash
pip install sacn
```

### Network Access Issues
- Ensure your firewall allows connections on ports 5173 and 9000
- Check that the application is binding to `0.0.0.0` (not just localhost)

### Configuration Issues
Delete `sacn_sender_config.json` and restart to use default settings.

## Headless Mode

For terminal-only operation:

```bash
python main.py --headless [--target-frame N] [--fps X]
```

- `--headless`: Run without web interface
- `--target-frame N`: Set target frame number
- `--fps X`: Set frame rate

## License

[Add your license information here] 