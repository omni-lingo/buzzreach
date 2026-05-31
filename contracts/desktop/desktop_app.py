"""
Cross-module contract for DESKTOP-001: Electron Desktop App.

Defines the data structures shared between the desktop app
and the backend API. The desktop app reuses the same API
endpoints as the web frontend — these contracts ensure
compatibility with the notification strategy switch
(native vs browser push).
"""

from dataclasses import dataclass
from enum import Enum


class DesktopPlatform(Enum):
    """Supported desktop platforms."""

    WINDOWS = "win32"
    MACOS = "darwin"
    LINUX = "linux"


class NotificationStrategy(Enum):
    """How the desktop app delivers notifications.

    NATIVE uses OS-level notifications (faster, richer).
    PUSH uses the same push notification path as mobile.
    """

    NATIVE = "native"
    PUSH = "push"


@dataclass
class DesktopAppInfo:
    """Desktop app registration data sent to backend on launch."""

    app_version: str
    platform: DesktopPlatform
    notification_strategy: NotificationStrategy
    electron_version: str


@dataclass
class DesktopUpdateInfo:
    """Update information returned by the update server."""

    available: bool
    version: str
    download_url: str
    release_notes: str
