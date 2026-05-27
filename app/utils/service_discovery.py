"""
Service discovery utilities using Bonjour/mDNS
"""
import logging
import re
import socket
from typing import Optional

from zeroconf import ServiceInfo, Zeroconf

logger = logging.getLogger(__name__)

SERVICE_TYPE = "_homehub._tcp.local."


def _sanitize_dns_label(name: str, fallback: str = "homehub") -> str:
    """Normalize a string for use as an mDNS host/service label."""
    label = name.strip().replace(" ", "-").replace("_", "-")
    label = re.sub(r"[^a-zA-Z0-9-]", "-", label)
    label = re.sub(r"-+", "-", label).strip("-").lower()
    return (label or fallback)[:63]


def _local_ip_for_discovery(bind_host: str) -> Optional[str]:
    """Return the LAN address to publish in mDNS records."""
    if bind_host not in ("0.0.0.0", "127.0.0.1", "::", "::1"):
        return bind_host

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return None


class BonjourService:
    """Bonjour/mDNS service registration for HomeHub server"""

    def __init__(self):
        self.zeroconf = None
        self.service_info = None
        self._running = False
        self.registered_hostname = None
        self.registered_service_name = None

    def register_service(self, host, port, server_name="HomeHub"):
        """
        Register the HomeHub service with Bonjour/mDNS

        Args:
            host (str): Server host/IP address Flask binds to
            port (int): Server port
            server_name (str): Display name for the service
        """
        if host in ("127.0.0.1", "::1"):
            logger.warning(
                "Skipping Bonjour registration: server is bound to %s (not reachable on the LAN)",
                host,
            )
            return

        local_ip = _local_ip_for_discovery(host)
        if not local_ip:
            logger.error("Could not determine local IP address for Bonjour advertisement")
            return

        hostname_label = _sanitize_dns_label(server_name)
        service_instance = f"{hostname_label}.{SERVICE_TYPE}"

        properties = {
            "name": server_name,
            "type": "HomeHub VOD Server",
            "version": "1.0.0",
            "path": "/",
            "api": "/api/info",
        }
        txt_properties = {k: str(v).encode("utf-8") for k, v in properties.items()}

        self.zeroconf = None
        try:
            self.service_info = ServiceInfo(
                SERVICE_TYPE,
                service_instance,
                addresses=[socket.inet_aton(local_ip)],
                port=port,
                properties=txt_properties,
                server=f"{hostname_label}.local.",
            )

            self.zeroconf = Zeroconf()
            self.zeroconf.register_service(self.service_info, allow_name_change=True)
            self._running = True

            registered_name = self.service_info.name or service_instance
            if not registered_name.endswith("."):
                registered_name = f"{registered_name}."
            self.registered_hostname = f"{hostname_label}.local"
            self.registered_service_name = registered_name

            logger.info("HomeHub Bonjour service registered: %s", registered_name)
            logger.info("  Address: %s:%s", local_ip, port)
            logger.info("  Hostname: %s", self.registered_hostname)
        except Exception:
            logger.exception("Failed to register Bonjour service")
            self._clear_registration()

    def _clear_registration(self):
        """Release zeroconf resources without treating the service as active."""
        if self.zeroconf:
            try:
                self.zeroconf.close()
            except Exception:
                logger.exception("Error closing Bonjour client after registration failure")
        self.zeroconf = None
        self.service_info = None
        self._running = False
        self.registered_hostname = None
        self.registered_service_name = None

    def unregister_service(self):
        """Unregister the service"""
        self._running = False
        if not self.zeroconf or not self.service_info:
            return

        try:
            self.zeroconf.unregister_service(self.service_info)
            self.zeroconf.close()
            logger.info("HomeHub Bonjour service unregistered")
        except Exception:
            logger.exception("Error unregistering Bonjour service")
        finally:
            self._clear_registration()

    def __del__(self):
        self.unregister_service()


_bonjour_service = None


def start_service_discovery(host, port, server_name="HomeHub"):
    """Start Bonjour/mDNS service discovery"""
    global _bonjour_service
    stop_service_discovery()
    _bonjour_service = BonjourService()
    _bonjour_service.register_service(host, port, server_name)
    return _bonjour_service


def stop_service_discovery():
    """Stop Bonjour/mDNS service discovery"""
    global _bonjour_service
    if _bonjour_service:
        _bonjour_service.unregister_service()
        _bonjour_service = None


def discovery_hostname_for(server_name: str) -> str:
    """Predict the Bonjour hostname when discovery has not started yet."""
    return f"{_sanitize_dns_label(server_name)}.local"


def get_discovery_status():
    """Return active Bonjour registration details for API consumers."""
    if not _bonjour_service or not _bonjour_service._running:
        return None

    return {
        "bonjour_service": _bonjour_service.registered_hostname,
        "service_type": SERVICE_TYPE,
        "service_name": _bonjour_service.registered_service_name,
    }
