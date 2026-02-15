# Vocalis - Medical AI Prescription Assistant

🚀 **QUICK START**: `./LAUNCH.sh`

## What is Vocalis?

Vocalis is an AI-powered medical prescription assistant that helps physicians draft prescriptions through a conversational interface.

**Key Features:**
- 💬 Conversational information collection
- 🤖 AI-guided prescription generation  
- ✏️ Edit and review prescriptions
- 🖊️ Digital signature pad
- 📄 PDF export with signature

## Quick Launch

### Easiest Way
```bash
./LAUNCH.sh
```

### Manual Method
```bash
# Terminal 1 - Backend
cd backend && python main.py

# Terminal 2 - Frontend  
cd frontend && flutter run -d chrome
```

## Prerequisites
- Python 3.11+
- Flutter SDK 3.11+
- TinyLlama model (~2GB)

[Full Setup Guide →](QUICKSTART.md)

## Documentation

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | Complete setup & configuration |
| [COMMANDS.md](COMMANDS.md) | Command reference |
| [backend/TEST_REPORT.md](backend/TEST_REPORT.md) | 36 tests (100% PASS) |
| [backend/API_TEST_EXAMPLES.md](backend/API_TEST_EXAMPLES.md) | API examples |

## Project Status

✅ **PRODUCTION READY**

- ✅ Full-featured implementation
- ✅ Comprehensive test suite (36/36 tests)
- ✅ Multi-platform support
- ✅ Complete documentation

## Architecture

```
Frontend (Flutter)          Backend (FastAPI)
├─ Web (Chrome)      ──→    ├─ Information collection
├─ iOS/Android              ├─ Prescription generation  
└─ Desktop           ←──    └─ PDF generation
                              + TinyLlama LLM
```

## API Endpoints

```
GET  /api/health                      Health check
POST /api/collect-prescription-info   Collect patient info
POST /api/generate-prescription       Generate prescription
POST /api/generate-pdf                Export as PDF
```

## How It Works

1. **Chat** - User provides patient information naturally
2. **Collect** - AI extracts and validates data
3. **Generate** - AI creates professional prescription
4. **Review** - User edits if needed
5. **Sign** - Digital signature
6. **Export** - Download as PDF

## Testing

```bash
# Run all tests
cd backend
pytest test_main.py test_advanced.py -v

# Result: ✅ 36/36 PASSED (100%)
```

## Development

```bash
# Backend development
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Frontend development
cd frontend
flutter run -d chrome
```

## Support

- 📖 See [QUICKSTART.md](QUICKSTART.md) for detailed setup
- 🔧 See [COMMANDS.md](COMMANDS.md) for common commands
- 🧪 See [backend/TEST_REPORT.md](backend/TEST_REPORT.md) for test details
- 🐛 Check [QUICKSTART.md](QUICKSTART.md#troubleshooting) for troubleshooting

---

**Ready to launch?** Run `./LAUNCH.sh` or read [QUICKSTART.md](QUICKSTART.md)

Status: 🟢 Production Ready | Tests: ✅ 36/36 | Platforms: 🌐 Web • 📱 Mobile • 💻 Desktop
