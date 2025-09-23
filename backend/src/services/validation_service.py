"""
ValidationService for Vagrantfile GUI Generator.

This service provides validation logic for projects, VMs, and configurations.
"""

from typing import Dict, List, Any, Tuple
import re
import ipaddress
from ..models.project import Project
from ..models.virtual_machine import VirtualMachine
from ..models.network_interface import NetworkInterface


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class ValidationService:
    """Service for validating project configurations."""
    
    def __init__(self):
        """Initialize the validation service."""
        pass
    
    def validate_project(self, project: Project) -> Dict[str, Any]:
        """
        Validate a complete project configuration.
        
        Args:
            project: The project to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        try:
            # Basic project validation
            self._validate_project_basic(project, results)
            
            # VM validation
            self._validate_project_vms(project, results)
            
            # Network validation
            self._validate_project_networking(project, results)
            
            # Resource validation
            self._validate_project_resources(project, results)
            
            # Best practices validation
            self._validate_project_best_practices(project, results)
            
        except ValidationError as e:
            results["is_valid"] = False
            results["errors"].append(str(e))
        
        # Set overall validity
        if results["errors"]:
            results["is_valid"] = False
        
        return results
    
    def _validate_project_basic(self, project: Project, results: Dict[str, Any]):
        """Validate basic project properties."""
        # Check project name
        if not project.name or len(project.name.strip()) == 0:
            results["errors"].append("Project name cannot be empty")
        
        if len(project.name) > 50:
            results["errors"].append("Project name cannot exceed 50 characters")
        
        # Check for invalid characters in project name
        if not re.match(r'^[a-zA-Z0-9_-]+$', project.name):
            results["errors"].append("Project name can only contain letters, numbers, underscores, and hyphens")
        
        # Check VM count
        if len(project.vms) == 0:
            results["warnings"].append("Project has no VMs defined")
        
        if len(project.vms) > 10:
            results["warnings"].append("Project has many VMs - this may impact performance")
    
    def _validate_project_vms(self, project: Project, results: Dict[str, Any]):
        """Validate VM configurations."""
        vm_names = set()
        
        for vm in project.vms:
            # Check for duplicate VM names
            if vm.name in vm_names:
                results["errors"].append(f"Duplicate VM name: {vm.name}")
            vm_names.add(vm.name)
            
            # Validate individual VM
            vm_results = self.validate_vm(vm)
            if not vm_results["is_valid"]:
                results["errors"].extend([f"VM '{vm.name}': {error}" for error in vm_results["errors"]])
            results["warnings"].extend([f"VM '{vm.name}': {warning}" for warning in vm_results["warnings"]])
            results["suggestions"].extend([f"VM '{vm.name}': {suggestion}" for suggestion in vm_results["suggestions"]])
    
    def _validate_project_networking(self, project: Project, results: Dict[str, Any]):
        """Validate network configurations across VMs."""
        used_ips = set()
        
        for vm in project.vms:
            for interface in vm.network_interfaces:
                if interface.ip_address:
                    # Check for IP conflicts
                    if interface.ip_address in used_ips:
                        results["errors"].append(f"IP address conflict: {interface.ip_address} is used by multiple VMs")
                    used_ips.add(interface.ip_address)
                    
                    # Validate IP address format
                    try:
                        ipaddress.IPv4Address(interface.ip_address)
                    except ipaddress.AddressValueError:
                        results["errors"].append(f"Invalid IP address: {interface.ip_address}")
        
        # Check for common network issues
        private_networks = []
        for vm in project.vms:
            for interface in vm.network_interfaces:
                if interface.type == "private_network" and interface.ip_address:
                    try:
                        ip = ipaddress.IPv4Address(interface.ip_address)
                        network = ipaddress.IPv4Network(f"{interface.ip_address}/{interface.netmask}", strict=False)
                        private_networks.append(network)
                    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
                        pass  # Already handled above
        
        # Check for overlapping networks
        for i, net1 in enumerate(private_networks):
            for net2 in private_networks[i+1:]:
                if net1.overlaps(net2):
                    results["warnings"].append(f"Overlapping networks detected: {net1} and {net2}")
    
    def _validate_project_resources(self, project: Project, results: Dict[str, Any]):
        """Validate resource allocations."""
        total_memory = sum(vm.memory for vm in project.vms)
        total_cpus = sum(vm.cpus for vm in project.vms)
        
        # Memory warnings
        if total_memory > 16384:  # 16GB
            results["warnings"].append(f"High total memory allocation: {total_memory}MB across all VMs")
        
        if total_memory > 32768:  # 32GB
            results["errors"].append(f"Excessive memory allocation: {total_memory}MB may cause host system issues")
        
        # CPU warnings
        if total_cpus > 8:
            results["warnings"].append(f"High total CPU allocation: {total_cpus} CPUs across all VMs")
        
        if total_cpus > 16:
            results["errors"].append(f"Excessive CPU allocation: {total_cpus} CPUs may cause host system issues")
        
        # Individual VM resource checks
        for vm in project.vms:
            if vm.memory < 512:
                results["warnings"].append(f"VM '{vm.name}' has low memory allocation: {vm.memory}MB")
            
            if vm.memory > 8192:
                results["warnings"].append(f"VM '{vm.name}' has high memory allocation: {vm.memory}MB")
            
            if vm.cpus > 4:
                results["warnings"].append(f"VM '{vm.name}' has high CPU allocation: {vm.cpus} CPUs")
    
    def _validate_project_best_practices(self, project: Project, results: Dict[str, Any]):
        """Validate against best practices."""
        # Check for descriptive names
        generic_names = {"vm", "test", "box", "server", "machine"}
        for vm in project.vms:
            if vm.name.lower() in generic_names:
                results["suggestions"].append(f"VM '{vm.name}' has a generic name - consider a more descriptive name")
        
        # Check for project description
        if not project.description or len(project.description.strip()) == 0:
            results["suggestions"].append("Consider adding a project description")
        
        # Check for common box names
        common_boxes = {"ubuntu/jammy64", "ubuntu/focal64", "centos/7", "debian/bullseye64"}
        for vm in project.vms:
            if vm.box not in common_boxes:
                results["suggestions"].append(f"VM '{vm.name}' uses box '{vm.box}' - ensure it's available")
        
        # Check hostname configuration
        for vm in project.vms:
            if not vm.hostname:
                results["suggestions"].append(f"VM '{vm.name}' has no hostname set - it will default to VM name")
    
    def validate_vm(self, vm: VirtualMachine) -> Dict[str, Any]:
        """
        Validate a single VM configuration.
        
        Args:
            vm: The VM to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Name validation
        if not re.match(r'^[a-zA-Z0-9_-]+$', vm.name):
            results["errors"].append("VM name can only contain letters, numbers, underscores, and hyphens")
        
        # Box validation
        if not vm.box or len(vm.box.strip()) == 0:
            results["errors"].append("VM box cannot be empty")
        
        # Resource validation
        if vm.memory < 512:
            results["warnings"].append("Memory allocation is below recommended minimum (512MB)")
        
        if vm.memory > 8192:
            results["warnings"].append("High memory allocation may impact host system")
        
        if vm.cpus < 1:
            results["errors"].append("VM must have at least 1 CPU")
        
        if vm.cpus > 4:
            results["warnings"].append("High CPU allocation may impact host system")
        
        # Network interface validation
        for interface in vm.network_interfaces:
            interface_results = self.validate_network_interface(interface)
            if not interface_results["is_valid"]:
                results["errors"].extend(interface_results["errors"])
            results["warnings"].extend(interface_results["warnings"])
            results["suggestions"].extend(interface_results["suggestions"])
        
        # Set overall validity
        if results["errors"]:
            results["is_valid"] = False
        
        return results
    
    def validate_network_interface(self, interface: NetworkInterface) -> Dict[str, Any]:
        """
        Validate a network interface configuration.
        
        Args:
            interface: The network interface to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Static IP validation
        if interface.ip_assignment == "static":
            if not interface.ip_address:
                results["errors"].append("Static IP assignment requires an IP address")
            else:
                try:
                    ip = ipaddress.IPv4Address(interface.ip_address)
                    
                    # Check for commonly problematic IPs
                    if ip.is_loopback:
                        results["errors"].append("Cannot use loopback IP address")
                    elif ip.is_multicast:
                        results["errors"].append("Cannot use multicast IP address")
                    elif ip.is_reserved:
                        results["warnings"].append("Using reserved IP address range")
                    
                    # Check for private network ranges
                    if not ip.is_private and interface.type == "private_network":
                        results["warnings"].append("Public IP address used in private network")
                    
                except ipaddress.AddressValueError:
                    results["errors"].append(f"Invalid IP address format: {interface.ip_address}")
        
        # Netmask validation
        try:
            ipaddress.IPv4Network(f"192.168.1.1/{interface.netmask}", strict=False)
        except ipaddress.NetmaskValueError:
            results["errors"].append(f"Invalid netmask: {interface.netmask}")
        
        # Port forwarding validation
        if interface.type == "forwarded_port":
            if interface.guest_port is None or interface.host_port is None:
                results["errors"].append("Port forwarding requires both guest and host ports")
            elif interface.guest_port == interface.host_port:
                results["suggestions"].append("Guest and host ports are the same")
            
            # Check for common port conflicts
            common_ports = {22: "SSH", 80: "HTTP", 443: "HTTPS", 3306: "MySQL", 5432: "PostgreSQL"}
            if interface.host_port in common_ports:
                service = common_ports[interface.host_port]
                results["warnings"].append(f"Host port {interface.host_port} is commonly used by {service}")
        
        # Set overall validity
        if results["errors"]:
            results["is_valid"] = False
        
        return results
    
    def validate_vagrantfile_syntax(self, content: str) -> Dict[str, Any]:
        """
        Validate Vagrantfile syntax (basic checks).
        
        Args:
            content: The Vagrantfile content
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Basic syntax checks
        if not content.strip():
            results["errors"].append("Vagrantfile content is empty")
            results["is_valid"] = False
            return results
        
        # Check for required structure
        if "Vagrant.configure" not in content:
            results["errors"].append("Vagrantfile missing Vagrant.configure block")
        
        if "config.vm.define" not in content and "config.vm.box" not in content:
            results["warnings"].append("No VM definitions found in Vagrantfile")
        
        # Check for common issues
        if content.count('"') % 2 != 0:
            results["errors"].append("Unmatched quotes in Vagrantfile")
        
        if "end" not in content:
            results["warnings"].append("No 'end' statements found - check block closures")
        
        # Check for best practices
        if "config.vm.box" in content and "config.vm.box_version" not in content:
            results["suggestions"].append("Consider pinning box versions for reproducibility")
        
        # Set overall validity
        if results["errors"]:
            results["is_valid"] = False
        
        return results