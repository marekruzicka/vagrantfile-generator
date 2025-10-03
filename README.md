# Vagrantfile Generator

MIT License — see the `LICENSE` file for details.

A modern web-based application for generating Vagrantfiles with an intuitive interface. Create and manage multiple virtual machines, configure networking, and generate production-ready Vagrant configurations with ease.

## Features

- **🚀 Modern Interface**: Clean, responsive web interface that works on any device
- **📦 Multiple VM Support**: Create and manage multiple virtual machines in a single project
- **🌐 Advanced Networking**: Configure private networks with static or dynamic IP assignment
- **🔧 Flexible IP Management**: Support for custom IP ranges and automatic IP incrementing for bulk VM creation
- **⚙️ Configuration Options**: Customizable validation settings for different use cases
- **💾 Project Management**: Save, load, and organize your VM configurations
- **✅ Real-time Validation**: Immediate feedback on configuration errors
- **📝 Production-Ready Output**: Generate syntactically correct, ready-to-use Vagrantfiles
- **🏷️ VM Organization**: Label and categorize VMs for better project organization
- **📱 Cross-Platform**: Works on desktop, tablet, and mobile devices

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd Vagrantfile-generator

# Start the application
make dev-setup

# Open your browser
# Application: http://localhost:5173
```

## How to Use

1. **Start the application** using the quick start command above
2. **Open your browser** and go to http://localhost:5173
3. **Create a new project** by clicking "Create Your First Project"
4. **Add virtual machines** with custom configurations:
   - Choose VM name and Vagrant box
   - Set memory and CPU requirements
   - Configure hostname (optional)
5. **Configure networking** (optional):
   - Add private network interfaces
   - Set static IP addresses or use DHCP
   - Enable port forwarding if needed
6. **Organize with labels** to categorize your VMs
7. **Generate Vagrantfile** by clicking the generate button
8. **Download and use** the Vagrantfile in your project directory

## Configuration Options

### Project Settings

- **Validation Mode**: Choose between strict and permissive validation
  - **Strict**: Enforces best practices and prevents common errors
  - **Permissive**: Allows more flexible configurations for advanced users

- **IP Range**: Default IP range for private networks (e.g., `192.168.50.0/24`)
- **Auto-increment IPs**: Automatically assign sequential IP addresses when creating multiple VMs
- **Default Memory**: Set default RAM allocation for new VMs
- **Default CPUs**: Set default CPU count for new VMs

### Footer Configuration

The application includes a configurable footer system that allows you to add static pages and external links.

#### Adding Footer Content

1. **Create content files** in the `backend/resources/footer/` directory:
   ```bash
   mkdir -p backend/resources/footer
   echo "# About Us\nThis is our about page." > backend/resources/footer/about.md
   echo "# Privacy Policy\nOur privacy policy." > backend/resources/footer/privacy.md
   ```

2. **Content files support Markdown** with full formatting:
   ```markdown
   # Page Title
   
   ## Section Header
   
   - List item 1
   - List item 2
   
   [External link](https://example.com)
   ```

3. **Footer automatically discovers** new content files and updates navigation

#### Footer Configuration Format

The footer supports both internal pages and external links:

```json
{
  "copyrightText": "© 2025 Your Company",
  "navigationLinks": [
    {
      "title": "About Us",
      "pageId": "about",
      "isExternal": false,
      "url": null,
      "isEnabled": true,
      "order": 1
    },
    {
      "title": "GitHub",
      "pageId": null,
      "isExternal": true,
      "url": "https://github.com/yourcompany",
      "isEnabled": true,
      "order": 2
    }
  ]
}
```

#### Footer Features

- **Responsive Design**: Optimized for mobile, tablet, and desktop
- **Accessibility**: Full keyboard navigation and screen reader support
- **Performance**: Cached content loading with <100ms response times
- **Error Handling**: Graceful fallbacks when content is unavailable
- **SEO Friendly**: Proper meta tags and semantic HTML structure

## Architecture

The application includes flexible settings to accommodate different use cases:

- **IP Validation**: Choose between strict private IP validation or allow custom ranges
- **Network Configuration**: Support for both simple and advanced networking setups
- **Bulk Operations**: Create multiple VMs with automatic IP incrementing
- **Project Templates**: Save and reuse common VM configurations

## Networking Features

- **Private Networks**: Configure isolated networks between VMs
- **Static IP Assignment**: Set specific IP addresses for each VM
- **Dynamic IP (DHCP)**: Let Vagrant assign IPs automatically
- **Port Forwarding**: Map host ports to guest services
- **IP Range Validation**: Prevent conflicts and ensure valid configurations
- **Bulk VM Creation**: Automatically increment IPs when creating multiple VMs

## Common Use Cases

- **Development Environments**: Create consistent development setups across teams
- **Testing Infrastructure**: Spin up isolated test environments quickly
- **Learning Vagrant**: Experiment with Vagrant configurations without manual file editing
- **Multi-VM Projects**: Set up complex environments with multiple interconnected VMs
- **Network Testing**: Create VMs with specific network configurations for testing

## Requirements

- Docker or Podman installed on your system
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Available ports 5173 and 8000 on your machine

## Support & Documentation

- **Container Setup**: See [Container Development Guide](README-CONTAINERS.md) for detailed setup instructions
- **Issues**: Report bugs and feature requests through the project repository
- **Contributing**: Fork the repository and submit pull requests for improvements

## License

MIT License - see LICENSE file for details.

## Testing

### Running Tests

```bash
# Run all tests using containers
make test

# Run backend tests only
make backend-test

# Run comprehensive container tests
./test-containers.sh

# Manual testing
# Frontend: http://localhost:5173
# API: http://localhost:8000/docs
```

### Test Coverage

- **Unit Tests**: Backend models and services
- **Contract Tests**: API endpoint validation
- **Integration Tests**: End-to-end workflows
- **Container Tests**: Full deployment validation

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `make test`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## Troubleshooting

### Common Issues

**Container won't start:**
```bash
make logs  # Check container logs
make clean && make dev-setup  # Clean rebuild
```

**Port conflicts:**
Edit `docker-compose.yml` to use different ports:
```yaml
ports:
  - "5174:5173"  # Frontend
  - "8001:8000"  # Backend
```

**CSS not loading:**
```bash
# Rebuild frontend with CSS compilation
cd frontend
npm run tailwind
```

For more detailed troubleshooting, see [Container Development Guide](README-CONTAINERS.md).

## License

MIT License - see LICENSE file for details.