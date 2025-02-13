# Vardhan Flask Application

A Flask-based web application for managing AMC contracts and equipment across multiple colleges.

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
2. GitHub Actions runs the test suite
3. If tests pass, the code is automatically deployed to the production server
4. The deployment script:
   - Pulls the latest changes
   - Rebuilds Docker containers
   - Runs database migrations
   - Restarts the application

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
4. Start development server: `flask run`

Last updated: 2025-02-13
