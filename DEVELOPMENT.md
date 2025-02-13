# Development Guidelines

## Daily Development Workflow

### 🌅 Start of Day Checklist
- [ ] Pull latest changes
  ```bash
  git pull origin master
  ```
- [ ] Create feature branch
  ```bash
  git checkout -b feature/your-feature-name
  ```
- [ ] Update dependencies
  ```bash
  pip install -r requirements.txt
  ```
- [ ] Run tests
  ```bash
  pytest
  ```
- [ ] Check security
  ```bash
  safety check
  bandit -r app/
  ```

### 💻 During Development
- [ ] Run development server
  ```bash
  flask run
  ```
- [ ] Write tests for new features
- [ ] Run tests frequently
  ```bash
  pytest
  ```
- [ ] Follow code style guidelines (PEP 8)
- [ ] Add docstrings to new functions
- [ ] Keep functions small and focused

### 📝 Before Committing
- [ ] Review changes
  ```bash
  git status
  git diff
  ```
- [ ] Run all tests
  ```bash
  pytest
  ```
- [ ] Check for security issues
  ```bash
  safety check
  bandit -r app/
  ```
- [ ] Stage and commit with meaningful message
  ```bash
  git add .
  git commit -m "type: description"
  ```

### 🚀 Before Pushing
- [ ] Update from master
  ```bash
  git checkout master
  git pull origin master
  git checkout your-feature-branch
  git rebase master
  ```
- [ ] Run tests again
  ```bash
  pytest
  ```
- [ ] Push changes
  ```bash
  git push origin feature/your-feature-name
  ```
- [ ] Create pull request on GitHub

## 📋 Commit Message Types
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Example:
```bash
git commit -m "feat: add email notifications for service requests"
git commit -m "fix: resolve login redirect issue"
git commit -m "docs: update API documentation"
```

## 🔄 Release Process
1. Update version in README.md
2. Create and push tag
   ```bash
   git tag -a v1.x.x -m "Release description"
   git push origin v1.x.x
   ```
3. Monitor GitHub Actions for:
   - Test results
   - Security scan results
   - Deployment status

## 🔍 Code Review Guidelines
- Keep changes focused and small
- Include tests for new features
- Update documentation
- Follow security best practices
- No sensitive data in commits
- Resolve all automated check issues

## 🏗️ Project Structure
```
vardhan-flask/
├── app/                    # Application package
│   ├── amc/               # AMC management
│   ├── auth/              # Authentication
│   ├── main/              # Main routes
│   ├── service_requests/  # Service request handling
│   ├── static/            # Static files
│   └── templates/         # HTML templates
├── migrations/            # Database migrations
├── tests/                 # Test files
├── config.py             # Configuration
├── requirements.txt      # Dependencies
└── wsgi.py              # WSGI entry point
```

## 🔒 Security Checklist
- [ ] No hardcoded secrets
- [ ] Input validation
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] Secure session handling
- [ ] Regular dependency updates
- [ ] Access control checks

## 📊 Monitoring
- Check application logs
- Monitor GitHub Actions
- Review security alerts
- Watch error reports

## 🐛 Bug Fixing Process
1. Create bug fix branch
   ```bash
   git checkout -b fix/bug-description
   ```
2. Write failing test
3. Fix bug
4. Verify test passes
5. Create pull request

## 📚 Documentation Updates
- Keep README.md current
- Update API documentation
- Document configuration changes
- Add comments for complex logic
- Update this guide as needed

Last updated: 2025-02-13
