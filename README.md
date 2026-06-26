# Digital Hand Goniometry

## Overview
This project is an automated clinical tool for digital hand goniometry. It utilizes a regular webcam and computer vision (MediaPipe Hands) to track finger joints in real time and compute the Total Active Motion (TAM) for all five digits simultaneously. 

Designed to provide continuous, contact-free functional assessment, the system replaces manual goniometers with an objective, data-driven approach. It features real-time plotting, live clinical metrics computation (rom, angular velocity, and movement frequency), and exports results automatically to CSV. Additionally, it generates a comprehensive, double-blind-ready post-session PDF report with automated clinical classification based on ASSH (American Society for Surgery of the Hand) guidelines.

## Prerequisites
- Windows 10/11 (Camera pipeline is optimized for DirectShow `CAP_DSHOW` on Windows)
- Python 3.9 or higher
- A standard webcam

## Installation Guide

1. **Clone or Download the Repository**
   Make sure you are in the project's root directory (`anonimo`).

2. **Create a Virtual Environment (Recommended)**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Core dependencies include: `PyQt6`, `opencv-python`, `mediapipe`, `numpy`, `pyqtgraph`, `fpdf2`, `matplotlib`.*

## How to Run

1. **Start the Application**
   Run the main entry point script from your terminal:
   ```bash
   python app_pyqt.py
   ```

2. **Using the System**
   - **Patient Form**: Fill in the patient's full name (mandatory), select the evaluated hand, and specify the session number.
   - **Start Session**: Click `▶ Start Session`. The webcam will turn on, and real-time goniometric analysis will begin. You will see the hand landmarks mapped over the video feed and live TAM charts.
   - **End Session**: Click `■ End Session` when the assessment is over. The data will be safely written to a CSV file in the `logs/` directory.
   - **Generate Report**: Once stopped, click `📄 Generate PDF Report` to create a clinical summary.

## License
MIT License

Copyright (c) 2026 Anonymous Authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
