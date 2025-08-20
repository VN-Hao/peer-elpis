from PyQt5.QtWidgets import QFrame, QVBoxLayout
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from voice.tts_engine import TTSEngine
from PyQt5.QtCore import Qt

class AvatarWidget(QFrame):
    def __init__(self, avatar_name="ANIYA", volume=1.0, rate=150):
        super().__init__()
        self.setStyleSheet("background-color: #ddd; border-radius: 10px;")
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)

        # WebView
        self.webview = QWebEngineView()
        # Request the 'upper' view when embedded so the webview focuses on upper body
        url = f"http://localhost:8080/index.html?avatar={avatar_name}&view=upper"
        self.webview.load(QUrl(url))
        self.layout.addWidget(self.webview)

        # After the page loads, ask it to size the avatar-root and then resize this widget
        self.webview.loadFinished.connect(self._on_page_load)

        # TTS
        self.tts = TTSEngine(volume=volume, rate=rate)

    def _on_page_load(self, ok: bool):
        if not ok:
            return
        # Set an initial avatar width (pixels) so the widget wraps tightly.
        initial_width = 180
        js_set_width = f"(function(){{const r=document.getElementById('avatar-root'); if(!r) return null; r.style.width='{initial_width}px'; return true; }})()"
        def _after_set(_):
            # Query bounding box and resize widget accordingly
            js_get_box = "(function(){const r=document.getElementById('avatar-root'); if(!r) return null; const b=r.getBoundingClientRect(); return {w:Math.round(b.width),h:Math.round(b.height)}; })()"
            def _apply_size(res):
                try:
                    if not res:
                        return
                    w = int(res.get('w', initial_width))
                    h = int(res.get('h', max(240, int(w*4/3))))
                    # Set fixed sizes so the widget and webview wrap tightly around the avatar
                    self.webview.setFixedSize(w, h)
                    self.setFixedSize(w + self.layout.contentsMargins().left() + self.layout.contentsMargins().right(), h + self.layout.contentsMargins().top() + self.layout.contentsMargins().bottom())
                except Exception:
                    pass
            self.webview.page().runJavaScript(js_get_box, _apply_size)
        # apply initial width then size
        self.webview.page().runJavaScript(js_set_width, _after_set)

    def resizeEvent(self, e):
        # Propagate new width to the page so the avatar scales with the widget
        try:
            w = max(80, self.width() - self.layout.contentsMargins().left() - self.layout.contentsMargins().right())
            js = f"(function(){{const r=document.getElementById('avatar-root'); if(!r) return null; r.style.width='{w}px'; const b=r.getBoundingClientRect(); return {{w:Math.round(b.width),h:Math.round(b.height)}}; }})()"
            def _apply(res):
                try:
                    if not res: return
                    new_w = int(res.get('w', w))
                    new_h = int(res.get('h', max(240, int(new_w*4/3))))
                    # resize webview to match the avatar-root size
                    self.webview.setFixedSize(new_w, new_h)
                except Exception:
                    pass
            # run async JS; result handled in callback
            self.webview.page().runJavaScript(js, _apply)
        except Exception:
            pass
        super().resizeEvent(e)

    def speak(self, text):
        self.tts.speak(text)
        self.webview.page().runJavaScript(f"setLipSyncText({repr(text)})")

    def set_volume(self, volume: float):
        self.tts.set_volume(volume)

    def set_rate(self, rate: int):
        self.tts.set_rate(rate)
