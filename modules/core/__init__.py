# -*- coding: utf-8 -*-
"""
modules.core — Utility Duniya Bot ka professional foundation layer (v50)
========================================================================
Ye package bot ke SAARE tools ko teen cheezein deta hai:

  1. `net`     — ek hi jagah se HTTP: timeout + retry + connection pool + SSRF guard
  2. `cache`   — TTL cache (same sawaal par baar-baar API call nahi = fast + API bachat)
  3. `limiter` — per-user rate limit (koi bhi bot ko spam karke API/IP nahi jala sakta)

Design rules:
  • Purane modules ko todna nahi hai — ye sab OPTIONAL helpers hain.
  • Har helper fail-safe hai: kuch bhi tut-ta hai to bot chalta rahega.
  • Koi naya third-party dependency nahi (Render par kuch install nahi karna padega).
"""
from .cache import TTLCache, cached_call, stats as cache_stats
from .limiter import RateLimiter, limiter, check_limit, reset_limit, limiter_stats
from .net import (
    http_get,
    http_get_json,
    http_post,
    http_post_json,
    http_head,
    http_bytes,
    is_safe_url,
    NetError,
)

__all__ = [
    "TTLCache", "cached_call", "cache_stats",
    "RateLimiter", "limiter", "check_limit", "reset_limit", "limiter_stats",
    "http_get", "http_get_json", "http_post", "http_post_json",
    "http_head", "http_bytes", "is_safe_url", "NetError",
]
