"""Local educational password check.

The guess list is the original CLI wordlist. Callers cannot replace it,
point it at another host, or receive the matched secret.
"""

DEMO_GUESSES = ("1234", "admin", "password", "test", "bank123", "abcd")
MAX_DEMO_ATTEMPTS = len(DEMO_GUESSES)
