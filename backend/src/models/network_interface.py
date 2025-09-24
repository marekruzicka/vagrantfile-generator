"""
NetworkInterface model for Vagrantfile GUI Generator.

This module defines network interface configurations for virtual machines.
"""

from typing import Optional
from enum import Enum
import ipaddress
import re

from pydantic import BaseModel, Field, field_validator, ValidationInfo

# Global configuration for validation
_validation_config = {
    "allow_public_ips_in_private_networks": False
}

def set_validation_config(config: dict):
    """Set global validation configuration."""
    global _validation_config
    _validation_config.update(config)

def get_validation_config() -> dict:
    """Get current validation configuration."""
    return _validation_config.copy()


class NetworkType(str, Enum):
    """Network interface types supported by Vagrant."""
    PRIVATE_NETWORK = "private_network"
    PUBLIC_NETWORK = "public_network"
    FORWARDED_PORT = "forwarded_port"


class IPAssignment(str, Enum):
    """IP address assignment methods."""
    STATIC = "static"
    DHCP = "dhcp"


class Protocol(str, Enum):
    """Network protocols for port forwarding."""
    TCP = "tcp"
    UDP = "udp"


class NetworkInterfaceBase(BaseModel):
    """Base class for network interface configuration."""
    
    type: NetworkType = Field(
        ...,
        description="Type of network interface"
    )
    ip_assignment: IPAssignment = Field(
        default=IPAssignment.DHCP,
        description="IP address assignment method"
    )
    ip_address: Optional[str] = Field(
        default=None,
        description="Static IP address (required if ip_assignment=static)"
    )
    netmask: str = Field(
        default="255.255.255.0",
        description="Network mask for static IP"
    )
    bridge: Optional[str] = Field(
        default=None,
        description="Bridge interface name (for public networks)"
    )
    host_port: Optional[int] = Field(
        default=None,
        ge=1,
        le=65535,
        description="Host port (for forwarded_port type)"
    )
    guest_port: Optional[int] = Field(
        default=None,
        ge=1,
        le=65535,
        description="Guest port (for forwarded_port type)"
    )
    protocol: Protocol = Field(
        default=Protocol.TCP,
        description="Protocol for forwarded ports"
    )

    @field_validator('ip_address')
    @classmethod
    def validate_ip_address(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate IP address format and requirements."""
        if v is None:
            # IP address is required for static assignment
            if info.data.get('ip_assignment') == IPAssignment.STATIC:
                raise ValueError("IP address is required for static IP assignment")
            return v
        
        # Validate IPv4 format
        try:
            ip = ipaddress.IPv4Address(v)
            # Check for reserved addresses
            if ip.is_loopback:
                raise ValueError("Loopback addresses not allowed")
            if ip.is_multicast:
                raise ValueError("Multicast addresses not allowed")
            if ip.is_reserved:
                raise ValueError("Reserved IP addresses not allowed")
            
            # Check for .1 addresses (typically network gateway)
            if str(ip).endswith('.1'):
                raise ValueError("IP addresses ending with .1 are not allowed (typically reserved for network gateway)")
            
            # Check for private network ranges validity (for private_network type)
            if info.data.get('type') == 'private_network':
                # Get current validation configuration
                config = get_validation_config()
                
                if not config.get('allow_public_ips_in_private_networks', False):
                    ip_parts = [int(part) for part in str(ip).split('.')]
                    is_private = False
                    
                    # 192.168.x.x
                    if ip_parts[0] == 192 and ip_parts[1] == 168:
                        is_private = True
                    # 10.x.x.x
                    elif ip_parts[0] == 10:
                        is_private = True
                    # 172.16-31.x.x
                    elif ip_parts[0] == 172 and 16 <= ip_parts[1] <= 31:
                        is_private = True
                    
                    if not is_private:
                        raise ValueError("Private network IP address should be in a private network range (192.168.x.x, 10.x.x.x, or 172.16-31.x.x)")
                # If allow_public_ips_in_private_networks is True, skip private range validation
                
        except ipaddress.AddressValueError:
            raise ValueError(f"Invalid IPv4 address: {v}")
        
        return v

    @field_validator('netmask')
    @classmethod
    def validate_netmask(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate netmask format."""
        if v is None:
            return v
        
        # Check if netmask is in valid format (255.255.255.0 or CIDR notation /24)
        if v.startswith('/'):
            # CIDR notation
            try:
                cidr = int(v[1:])
                if not 0 <= cidr <= 32:
                    raise ValueError("CIDR notation must be between /0 and /32")
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError("Invalid CIDR notation format")
                raise
        else:
            # Dotted decimal notation
            try:
                ipaddress.IPv4Address(v)
            except ipaddress.AddressValueError:
                raise ValueError("Invalid netmask format")
        
        return v

    @field_validator('bridge')
    @classmethod
    def validate_bridge(cls, v: Optional[str]) -> Optional[str]:
        """Validate bridge interface name."""
        if v is None:
            return v
        
        # Basic validation for bridge interface names
        if not v.strip():
            raise ValueError("Bridge interface name cannot be empty")
        
        # Check for valid interface name patterns
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Bridge interface name contains invalid characters")
        
        return v

    @field_validator('host_port')
    @classmethod
    def validate_host_port(cls, v: Optional[int]) -> Optional[int]:
        """Validate host port number."""
        if v is None:
            return v
        
        if not 1 <= v <= 65535:
            raise ValueError("Port number must be between 1 and 65535")
        
        return v

    @field_validator('guest_port')
    @classmethod
    def validate_guest_port(cls, v: Optional[int]) -> Optional[int]:
        """Validate guest port number."""
        if v is None:
            return v
        
        if not 1 <= v <= 65535:
            raise ValueError("Port number must be between 1 and 65535")
        
        return v


class NetworkInterface(NetworkInterfaceBase):
    """Complete network interface model."""
    
    id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the interface"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "type": "private_network",
                "ip_assignment": "static",
                "ip_address": "192.168.33.10",
                "netmask": "255.255.255.0"
            }
        }

    def __init__(self, **data):
        """Initialize with auto-generated ID if not provided."""
        if 'id' not in data or data['id'] is None:
            import uuid
            data['id'] = str(uuid.uuid4())
        super().__init__(**data)

    def is_static(self) -> bool:
        """Check if this interface uses static IP assignment."""
        return self.ip_assignment == IPAssignment.STATIC

    def is_forwarded_port(self) -> bool:
        """Check if this is a port forwarding configuration."""
        return self.type == NetworkType.FORWARDED_PORT

    def get_vagrant_config(self) -> str:
        """Generate Vagrant configuration string for this interface."""
        if self.type == NetworkType.FORWARDED_PORT:
            protocol_str = self.protocol.value if hasattr(self.protocol, 'value') else str(self.protocol).lower()
            return f'config.vm.network "forwarded_port", guest: {self.guest_port}, host: {self.host_port}, protocol: "{protocol_str}"'
        
        elif self.type == NetworkType.PRIVATE_NETWORK:
            if self.ip_assignment == IPAssignment.STATIC:
                return f'config.vm.network "private_network", ip: "{self.ip_address}"'
            else:
                return 'config.vm.network "private_network", type: "dhcp"'
        
        elif self.type == NetworkType.PUBLIC_NETWORK:
            if self.bridge:
                return f'config.vm.network "public_network", bridge: "{self.bridge}"'
            else:
                return 'config.vm.network "public_network"'
        
        return ""

    def validate_interface(self) -> tuple[list[str], list[str]]:
        """
        Validate the network interface configuration.
        
        Returns:
            tuple: (errors, warnings)
        """
        errors = []
        warnings = []

        # Type-specific validation
        if self.type == NetworkType.FORWARDED_PORT:
            if not self.host_port or not self.guest_port:
                errors.append("Port forwarding requires both host and guest ports")
            elif self.host_port == self.guest_port:
                warnings.append("Host and guest ports are the same")
        
        elif self.type == NetworkType.PRIVATE_NETWORK:
            if self.ip_assignment == IPAssignment.STATIC and not self.ip_address:
                errors.append("Static private network requires IP address")
        
        elif self.type == NetworkType.PUBLIC_NETWORK:
            if not self.bridge:
                warnings.append("Public network without bridge specification may prompt for interface selection")

        return errors, warnings