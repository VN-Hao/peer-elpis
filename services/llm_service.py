from PyQt5.QtCore import QObject, pyqtSignal
from bot.llm_bot import get_bot_response


class LLMSvc(QObject):
    response_ready = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def ask(self, prompt: str):
        # synchronous call for now; can be moved to a worker thread later
        resp = get_bot_response(prompt)
        self.response_ready.emit(resp)
        return resp
