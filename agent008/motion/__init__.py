"""Agent-008 v0.2 stage 8C: motion-generation provider boundary.

Everything in this package except provider.submit/poll/fetch is deterministic.
Provider calls are the only non-deterministic, paid step, and they are gated by
an exact-scope spend authorisation with an append-only ledger.
"""
