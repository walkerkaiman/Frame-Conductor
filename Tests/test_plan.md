# Frame Conductor Test Plan

This document outlines the unit and regression tests for the Frame Conductor application. Tests are organized by feature and indicate whether they use `pytest` (for backend/unit tests) or `playwright` (for GUI/functional tests).

---

## 1. Configuration Management (pytest)
- [ ] Loads default config if no file exists
- [ ] Loads config from file with all fields
- [ ] Loads config from file with missing fields (uses defaults)
- [ ] Saves config with all fields
- [ ] Updates config when a value changes
- [ ] Handles invalid config file gracefully

## 2. sACN Sender Logic (pytest)
- [ ] Initializes with default universe and frame length
- [ ] Starts sending frames at correct rate
- [ ] Pauses and resumes sending
- [ ] Stops sending and cleans up resources
- [ ] Encodes frame number correctly in DMX channels
- [ ] Updates frame callback on each frame
- [ ] Handles invalid universe/frame length/fps values

## 3. Headless Mode (pytest)
- [ ] Starts in paused state
- [ ] Responds to play/pause/reset/quit keyboard commands
- [ ] Progress bar updates in terminal
- [ ] Exits cleanly on keyboard interrupt

## 4. GUI Functionality (playwright)
- [ ] Window opens with correct title and size
- [ ] All config fields display correct initial values
- [ ] Changing a value updates config and persists after restart
- [ ] Start button begins sending frames
- [ ] Pause/Resume button toggles sending
- [ ] Reset button resets progress and state
- [ ] Progress bar and label update as frames are sent
- [ ] Progress label shows current/total/percentage
- [ ] Window cannot be resized
- [ ] GUI closes cleanly on window close or Ctrl+C

## 5. Error Handling (pytest & playwright)
- [ ] Shows error for invalid frame/fps values
- [ ] Shows error for invalid universe/frame length (if applicable)
- [ ] Handles missing sACN library gracefully
- [ ] Handles network errors gracefully

## 6. Regression/Integration (pytest & playwright)
- [ ] Changing config values in GUI updates sender behavior
- [ ] Headless and GUI modes use the same config and produce the same results
- [ ] Progress bar and label are always in sync with sender state
- [ ] No resource leaks or hanging threads after exit

---

**Note:**
- Use `pytest` for backend logic, config, and sender tests.
- Use `playwright` for GUI and end-to-end functional tests.
- Add/expand tests as new features are added. 