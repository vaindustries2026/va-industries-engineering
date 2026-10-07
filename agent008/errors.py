class FailClosed(Exception):
    """Raised whenever an input, contract or output check fails.

    Agent-008 never degrades, guesses or substitutes: any failure stops the run.
    The first argument is a stable reason code; the rest is detail.
    """

    def __init__(self, code, detail=''):
        self.code = code
        self.detail = detail
        super().__init__(f'{code}: {detail}' if detail else code)
