from tracking.middleware import VisitorTrackingMiddleware
from django.utils.deprecation import MiddlewareMixin


class CloudflareAwareVisitorTrackingMiddleware(VisitorTrackingMiddleware):
    """
    Extended VisitorTrackingMiddleware that properly handles Cloudflare proxy headers
    to reduce duplicate sessions from the same real users.
    """

    def get_client_ip(self, request):
        """
        Get the real client IP from Cloudflare headers, falling back to standard methods.
        This helps reduce duplicate sessions from Cloudflare proxies.
        """
        # Cloudflare sends the real IP in CF-Connecting-IP header
        cf_ip = request.META.get("HTTP_CF_CONNECTING_IP")
        if cf_ip:
            return cf_ip

        # Fallback to X-Forwarded-For (standard proxy header)
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first (real client)
            return x_forwarded_for.split(",")[0].strip()

        # Fallback to X-Real-IP (some proxies use this)
        x_real_ip = request.META.get("HTTP_X_REAL_IP")
        if x_real_ip:
            return x_real_ip

        # Final fallback to REMOTE_ADDR
        return request.META.get("REMOTE_ADDR")

    def should_track(self, request):
        """
        Enhanced tracking logic to reduce duplicate sessions from Cloudflare.
        Only track if we haven't seen this IP+User-Agent combination recently.
        """
        # First check if the parent middleware would track
        if not super().should_track(request):
            return False

        # Get the real client IP
        client_ip = self.get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        # Don't track if no IP or user agent
        if not client_ip or not user_agent:
            return False

        # Check if we've seen this IP+User-Agent combination in the last 2 minutes
        # This helps reduce Cloudflare duplicate sessions while allowing legitimate new visits
        from tracking.models import Visitor
        from django.utils import timezone
        from datetime import timedelta

        two_minutes_ago = timezone.now() - timedelta(minutes=2)
        recent_visitor = Visitor.objects.filter(
            ip_address=client_ip,
            user_agent=user_agent,
            start_time__gte=two_minutes_ago,
        ).first()

        # If we've seen this IP+User-Agent recently, don't track again
        if recent_visitor:
            return False

        return True
