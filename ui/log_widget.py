"""
ui/log_widget.py — System event log widget with timestamps
===========================================================

This module implements the LogWidget: a read-only text area that
chronologically records all relevant system events
(initialization, errors, warnings, session end, etc.).

Responsibility:
    Receive text messages from any application component and display
    them with a "HH:MM:SS" timestamp in system log format.
    Automatically scrolls to always show the most recent message.

Why a log instead of QMessageBox for each event?
    QMessageBox blocks the program waiting for the user's click.
    In real time (~30 FPS processing), any blocking would be catastrophic —
    frames would be lost and the camera would go unread.
    The LogWidget records events without interrupting any processing.

Who uses the LogWidget:
    - MainWindow: session events ("Session started", "Session ended").
    - CameraWorker (via camera_error signal): camera errors.
    - ProcessingWorker (via processing_error signal): processing errors.
    - Any future module that needs to communicate events to the clinician.

Integration in MainWindow:
    self.log_widget = LogWidget()
    camera_worker.camera_error.connect(
        lambda msg: self.log_widget.log(f"CAMERA ERROR: {msg}")
    )
    processing_worker.processing_error.connect(self.log_widget.log)
"""

from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import QSizePolicy, QTextEdit, QWidget


class LogWidget(QTextEdit):
    """
    System event log area with automatic timestamps.

    Inherits from QTextEdit to leverage native support for multi-line text,
    automatic scrolling, and text selection (useful for copying error messages).
    Default behavior is overridden only to enforce read-only mode
    and apply the dark theme visual style.

    Features:
        - Read-only (the user cannot edit).
        - Automatic scroll to the bottom on new messages.
        - Monospaced font for consistent timestamp alignment.
        - Maximum height of 120px to avoid dominating the window layout.
        - Each line follows the format: "HH:MM:SS  message"

    Example content:
        14:35:12  Application started.
        14:35:15  Session started — Patient: John Doe | Hand: Right | Session 1
        14:36:02  CAMERA ERROR: Camera lost after 10 invalid frames.
        14:36:03  Session ended. Duration: 00:00:48
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initializes the LogWidget with visual style and behavior settings.

        Parameters:
            parent: Qt parent widget (optional). Usually the layout container.
        """
        super().__init__(parent)

        # Read-only: the clinician can view and copy, but not edit.
        # Accidental editing could erase important error messages.
        self.setReadOnly(True)

        # Maximum height of 120px — the log should not dominate the layout.
        # With font size 9, each line is ~14px tall:
        # 120px / 14px ≈ 8 simultaneously visible lines.
        self.setMaximumHeight(120)

        # Size policy: expands horizontally, height controlled by the max.
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )

        # Monospaced font for timestamp alignment.
        # Consolas: available on Windows. Courier New: universal fallback.
        # Size 9: compact enough for 8 lines in 120px height.
        mono_font = QFont()
        mono_font.setFamilies(["Consolas", "Courier New", "Monospace"])
        mono_font.setPointSize(9)
        self.setFont(mono_font)

        # Visual style compatible with the application's dark theme.
        # Near-black background (#0d1117) for maximum contrast with gray text.
        # Subtle border to demarcate the log area without excessive attention.
        self.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117;
                color: #94a3b8;
                border: 1px solid #1e293b;
                border-radius: 4px;
                padding: 4px 6px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
            }
            QScrollBar:vertical {
                background: #0d1117;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                border-radius: 3px;
                min-height: 16px;
            }
            QScrollBar::handle:vertical:hover {
                background: #38bdf8;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Initial message to confirm the widget is functional.
        # Also serves as visual validation during development.
        self.log("Digital Goniometry system initialized.")

    # =========================================================================
    # PUBLIC INTERFACE
    # =========================================================================

    def log(self, message: str) -> None:
        """
        Adds a message to the log with the current time timestamp.

        Formats the message as "HH:MM:SS  message" and appends it to the
        current content. Automatically scrolls to show the new entry.

        This method is safe to connect directly to pyqtSignal(str),
        such as camera_error and processing_error signals from workers.
        Qt ensures that signal-invoked calls always happen on the main thread
        (where the widget lives), even if emitted from a QThread.

        Parameters:
            message: Text of the message to log. Can contain any string,
                     including error messages with technical details.
        """
        # Get the current timestamp in HH:MM:SS format.
        # Date is not included because all log entries are from the same
        # program session. The date can be inferred from the CSV filename.
        timestamp: str = datetime.now().strftime("%H:%M:%S")

        # Full line: timestamp + two spaces + message.
        # Two spaces (not a tab) for consistent visual separation in monospaced fonts
        # where tab width may vary depending on OS settings.
        log_line: str = f"{timestamp}  {message}"

        # Use append() instead of setPlainText() to ADD to existing content
        # without erasing the history.
        self.append(log_line)

        # Scroll to the bottom to show the most recent message.
        self._scroll_to_bottom()

    def log_error(self, message: str) -> None:
        """
        Adds an error message to the log with a visual highlight prefix.

        Variant of log() for critical errors. Automatically prefixes with
        "❌ ERROR:" for immediate visual distinction — the clinician can identify
        errors without reading line by line.

        Parameters:
            message: Error description. E.g.: "Camera lost after 10 frames."
        """
        self.log(f"❌ ERROR: {message}")

    def log_warning(self, message: str) -> None:
        """
        Adds a warning message to the log with an alert prefix.

        For situations that are not fatal errors but deserve attention:
        e.g., degraded performance, data outside the expected clinical range.

        Parameters:
            message: Warning description.
        """
        self.log(f"⚠️ WARNING: {message}")

    def log_success(self, message: str) -> None:
        """
        Adds a positive confirmation message to the log.

        For important successful events: session started, PDF generated,
        CSV exported. Visually distinguished from common informational messages.

        Parameters:
            message: Description of the successful event.
        """
        self.log(f"✅ {message}")

    def clear_log(self) -> None:
        """
        Clears all log content and inserts a reset message.

        Called by MainWindow when starting a new session, so that the previous
        session's log does not pollute the new one. The reset message
        ensures the log never appears completely empty — avoiding ambiguity
        between "log cleared" and "no event has occurred".
        """
        # clear() clears all QTextEdit content at once.
        self.clear()
        self.log("Log reset for new session.")

    # =========================================================================
    # INTERNAL METHODS
    # =========================================================================

    def _scroll_to_bottom(self) -> None:
        """
        Scrolls the vertical scrollbar to show the last line of the log.

        Uses a QTextCursor positioned at the End of the document to ensure
        scrolling goes to the REAL end of the content, not just an approximate
        position calculated by the scrollbar.

        Why QTextCursor instead of verticalScrollBar().setValue(maximum())?
            The scrollbar's maximum() may be stale when the new text was just
            inserted — Qt has not yet recalculated the layout.
            QTextCursor.End is always the real end of the document.
        """
        # Move the cursor to the end of the document.
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # Set the modified cursor on the widget — this causes the scroll.
        self.setTextCursor(cursor)

        # ensureCursorVisible() guarantees the cursor (now at the end) is
        # within the visible area of the widget, scrolling if necessary.
        self.ensureCursorVisible()
