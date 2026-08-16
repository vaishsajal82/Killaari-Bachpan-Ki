"""
rate_limit.py — a single shared slowapi Limiter instance, applied per-route
in the routers below rather than globally, so limits can be tuned per
endpoint (a login attempt and a public GET of the events list are very
different in how abusable they are).

Keys by client IP (get_remote_address). In-memory storage — fine for a
single-instance deployment like this one; if this app is ever scaled to
multiple backend instances behind a load balancer, swap the storage_uri to
a shared Redis instance (slowapi supports this via the `storage_uri` param)
so limits are enforced consistently across instances instead of each
instance tracking its own separate counts.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
