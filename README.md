# Vagrantfile Generator

A modern web-based application for generating Vagrantfiles with an intuitive interface. Create and manage multiple virtual machines, configure networking, and generate production-ready Vagrant configurations with ease.

## Features

- **🚀 Modern Interface**: Responsive, mobile-friendly web interface built with Tailwind CSS
- **📦 Multiple VM Support**: Create and manage multiple virtual machines in a single project
- **🌐 Advanced Networking**: Configure static/dynamic IP assignment and multiple network interfaces
- **🔧 Plugin Configuration**: Add and configure custom Vagrant plugins per VM or globally
- **💾 Project Management**: Save, load, and organize project configurations with persistent storage
- **✅ Real-time Validation**: Immediate feedback on configuration errors and validation
- **📝 Vagrantfile Generation**: Generate syntactically correct, production-ready Vagrantfiles
- **🐳 Containerized Development**: Full Docker/Podman support with hot reloading
- **📱 Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

## Technology Stack

- **Backend**: Python 3.11 + FastAPI + Pydantic + Uvicorn
- **Frontend**: HTML5/CSS3/JavaScript ES2022 + Tailwind CSS + Alpine.js
- **Development**: Vite dev server with hot module replacement
- **Storage**: JSON-based project persistence with file system storage
- **Containerization**: Docker/Podman with docker-compose for development
- **Testing**: Pytest for backend, comprehensive integration testing

## Quick Start

### Using Containers (Recommended)

The fastest way to get started is using the containerized development environment:

```bash
# Clone the repository
git clone <repository-url>
cd Vagrantfile-generator

# Start the development environment
make dev-setup

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

For detailed container setup, see [Container Development Guide](README-CONTAINERS.md).

### Manual Development Setup

#### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Run the API server (with auto-reload)
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Build Tailwind CSS
npm run tailwind

# Start development server
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Project Structure

```
Vagrantfile-generator/
├── backend/
│   ├── src/
│   │   ├── models/          # Pydantic data models
│   │   ├── services/        # Business logic services
│   │   ├── api/            # FastAPI route endpoints
│   │   ├── utils/          # Utility functions and validation
│   │   └── main.py         # Application entry point
│   ├── data/               # Project storage directory
│   ├── tests/
│   │   ├── contract/       # API contract tests
│   │   ├── integration/    # End-to-end integration tests
│   │   └── unit/          # Unit tests
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Backend container configuration
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/         # Main application views
│   │   ├── services/      # API communication layer
│   │   ├── styles/        # Tailwind CSS configuration
│   │   └── index.html     # Main application entry point
│   ├── tests/
│   │   └── unit/          # Frontend component tests
│   ├── package.json       # Node.js dependencies
│   ├── vite.config.js     # Vite development server config
│   ├── tailwind.config.js # Tailwind CSS configuration
│   └── Dockerfile         # Frontend container configuration
├── docker-compose.yml     # Container orchestration
├── Makefile              # Development automation commands
├── README.md             # This file
├── README-CONTAINERS.md  # Container development guide
└── test-containers.sh    # Container testing script
```

## Usage

1. **Start the application** using containers (`make dev-setup`) or manual setup
2. **Open your browser** and navigate to http://localhost:5173
3. **Create a new project** by clicking "Create Your First Project"
4. **Add virtual machines** and configure their properties:
   - Choose VM name and Vagrant box
   - Set memory and CPU allocations
   - Configure hostname (optional)
5. **Set up networking** (optional):
   - Add private network interfaces
   - Configure static or dynamic IP assignment
   - Set port forwarding rules
6. **Add provisioners** (optional) for VM setup automation
7. **Generate Vagrantfile** by clicking the "Generate Vagrantfile" button
8. **Download and use** the generated Vagrantfile in your project
9. **Save your project** for future editing and modifications

### Example Workflow

```bash
# 1. Start the application
make dev-setup

# 2. Open browser to http://localhost:5173
# 3. Create a project called "Web Development Environment"
# 4. Add VM: "web-server" with "ubuntu/jammy64" box
# 5. Configure: 2GB RAM, 2 CPUs
# 6. Add private network: 192.168.33.10
# 7. Generate and download Vagrantfile
# 8. Use in your project:

cd my-project
# Place downloaded Vagrantfile here
vagrant up
```

## API Documentation

The backend provides a comprehensive REST API documented with OpenAPI/Swagger:

- **Interactive API Docs**: http://localhost:8000/docs
- **OpenAPI Specification**: http://localhost:8000/openapi.json

### Key API Endpoints

- `GET /api/projects` - List all projects
- `POST /api/projects` - Create a new project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project
- `POST /api/projects/{id}/vms` - Add VM to project
- `PUT /api/projects/{id}/vms/{name}` - Update VM configuration
- `DELETE /api/projects/{id}/vms/{name}` - Remove VM from project
- `POST /api/projects/{id}/generate` - Generate Vagrantfile
- `GET /api/projects/{id}/download` - Download Vagrantfile

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