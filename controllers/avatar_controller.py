from PyQt5.QtCore import QObject

class AvatarController(QObject):
    """A thin controller that centralizes avatar widget interactions.

    It wraps an AvatarWidget instance and provides a stable interface for the rest
    of the app (speak, set_volume, set_view, set_lip_sync).
    """
    def __init__(self, avatar_widget):
        super().__init__()
        self.avatar_widget = avatar_widget

    def speak(self, text: str):
        try:
            self.avatar_widget.speak(text)
        except Exception:
            pass

    def set_volume(self, v: float):
        try:
            self.avatar_widget.set_volume(v)
        except Exception:
            pass

    def set_lip_sync(self, text: str):
        # Keep a single place to call the page JS
        try:
            self.avatar_widget.webview.page().runJavaScript(f"setLipSyncText({repr(text)})")
        except Exception:
            pass

    def set_view(self, mode: str):
        # future: tell page to switch view mode
        pass
