# Autonomous AI Agent for Controlling Computer UI

![Screenshot 2025-03-14 210951](https://github.com/user-attachments/assets/0d1e4f54-99e4-4cf7-8550-683a9dcb8d8e)
![Screenshot 2025-03-14 211007](https://github.com/user-attachments/assets/ab625a4d-e07a-4edc-8f7d-e9a4e7e9a340)

## Overview

The Autonomous AI Agent enables AI to interact with your computer on your behalf. Built with Python, Flask, and Gemini AI, it provides a user-friendly interface for AI-assisted computer control and automation.

## Features

- **Real-time Screen Analysis**: Captures and analyzes your screen to understand the UI elements
- **AI-Powered Assistance**: Leverages Google's Gemini model to interpret commands and context
- **Element Detection**: Identifies elements on screen using computer vision
- **Chat Interface**: Easy-to-use chat interface with conversation history
- **Python Code Execution**: Execute custom Python scripts directly from the agent

## Demo

[![Watch the demo](https://img.youtube.com/vi/nmJ8wzfnIcc/maxresdefault.jpg)](https://youtu.be/nmJ8wzfnIcc)

## Installation

### Prerequisites

- Python 3.8+
- Windows OS (Currently only supports Windows)

### Setup

1. Clone the repository:
   ```powershell
   git clone https://github.com/piyush-suteri/Autonomous-AI-Agent.git
   cd ai_agent
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Create a Google API key for Gemini at [Google AI Studio](https://aistudio.google.com). Set it as an environment variable on your system named GEMINI_API_KEY.

4. Run the application:
   ```powershell
   python main.py
   ```

## Usage

1. Start the application
2. The AI Agent window will appear on the left side of your screen
3. Type your instructions in the chat interface
4. The agent will analyze your screen, interpret your commands, and perform actions

## How the AI System Works

This AI system automates computer tasks by mimicking human interaction with the graphical user interface (GUI). Here's a breakdown of its operational flow:

### 1. Task Initialization

The process begins when you, the user, specify a task. The AI then formulates a preliminary plan to execute this task.

### 2. Automation Loop

If the task requires interacting with the computer, the AI enters an automated loop. Within this loop, it dynamically generates and executes **Python code** to perform actions. It primarily leverages **PyAutoGUI**, a GUI automation library, to simulate:

* **Keyboard input** (e.g., typing text)
* **Mouse actions** (e.g., clicking, dragging, and movement)

Beyond PyAutoGUI, the system can utilize other Python libraries to perform a wide range of operations, including:

* **File operations** (e.g., creating, reading, or deleting files)
* **Terminal command execution** (e.g., running command-line tools)
* And many more complex interactions.

### 3. Action Verification and Decision Making

After each action is performed, the system captures a **screenshot** of the GUI. This screenshot is then processed and sent to **Gemini**, which acts as the system's "eyes" and "brain." Gemini analyzes the current interface, verifies the outcome of the previous action, and determines the most appropriate next step. This iterative loop of action, verification, and decision-making continues until the entire task is successfully completed.

### 4. GUI Interaction Enhancement

While the AI can interact with any GUI element, Gemini on its own isn't precise enough for exact positioning. To overcome this, the system employs **image processing** techniques on the screenshots, specifically **edge detection**. This allows it to accurately identify and delineate elements like buttons, text fields, and other interactive components.

Each detected element is then annotated with a **numbered bounding box**. Gemini identifies the specific element it needs to interact with by referencing its assigned number. This number is then passed to a function from a custom library, which returns the precise **coordinates** of that element. These coordinates are then fed into PyAutoGUI, enabling highly accurate and targeted interactions with the GUI.

## Architecture

The project is organized into several components:

- **Frontend**: Web-based chat interface built with HTML, CSS, and JavaScript
- **Backend**: Flask server with SocketIO for real-time communication
- **Element Detection**: Computer vision system to identify UI elements
- **Agent Functions**: Core functionality for screen interaction, code execution, etc.

## Development

### Project Structure

```
ai_agent/
├── assets/                # System prompt
├── logs/                  # Application logs
├── src/
│   ├── backend/           # Flask API and backend logic
│   │   └── utils/         # Utility modules
│   ├── element_detection/ # Screen analysis and UI element detection
│   └── frontend/          # Web interface
├── user_data/             # User chat history and data
├── main.py                # Application
└── requirements.txt       # Python dependencies
```

## Contributing

Contributions are welcome! Feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.


## Connect

- YouTube: [@piyushsuteri](https://youtube.com/@piyushsuteri)
- LinkedIn: [Piyush Suteri](https://www.linkedin.com/in/piyush-suteri/)
- GitHub: [piyush-suteri](https://github.com/piyush-suteri) 
