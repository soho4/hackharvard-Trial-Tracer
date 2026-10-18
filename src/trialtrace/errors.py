"""Structured failures; row uncertainty is represented in results instead."""


class InputError(ValueError):
    def __init__(self, code, message, **context):
        super().__init__(message)
        self.code = code
        self.context = context

    def diagnostic(self):
        return {"code": self.code, "message": str(self), **self.context}
