"""Custom rate limiting based on tenant plan using Redis."""
from django.core.cache import cache
from django.conf import settings
from rest_framework.throttling import BaseThrottle
from datetime import datetime, timezone


class TenantRateThrottle(BaseThrottle):
    """ "
    Rate limit resume submissions based on tenant plan.
    """

    def generate_cache_key(self, tenant_id):
        """Generate redis key for today's Count."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"rate:{tenant_id}:{today}"

    def get_limit(self, tenant):
        """Get the daily limit for the tenant's plan."""
        return settings.PLAN_RATE_LIMITS.get(tenant.plan)

    def allow_request(self, request, view):
        """Check if tenant is within daily limit."""
        tenant = request.user
        limit = self.get_limit(tenant)

        # No limit for enterprice.
        if limit is None:
            return True

        cache_key = self.generate_cache_key(str(tenant.id))

        current_count = cache.get(cache_key, 0)

        if current_count >= limit:
            # calculate seconds until midnight UTC for reset time.
            now = datetime.now(timezone.utc)

            midnight = now.replace(hour=23, minute=59, second=59, microsecond=0)

            self.wait_hours = (midnight - now).seconds//3600

            return False
        
        cache.incr(cache_key)
        return True

    def wait(self):
        """Return seconds until the rate limit resets."""
        return getattr(self, "wait_hours", None)

    #def increment(self, tenant):
        """Increment the request count for today."""
    #    cache_key = self.generate_cache_key(str(tenant.id))
    #    cache.add(cache_key, 0, timeout=60 * 60 * 25)
    #   cache.incr(cache_key)
