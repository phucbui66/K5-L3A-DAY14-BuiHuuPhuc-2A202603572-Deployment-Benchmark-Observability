import hashlib
import time
import uuid
from fastapi import HTTPException
from app.config import settings
from app.redis_client import r

# The Lua script makes the sliding window atomic across workers.
_SCRIPT = """
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ARGV[1] - 60000)
if redis.call('ZCARD', KEYS[1]) >= tonumber(ARGV[2]) then return 0 end
redis.call('ZADD', KEYS[1], ARGV[1], ARGV[3])
redis.call('EXPIRE', KEYS[1], 60)
return 1
"""

def check_rate_limit(key: str) -> None:
    bucket = "rate:" + hashlib.sha256(key.encode()).hexdigest()
    allowed = r.eval(_SCRIPT, 1, bucket, int(time.time() * 1000), settings.rate_limit_per_minute, uuid.uuid4().hex)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers={"Retry-After": "60"})
