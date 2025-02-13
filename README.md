# Vardhan Flask Application

A Flask-based web application for managing AMC contracts and equipment across multiple colleges.

## Version
Current Version: 1.0.0

## Features

- Multi-user authentication system
- Equipment management
- AMC contract tracking
- Technician assignment system
- Automated deployment via GitHub Actions

## Deployment

The application is automatically deployed to https://vardhan.planetmilav.com when changes are pushed to the master branch.

### Deployment Process
1. Push changes to the master branch
2. GitHub Actions runs the test suite and security checks
3. If tests pass, the code is automatically deployed to the production server
4. The deployment script:
   - Pulls the latest changes
   - Rebuilds Docker containers
   - Runs database migrations
   - Restarts the application

### Release Process
1. Create a new version tag: `git tag -a v1.x.x -m "Release message"`
2. Push the tag: `git push origin v1.x.x`
3. GitHub Actions will automatically:
   - Run tests and security checks
   - Deploy to production
   - Create a GitHub release with notes

## Default Credentials

### System Admin
- Email: admin@vardhaninsys.com
- Password: admin123

### College Admins
- Engineering College: college1@example.com / password123
- Medical College: college2@example.com / password123
- Arts College: college3@example.com / password123

### Technicians
- Junior Technicians:
  - jrtech1@example.com / password123
  - jrtech2@example.com / password123
  - jrtech3@example.com / password123
- Senior Technicians:
  - srtech1@example.com / password123
  - srtech2@example.com / password123

## Development

### Prerequisites
- Python 3.12+
- Docker and Docker Compose
- Git

### Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `pytest`
4. Start development server:
   ```bash
   # Option 1: Using Python directly
   python main.py

   # Option 2: Using Flask CLI
   flask run

   # Option 3: Using Docker
   docker-compose up
   ```

### Flask Shell
For database operations and testing, use Flask shell:
```bash
flask shell
```
Available objects in shell context:
- `db`: Database instance
- `User`: User model
- `ServiceRequest`: Service Request model
- `TicketUpdate`: Ticket Update model

## Security
- All dependencies are regularly scanned for vulnerabilities
- Code is analyzed using Bandit for security issues
- Automated security checks in CI/CD pipeline

Last updated: 2025-02-14
