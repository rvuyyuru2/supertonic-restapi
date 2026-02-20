# Contributing to Supertonic TTS API

Thank you for your interest in contributing to the Supertonic Text-to-Speech API project!

## 🎯 What is Supertonic TTS?

Supertonic TTS is an **OpenAI-compatible Text-to-Speech API** that provides high-performance speech synthesis with support for multiple audio formats, voices, and GPU acceleration. It's designed as a drop-in replacement for OpenAI's TTS API, making it easy to integrate into existing applications.

## 🚀 Quick Links

- [Official Documentation](https://github.com/supertoneinc/supertonic-fastapi#-quick-start)
- [API Reference](https://github.com/supertoneinc/supertonic-fastapi#-api-reference)
- [Feature Request Board](https://github.com/supertoneinc/supertonic-fastapi/issues)
- [Bug Reports](https://github.com/supertoneinc/supertonic-fastapi/issues)

## 🤝 How to Contribute

### Reporting Bugs

1. **Search existing issues** to avoid duplicates
2. **Use the bug report template** when creating a new issue
3. **Include details**: environment, steps to reproduce, expected vs actual behavior
4. **Add logs and screenshots** if applicable

### Suggesting Features

1. **Check the issues** for similar proposals
2. **Explain the use case** - why do you need this feature?
3. **Consider alternatives** - is there a better way to solve the problem?

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Follow the coding standards** (PEP 8 for Python)
4. **Write tests** for new functionality
5. **Update documentation** if needed
6. **Commit with clear messages**: `git commit -m 'Add amazing feature'`
7. **Push to your branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

## 🛠️ Development Setup

```bash
# Clone the repository
git clone https://github.com/supertoneinc/supertonic-fastapi.git
cd supertonic-fastapi

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8800
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/tests/test_tts.py

# Run with coverage
pytest --cov=app tests/
```

## 📝 Coding Standards

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints for function parameters and return values
- Write docstrings for all public functions
- Keep functions focused and modular
- Add inline comments for complex logic

## 🎭 Voice & Audio Guidelines

When contributing voice-related features:

- Maintain OpenAI voice compatibility (alloy, echo, fable, onyx, nova, shimmer)
- Support all standard audio formats (MP3, WAV, FLAC, Opus, AAC, PCM)
- Ensure GPU acceleration works on CUDA, CoreML, and Metal

## 📖 Documentation

Good documentation includes:

- Clear README with quick start guide
- API endpoint descriptions with examples
- Configuration options explained
- Docker deployment instructions
- Troubleshooting section

## 🏆 Recognition

Contributors will be recognized in the [README.md](README.md#-acknowledgments) and on the project page.

## 📄 License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

## ❓ Get Help

- Open an [issue](https://github.com/supertoneinc/supertonic-fastapi/issues) for questions
- Join the community discussions
- Check the [Wiki](https://github.com/supertoneinc/supertonic-fastapi/wiki) for guides

---

**Thank you for making Supertonic TTS better!**
