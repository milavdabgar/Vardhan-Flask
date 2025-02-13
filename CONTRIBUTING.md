# Contributing to Vardhan Flask Project

Welcome students! This guide will help you contribute to the project effectively.

## Getting Started

1. Fork the repository to your GitHub account
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Vardhan-Flask.git
   cd Vardhan-Flask
   ```
3. Set up your development environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Development Workflow

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "feat: describe your changes"
   ```
   
   Follow our commit message convention:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `style:` for formatting changes
   - `refactor:` for code refactoring
   - `test:` for adding tests
   - `chore:` for maintenance tasks

3. Push your changes:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Create a Pull Request (PR) from your fork to our main repository

## Code Quality Guidelines

1. Write tests for new features
2. Follow PEP 8 style guide for Python code
3. Add docstrings to functions and classes
4. Keep functions small and focused
5. Use meaningful variable and function names

## Pull Request Process

1. Update documentation if needed
2. Add tests for new features
3. Ensure all tests pass
4. Get your PR reviewed by at least one maintainer
5. Address review comments

## Getting Help

- Create an issue for bugs or feature requests
- Ask questions in pull request comments
- Contact the maintainer for guidance

## Learning Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Python Testing with pytest](https://docs.pytest.org/)
- [Git Branching Model](https://nvie.com/posts/a-successful-git-branching-model/)
- [Writing Good Commit Messages](https://chris.beams.io/posts/git-commit/)
