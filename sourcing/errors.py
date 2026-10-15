class FailClosed(Exception):
    """Raised whenever a class, rights, integrity or contract check fails.

    Procurement never guesses a licence, substitutes a source or retries into a
    different item: any failure stops the run. The first argument is a stable
    reason code; the rest is detail.
    """

    def __init__(self, code, detail=''):
        self.code = code
        self.detail = detail
        super().__init__(f'{code}: {detail}' if detail else code)
