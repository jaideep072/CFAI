# How to Setup and Run in PyCharm

This guide provides step-by-step instructions for opening, configuring, running, and testing the Intelligent Pathfinding & Maze Solver project in PyCharm.

---

## Prerequisites

Before starting, make sure you have:
1. **Python 3.10+** installed on your system.
2. **PyCharm (Community or Professional Edition)** installed.

---

## Step 1: Open the Project in PyCharm

1. Launch **PyCharm**.
2. Click **Open** (or go to **File** -> **Open...**).
3. Navigate to the project root directory:
   `C:\Users\jdeep\OneDrive\Desktop\maze_solver`
4. Click **OK** to load the project.

---

## Step 2: Configure a Virtual Environment

It is highly recommended to run the project within a clean virtual environment (`.venv`) to isolate dependencies.

1. Go to **File** -> **Settings** (or `Ctrl+Alt+S`). On macOS, go to **PyCharm** -> **Preferences**.
2. In the left panel, navigate to **Project: maze_solver** -> **Python Interpreter**.
3. If no interpreter is set up:
   - Click **Add Interpreter** -> **Add Local Interpreter...**
   - Choose **Virtualenv Environment**.
   - Set the **Base interpreter** to your installed Python version (e.g., Python 3.11 or 3.12).
   - Keep the default location (usually a `.venv` directory inside the project root).
   - Click **OK**.
4. PyCharm will create the virtual environment and register it.

---

## Step 3: Install Required Dependencies

The web-based visualizer relies on **Flask**.

1. Open the PyCharm terminal at the bottom of the window (**Terminal** tab or press `Alt+F12`).
2. Verify that the virtual environment is activated (you should see `(.venv)` at the beginning of the terminal command line prompt).
3. Install the project package requirements:
   ```bash
   pip install flask
   ```

---

## Step 4: Configure and Run the Applications

The project includes two interfaces:
1. **Web-Based Visualizer** (`app.py`) - The premium interactive GUI.
2. **Console CLI Interface** (`main.py`) - The command-line utility.

### Running the Web Visualizer (`app.py`)
1. In the PyCharm project directory tree (left panel), right-click on [app.py](file:///c:/Users/jdeep/OneDrive/Desktop/maze_solver/app.py).
2. Select **Run 'app'** from the context menu (or press `Ctrl+Shift+F10`).
3. PyCharm will launch the Flask web server. In the run output console, you will see:
   `* Running on http://127.0.0.1:5000`
4. Open your browser and navigate to `http://127.0.0.1:5000` to interact with the visualizer.

### Running the Console Interface (`main.py`)
1. In the project directory tree, right-click on [main.py](file:///c:/Users/jdeep/OneDrive/Desktop/maze_solver/main.py).
2. Select **Run 'main'** (or press `Ctrl+Shift+F10`).
3. PyCharm will launch the command-line menu. You can enter commands directly into the PyCharm run console (e.g., configure speed, solve via BFS/DFS, view PEAS declaration, run benchmarks, etc.).

---

## Step 5: Configure and Run Unit Tests

PyCharm integrates seamlessly with Python's built-in testing frameworks.

1. In the project directory tree, expand the `tests` directory and locate [test_all.py](file:///c:/Users/jdeep/OneDrive/Desktop/maze_solver/tests/test_all.py).
2. Right-click on [test_all.py](file:///c:/Users/jdeep/OneDrive/Desktop/maze_solver/tests/test_all.py) and select **Run 'Python tests in test_all.py'**.
3. PyCharm will run the unit test cases and display a visual green/red progress bar in the **Run** window, validating all pathfinding search and CSP scheduling constraints.
