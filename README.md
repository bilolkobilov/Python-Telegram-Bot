# Telegram Media Downloader Bot

A professional-grade Telegram bot for downloading Instagram and TikTok media, built with **Clean Architecture** principles and modern Python practices.

## 🏗️ Architecture Overview

This project follows **Clean Architecture** principles, ensuring high maintainability, testability, and scalability:


## ✨ Features

- 📱 **Multi-Platform Support**: Instagram & TikTok media downloading
- 🏛️ **Clean Architecture**: Separation of concerns with dependency injection
- 🔒 **Security-First**: No hardcoded credentials, environment-based configuration
- 🌐 **Internationalization**: Multi-language support (English, Russian, Uzbek)
- 📊 **Analytics**: Comprehensive usage tracking and reporting
- 🛡️ **Rate Limiting**: Built-in protection against abuse
- 👨‍💼 **Admin Panel**: Management interface for administrators
- 🔄 **Async Operations**: High-performance asynchronous processing
- 🧪 **Testable**: Modular design with dependency injection
- 📦 **Containerized**: Docker support for easy deployment

## 🛠️ Technology Stack

- **Framework**: Python 3.11+ with AsyncIO
- **Bot Framework**: python-telegram-bot
- **Web Framework**: FastAPI
- **Media Processing**: instaloader, yt-dlp
- **Data Storage**: JSON-based repositories (easily replaceable)
- **Dependency Injection**: Custom container implementation
- **Logging**: Structured logging with multiple handlers
- **Configuration**: Environment-based with validation

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Telegram Bot Token (from @BotFather)
- Optional: Instagram session for private content

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/bilolkobilov/Python-Telegram-Bot.git
   cd Python-Telegram-Bot
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your bot tokens and settings
   ```

5. **Run the application**:
   ```bash
   python src/main.py
   ```

### Docker Deployment

```bash
# Build the image
docker build -t Python-Telegram-Bot .

# Run with environment variables
docker run -d --name Python-Telegram-Bot \
  -e BOT_TOKEN=your_bot_token \
  -e ADMIN_BOT_TOKEN=your_admin_token \
  -e ADMIN_IDS=your_admin_id \
  Python-Telegram-Bot
```

## 🔧 Configuration

All configuration is done via environment variables. See `.env.example` for all available options:

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Main bot token from @BotFather | Yes |
| `ADMIN_BOT_TOKEN` | Admin bot token | Yes |
| `ADMIN_IDS` | Comma-separated admin user IDs | Yes |
| `INSTAGRAM_USERNAME` | Instagram username for session | No |
| `MAX_FILE_SIZE` | Maximum file size in MB | No |
| `RATE_LIMIT_REQUESTS` | Rate limit for requests | No |

## 📋 Usage

### User Commands

- `/start` - Initialize the bot
- `/help` - Show help message
- `/language` - Change language preference

### Admin Commands

- `/stats` - Show system statistics
- `/users` - Manage users
- `/broadcast` - Send broadcast message

### Media Download

Simply send an Instagram or TikTok URL to the bot, and it will download and send the media back to you.

## 🏗️ Architecture Details

### Domain Layer

Contains the core business entities and rules:
- **Entities**: `User`, `Media`, `DownloadRequest`, `Analytics`
- **Repository Interfaces**: Define contracts for data access
- **Domain Services**: Business logic that doesn't fit in entities

### Application Layer

Contains use cases and application-specific business rules:
- **Use Cases**: `DownloadMediaUseCase`, `ManageUserUseCase`, `AnalyticsUseCase`
- **Service Interfaces**: Define contracts for external services
- **DTOs**: Data transfer objects for use case boundaries

### Infrastructure Layer

Contains implementations of external concerns:
- **Repositories**: JSON-based data persistence
- **External Services**: Instagram/TikTok downloaders, rate limiting
- **Telegram Integration**: Bot handlers and notification services

### Presentation Layer

Contains the user interface implementations:
- **Telegram Handlers**: Bot command and message handlers
- **Web API**: FastAPI endpoints for webhooks and monitoring
- **Response Formatters**: Convert domain objects to user-friendly formats

## 🧪 Testing

The clean architecture makes testing straightforward:

```bash
# Run unit tests
python -m pytest tests/unit/

# Run integration tests
python -m pytest tests/integration/

# Run all tests with coverage
python -m pytest --cov=src tests/
```

## 📊 Monitoring

The application includes comprehensive monitoring:

- **Structured Logging**: JSON-formatted logs for easy parsing
- **Metrics Collection**: Usage statistics and performance metrics
- **Error Tracking**: Detailed error reporting with context
- **Health Checks**: Application health monitoring endpoints

## 🔄 Development

### Adding New Features

1. **Domain**: Define new entities or extend existing ones
2. **Application**: Create use cases for new business logic
3. **Infrastructure**: Implement external service integrations
4. **Presentation**: Add new handlers or API endpoints

### Code Quality

- **Linting**: `flake8`, `black`, `isort`
- **Type Checking**: `mypy`
- **Testing**: `pytest` with coverage reporting
- **Documentation**: Comprehensive docstrings

## 🚀 Deployment

### Production Considerations

- Use environment variables for all configuration
- Set up proper logging aggregation
- Configure rate limiting based on your needs
- Monitor application performance and errors
- Set up automatic backups for data files

### Cloud Deployment

The application is cloud-ready and can be deployed on:
- **Azure App Service** (includes specific configurations)
- **AWS Lambda** (with appropriate adapters)
- **Google Cloud Run**
- **Heroku**
- **DigitalOcean**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the architecture principles
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [instaloader](https://github.com/instaloader/instaloader) - Instagram content downloader
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Universal media downloader
- [FastAPI](https://github.com/tiangolo/fastapi) - Modern web framework

## 📞 Support

For support, please create an issue on GitHub or contact the maintainers.
