import os
import json
import time
from PyQt5.QtWidgets import QFrame, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView


class AvatarWidget(QFrame):
    """Minimal AvatarWidget restoring safe defaults and APIs used by chat_window.

    Keeps a small, well-tested surface so the rest of the app can import and run.
    """

    def __init__(self, avatar_name: str = None, view_settings: dict | None = None, parent=None):
        super().__init__(parent)
        self.avatar_name = avatar_name
        self.view_settings = view_settings or {}

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.webview = QWebEngineView()
        self.webview.setContextMenuPolicy(Qt.NoContextMenu)
        self.layout().addWidget(self.webview)

        url = self.view_settings.get('avatar_page_url') or 'http://localhost:8080/index.html'
        try:
            self.webview.load(QUrl(url))
        except Exception:
            pass

        try:
            self.webview.page().loadFinished.connect(lambda ok: QTimer.singleShot(50, self._apply_view_settings))
        except Exception:
            pass

    def update_view_settings(self, vs: dict):
        self.view_settings = vs or {}
        try:
            QTimer.singleShot(10, self._apply_view_settings)
        except Exception:
            pass

    def _apply_view_settings(self):
        try:
            external = {
                'zoom': float(self.view_settings.get('zoom', 1.0)),
                'pan_x': float(self.view_settings.get('pan_x', 0) or self.view_settings.get('drag_offset_x', 0)),
                'pan_y': float(self.view_settings.get('pan_y', 0) or self.view_settings.get('drag_offset_y', 0)),
                'previewScaleX': float(self.view_settings.get('preview_original_scale_x')) if self.view_settings.get('preview_original_scale_x') else None,
                'previewScaleY': float(self.view_settings.get('preview_original_scale_y')) if self.view_settings.get('preview_original_scale_y') else None,
                'previewRootWidth': int(self.view_settings.get('preview_root_width')) if self.view_settings.get('preview_root_width') else None,
                'previewRootHeight': int(self.view_settings.get('preview_root_height')) if self.view_settings.get('preview_root_height') else None,
                'view': self.view_settings.get('view_mode', 'upper')
            }
            if self.view_settings.get('debug_avatar', False) or self.view_settings.get('preview_root_width'):
                external['debug'] = True

            inject_code = f"(function(){{ try {{ window._externalViewParams = {json.dumps(external)}; if (typeof window._layoutModel === 'function') {{ window._layoutModel(); }} return true; }} catch(e) {{ return false; }} }})()"

            try:
                self.webview.page().runJavaScript(inject_code, lambda res: None)
            except Exception:
                pass
        except Exception:
            pass

    def speak(self, text: str):
        try:
            js = f"(function(){{ try{{ if(typeof setLipSyncText === 'function') {{ setLipSyncText({json.dumps(text)}) }}; }}catch(e){{}} }})()"
            try:
                self.webview.page().runJavaScript(js)
            except Exception:
                pass
        except Exception:
            pass

    def set_volume(self, v: float):
        try:
            js = f"(function(){{ try{{ if(window.avatarModel && window.avatarModel.setVolume) {{ window.avatarModel.setVolume({float(v)}) }}; }}catch(e){{}} }})()"
            try:
                self.webview.page().runJavaScript(js)
            except Exception:
                pass
        except Exception:
            pass
    # file intentionally ends here (minimal safe implementation)
