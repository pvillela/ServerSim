"""
Common settings and initializations for tests
"""

from hypothesis import settings


settings.register_profile("pv", settings(
    timeout = -1,
    database_file = None,
    derandomize = True,
    max_examples = 50,  # default = 200
    # verbosity = Verbosity.verbose  # useless
))

settings.load_profile("pv")
