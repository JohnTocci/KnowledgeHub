# Contributing to KnowledgeHub

We love your input! We want to make contributing to KnowledgeHub as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

## Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/JohnTocci/KnowledgeHub.git
   cd KnowledgeHub
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env  # If available
   # Edit .env and add your OpenAI API key
   ```

5. **Run the application:**
   ```bash
   streamlit run streamlit_app.py
   ```

## Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small
- Add type hints where appropriate

## Testing

- Write unit tests for new functionality
- Ensure existing tests pass before submitting PR
- Run tests with: `python -m pytest`

## Security

- Never commit API keys, passwords, or other sensitive information
- Use environment variables for configuration
- Report security vulnerabilities responsibly (see SECURITY.md)

## Issue Reporting

- Use the GitHub issue tracker
- Include detailed steps to reproduce bugs
- Provide system information (OS, Python version, etc.)
- Use the appropriate issue template

## Feature Requests

- Create an issue describing the feature
- Explain the use case and benefits
- Be open to discussion and feedback

## Code of Conduct

This project adheres to the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Getting Help

- Check the [README](README.md) for basic usage
- Look through existing issues before creating new ones
- Join discussions in existing issues
- Reach out to maintainers if needed

Thank you for contributing to KnowledgeHub! 🎉