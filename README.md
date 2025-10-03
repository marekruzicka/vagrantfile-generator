![logo](pics/logo_light_cropped.png)
# Overview

A modern web-based application for generating Vagrantfiles with an intuitive interface.  
Create and manage multiple virtual machines, configure networking, provisioners, triggers, plugins, and generate working Vagrant configurations with ease.

## Features

- **🚀 Modern Interface**: Clean, responsive web interface that works on any device
- **📦 Multiple VMs**: Create and edit multiple virtual machines with custom memory, CPUs, boxes, and network settings
- **🌐 Advanced Networking**: Static IPs, DHCP, port forwarding, and private networks between VMs
- **🔧 Provisioners**: Add shell scripts for VM setup (anisble to come)
- **⚙️ Plugins & Triggers**: Install Vagrant plugins and configure triggers for pre/post Vagrant actions
- **💾 Project Management**: Save and organize your Vagrant configurations
- **✅ Real-time Validation**: Immediate feedback on configuration errors
- **📝 Production-Ready Output**: Generate syntactically correct, ready-to-use Vagrantfiles
- **📱 Cross-Platform**: Works on desktop, tablet, and mobile devices

## Requirements
Docker or Podman installed on your system
Modern web browser (Chrome, Firefox, Safari, Edge)
Available ports 5173 and 8000 on your machine

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd Vagrantfile-generator

# Start the application
make dev

# Open your browser
# Application: http://localhost:5173
```

## How to Use

1. **Start the application** using the quick start command above
2. **Open your browser** and go to http://localhost:5173
3. **Click on shiny things** - it's pretty self explanatory

## Support & Documentation

- **Development Setup**: See [Development Guide](DEVELOPMENT.md) for detailed setup instructions
- **Production Deployment**: Follow the [Frontend Production Guide](docs/FRONTEND_PRODUCTION.md) for the nginx-based runtime-configured stack
- **Issues**: Report bugs and feature requests through the project repository
- **Contributing**: Fork the repository and submit pull requests for improvements

## License

MIT License - see [LICENSE](LICENSE) file for details.
