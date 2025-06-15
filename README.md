# Manual Support App

AI-powered PDF manual support application with voice summary and Q&A functionality.

## Features

- =Ä PDF manual upload and processing
- <™ AI-generated voice summaries (15,000 characters)
- =¬ Intelligent Q&A with page references
- = RAG (Retrieval-Augmented Generation) powered search
- <¨ Clean, responsive UI

## Tech Stack

- **Backend**: Flask
- **AI/ML**: OpenAI API (GPT-3.5-turbo, TTS-1)
- **RAG**: LangChain + ChromaDB
- **PDF Processing**: pypdf
- **Frontend**: Bootstrap 5 + JavaScript
- **Package Management**: UV

## Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/manual-support-app.git
cd manual-support-app
```

2. **Install dependencies**
```bash
uv sync
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

4. **Run the application**
```bash
uv run python main.py
```

5. **Open in browser**
```
http://localhost:5000
```

## Deployment

See [CLAUDE.md](CLAUDE.md) for detailed deployment instructions for Railway, Render, and other platforms.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.