# Contributing to Whispers of the Wires

Thank you for your interest in contributing!

## Development Setup

```bash
git clone <repo-url>
cd whispers_of_the_wires
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Code Style

- Follow PEP 8
- Use black for formatting
- Run flake8 before committing

## Testing

```bash
pytest tests/ -v --cov=app
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a PR
