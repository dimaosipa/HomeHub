"""
Service discovery utilities using Bonjour/mDNS
"""
import socket
import threading
import time
from zeroconf import ServiceInfo, Zeroconf

class BonjourService:
    """Bonjour/mDNS service registration for HomeHub server"""
    
    def __init__(self):
        self.zeroconf = None
        self.service_info = None
        self._thread = None
        self._running = False
        
    def register_service(self, host, port, server_name="HomeHub"):
        """
        Register the HomeHub service with Bonjour/mDNS
        
        Args:
            host (str): Server host/IP address
            port (int): Server port
            server_name (str): Display name for the service
        """
        try:
            # Get local IP address if host is 0.0.0.0
            if host == "0.0.0.0":
                # Get the local IP address
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
            else:
                local_ip = host
            
            # Clean up server name for DNS compatibility and make unique
            import os
            clean_server_name = server_name.replace(' ', '-').replace('_', '-')
            unique_server_name = f"{clean_server_name}-{os.getpid()}"
            
            # Service type for HTTP servers
            service_type = "_http._tcp.local."
            service_name = f"{unique_server_name}.{service_type}"
            
            # Service properties (TXT records)
            properties = {
                'name': server_name,
                'type': 'HomeHub VOD Server',
                'version': '1.0.0',
                'path': '/',
                'api': '/api/info'
            }
            
            # Convert string values to bytes for TXT records
            txt_properties = {k: str(v).encode('utf-8') for k, v in properties.items()}
            
            # Create service info
            self.service_info = ServiceInfo(
                service_type,
                service_name,
                addresses=[socket.inet_aton(local_ip)],
                port=port,
                properties=txt_properties,
                server=f"{unique_server_name}.local."
            )
            
            # Initialize zeroconf
            self.zeroconf = Zeroconf()
            
            # Register the service in main thread to avoid threading issues
            self._register_service_sync()
            
            print(f"✅ HomeHub service registered: {service_name}")
            print(f"   Host: {local_ip}:{port}")
            print(f"   Service: {service_type}")
            print(f"   Discoverable as: {unique_server_name}.local")
            
        except Exception as e:
            import traceback
            print(f"❌ Failed to register Bonjour service: {e}")
            print(f"Full traceback: {traceback.format_exc()}")
    
    def _register_service_sync(self):
        """Register service synchronously"""
        try:
            self.zeroconf.register_service(self.service_info)
            self._running = True
            print(f"✅ Service registration completed successfully")
        except Exception as e:
            import traceback
            print(f"❌ Error in service registration: {e}")
            print(f"Full traceback: {traceback.format_exc()}")
    
    def unregister_service(self):
        """Unregister the service"""
        try:
            self._running = False
            if self.zeroconf and self.service_info:
                self.zeroconf.unregister_service(self.service_info)
                self.zeroconf.close()
                print("✅ HomeHub service unregistered")
        except Exception as e:
            print(f"❌ Error unregistering service: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.unregister_service()

# Global service instance
_bonjour_service = None

def start_service_discovery(host, port, server_name="HomeHub"):
    """Start Bonjour/mDNS service discovery"""
    global _bonjour_service
    _bonjour_service = BonjourService()
    _bonjour_service.register_service(host, port, server_name)
    return _bonjour_service

def stop_service_discovery():
    """Stop Bonjour/mDNS service discovery"""
    global _bonjour_service
    if _bonjour_service:
        _bonjour_service.unregister_service()
        _bonjour_service = None
