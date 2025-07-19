# Frame Conductor - Development Guide

This document provides comprehensive guidance for developers working on the Frame Conductor project.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Development Setup](#development-setup)
3. [Coding Standards](#coding-standards)
4. [Testing](#testing)
5. [API Documentation](#api-documentation)
6. [Troubleshooting](#troubleshooting)
7. [Contributing](#contributing)

## Architecture Overview

### System Architecture

Frame Conductor uses a modern web architecture with:

- **Backend**: FastAPI (Python) - RESTful API + WebSocket server
- **Frontend**: React (TypeScript) - Modern web interface
- **Communication**: sACN (Streaming ACN) - DMX over Ethernet
- **Build System**: Vite - Fast development and building

### Component Structure

```
Frame-Conductor/
├── main.py                 # Application entry point
├── api_server.py           # FastAPI backend server
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── App.tsx        # Main React component
│   │   ├── App.css        # Component styles
│   │   └── main.tsx       # React entry point
│   ├── package.json       # Frontend dependencies
│   ├── vite.config.ts     # Vite configuration
│   └── tests/             # Frontend tests
├── utils/
│   ├── sacn_sender.py     # sACN communication logic
│   ├── config_manager.py  # Configuration management
│   └── headless_utils.py  # Headless mode utilities
├── Tests/                 # Backend test suite
├── requirements.txt       # Python dependencies
└── README.md             # User documentation
```

### Data Flow

1. **Configuration**: Frontend ↔ Backend via REST API
2. **Control**: Frontend → Backend via REST API
3. **Progress**: Backend → Frontend via WebSocket
4. **sACN**: Backend → DMX devices via sACN protocol

## Development Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- Git

### Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd Frame-Conductor

# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Development Mode

```bash
# Terminal 1: Start backend
python main.py

# Terminal 2: Start frontend (optional, main.py starts it automatically)
cd frontend
npm run dev
```

### Environment Variables

Create a `.env` file in the root directory for local development:

```env
# Backend configuration
BACKEND_PORT=9000
FRONTEND_PORT=5173
LOG_LEVEL=INFO

# sACN configuration
DEFAULT_UNIVERSE=999
DEFAULT_FRAME_LENGTH=512
```

## Coding Standards

### Python (Backend)

#### Code Style
- Follow PEP 8 style guide
- Use type hints for all function parameters and return values
- Maximum line length: 88 characters (Black formatter)
- Use f-strings for string formatting

#### Documentation
- All modules must have docstrings
- All functions must have docstrings with Args/Returns sections
- Use Google-style docstrings

#### Example
```python
def process_config(config_data: Dict[str, Any]) -> bool:
    """
    Process configuration data and validate it.
    
    Args:
        config_data: Configuration dictionary to process
        
    Returns:
        bool: True if processing was successful
        
    Raises:
        ValueError: If configuration is invalid
    """
    # Implementation here
    pass
```

### TypeScript (Frontend)

#### Code Style
- Use TypeScript strict mode
- Follow ESLint configuration
- Use functional components with hooks
- Prefer arrow functions for components

#### Documentation
- Use JSDoc comments for components and functions
- Document all props interfaces
- Include usage examples

#### Example
```typescript
/**
 * Configuration panel component
 * 
 * @param props - Component props
 * @param props.config - Current configuration
 * @param props.onSave - Save callback function
 */
interface ConfigPanelProps {
  config: ConfigData;
  onSave: (config: ConfigData) => void;
}

const ConfigPanel: React.FC<ConfigPanelProps> = ({ config, onSave }) => {
  // Implementation here
};
```

### Error Handling

#### Backend
- Use proper exception handling with specific exception types
- Log errors with appropriate levels (ERROR, WARNING, INFO)
- Return meaningful error messages to clients
- Use HTTP status codes correctly

#### Frontend
- Use try-catch blocks for async operations
- Display user-friendly error messages
- Handle network errors gracefully
- Implement error boundaries for React components

## Testing

### Backend Testing

#### Running Tests
```bash
# Run all tests
python -m pytest Tests/

# Run specific test file
python -m pytest Tests/test_api.py

# Run with coverage
python -m pytest Tests/ --cov=. --cov-report=html
```

#### Test Structure
- Unit tests for individual functions
- Integration tests for API endpoints
- Mock external dependencies (sACN library)

#### Example Test
```python
import pytest
from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)

def test_get_config():
    """Test configuration retrieval endpoint."""
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "total_frames" in data
    assert "frame_rate" in data
```

### Frontend Testing

#### Running Tests
```bash
cd frontend

# Run unit tests
npm test

# Run Playwright tests
npx playwright test

# Run with coverage
npm test -- --coverage
```

#### Test Structure
- Unit tests for React components
- Integration tests with Playwright
- Test user interactions and API calls

#### Example Test
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';

test('renders configuration panel', () => {
  render(<App />);
  expect(screen.getByText('Configuration')).toBeInTheDocument();
  expect(screen.getByLabelText('Total Frames:')).toBeInTheDocument();
});
```

## API Documentation

### REST Endpoints

#### GET /api/config
Retrieve current configuration.

**Response:**
```json
{
  "total_frames": 1000,
  "frame_rate": 30,
  "universe": 999,
  "frame_length": 512
}
```

#### POST /api/config
Update configuration.

**Request:**
```json
{
  "total_frames": 2000,
  "frame_rate": 60
}
```

**Response:**
```json
{
  "success": true
}
```

#### POST /api/start
Start frame transmission.

**Response:**
```json
{
  "success": true
}
```

#### POST /api/pause
Pause/resume transmission.

**Response:**
```json
{
  "success": true
}
```

#### POST /api/reset
Reset transmission.

**Response:**
```json
{
  "success": true
}
```

### WebSocket

#### Endpoint: ws://[HOST]:9000/ws/progress

**Progress Updates:**
```json
{
  "frame": 150,
  "total_frames": 1000,
  "status": "Sending frames...",
  "percent": 15
}
```

**Configuration Updates:**
```json
{
  "type": "config_update",
  "config": {
    "total_frames": 2000,
    "frame_rate": 60,
    "universe": 999,
    "frame_length": 512
  }
}
```

## Troubleshooting

### Common Issues

#### Backend Issues

**sACN Library Not Available**
```bash
pip install sacn
```

**Port Already in Use**
```bash
# Check what's using the port
netstat -ano | findstr :9000  # Windows
lsof -i :9000                 # macOS/Linux

# Kill the process or change the port
```

**Configuration File Issues**
```bash
# Delete corrupted config
rm sacn_sender_config.json
# Restart application
```

#### Frontend Issues

**npm Install Fails**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Vite Dev Server Issues**
```bash
# Check if port is available
netstat -ano | findstr :5173  # Windows
lsof -i :5173                 # macOS/Linux
```

### Debug Mode

Enable debug logging by setting environment variables:

```bash
export LOG_LEVEL=DEBUG
python main.py
```

### Network Issues

**Firewall Configuration**
- Ensure ports 9000 and 5173 are open
- Check Windows Firewall settings
- Verify network interface binding

**CORS Issues**
- Check browser console for CORS errors
- Verify backend CORS configuration
- Ensure frontend is accessing correct backend URL

## Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
   - Follow coding standards
   - Add tests for new functionality
   - Update documentation
4. **Test your changes**
   ```bash
   # Backend tests
   python -m pytest Tests/
   
   # Frontend tests
   cd frontend && npm test
   ```
5. **Commit your changes**
   ```bash
   git commit -m "feat: add new feature description"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a pull request**

### Commit Message Format

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes

### Code Review Process

1. **Automated Checks**
   - Tests must pass
   - Code style checks must pass
   - No merge conflicts

2. **Manual Review**
   - Code quality review
   - Functionality testing
   - Documentation review

3. **Approval**
   - At least one approval required
   - All comments must be resolved

### Release Process

1. **Version Bumping**
   - Update version in `package.json` and `api_server.py`
   - Create version tag

2. **Testing**
   - Run full test suite
   - Manual testing on different platforms

3. **Documentation**
   - Update README.md
   - Update API documentation
   - Create release notes

4. **Deployment**
   - Create GitHub release
   - Update installation instructions

### Support

For development questions or issues:

1. Check this documentation
2. Search existing issues
3. Create a new issue with detailed information
4. Join the development discussion

---

**Note**: This development guide is a living document. Please update it as the project evolves. 