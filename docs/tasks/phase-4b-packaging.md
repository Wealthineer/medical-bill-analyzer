# Phase 4b: Packaging & Distribution - Detailed Tasks

**Status**: 🔄 Not Started
**Estimated Duration**: Weeks 8-9
**Dependencies**: All previous phases must be complete and tested

---

## Overview

Phase 4b packages the application as standalone executables for Windows, macOS, and Linux using PyInstaller. Users should be able to run the app without Python installed.

---

## 4b.1 PyInstaller Configuration

**Status**: 🔄 Pending

### Dependencies to Add:
- [ ] Add `pyinstaller = "^6.0.0"` to dev dependencies

### Files to Create:
- [ ] `packaging/medical-bill-analyzer.spec`
- [ ] `packaging/assets/icon.ico` (Windows)
- [ ] `packaging/assets/icon.icns` (macOS)

### Tasks:
- [ ] Create PyInstaller spec file
- [ ] Configure hidden imports (LLM providers)
- [ ] Bundle data files (config template, README)
- [ ] Set console mode (terminal app)
- [ ] Enable UPX compression
- [ ] Add application icons (optional)

### Spec File Configuration:
```python
hiddenimports=[
    'anthropic',
    'openai',
    'ollama',
    'pdfplumber',
    'textual',
    'medical_bill_analyzer.llm.anthropic_provider',
    'medical_bill_analyzer.llm.openai_provider',
    'medical_bill_analyzer.llm.ollama_provider',
]

datas=[
    ('config.yaml.template', '.'),
    ('README.md', '.'),
]
```

### Testing:
- [ ] Test spec file syntax
- [ ] Verify hidden imports work
- [ ] Check bundled data files

---

## 4b.2 Build Scripts

**Status**: 🔄 Pending

### Files to Create:
- [ ] `scripts/build.sh` (Linux/macOS)
- [ ] `scripts/build.bat` (Windows)

### Tasks:
- [ ] Create build script for Linux/macOS
- [ ] Create build script for Windows
- [ ] Install PyInstaller in script
- [ ] Run tests before building
- [ ] Build with PyInstaller
- [ ] Test executable
- [ ] Report success/failure

### Build Script Steps:
1. Install PyInstaller
2. Run test suite (`pytest`)
3. Build with `pyinstaller medical-bill-analyzer.spec`
4. Test executable (`./dist/medical-bill-analyzer --version`)
5. Report completion

### Testing:
- [ ] Test build script on Linux
- [ ] Test build script on macOS
- [ ] Test build script on Windows
- [ ] Verify executable created
- [ ] Test executable launches

---

## 4b.3 First-Run Experience

**Status**: 🔄 Pending

### Files to Update:
- [ ] `src/medical_bill_analyzer/main.py`
- [ ] `src/medical_bill_analyzer/config/settings.py`

### Tasks:
- [ ] Implement first-run detection
- [ ] Auto-launch setup wizard on first run
- [ ] Create user config directory
- [ ] Initialize database
- [ ] Copy config template
- [ ] Set up logging

### User Directory Structure:
```
~/.medical-bill-analyzer/  (Linux/macOS)
%APPDATA%/medical-bill-analyzer/  (Windows)
├── config.yaml
├── data/
│   ├── medical_bills.db
│   └── pdfs/
└── logs/
    └── app.log
```

### First-Run Flow:
1. Check if config.yaml exists
2. If not: Welcome message, launch setup wizard
3. Setup wizard completes
4. Config and directories created
5. Proceed to TUI or CLI

### Testing:
- [ ] Test first-run detection
- [ ] Test setup wizard auto-launch
- [ ] Test directory creation
- [ ] Test on Windows, macOS, Linux
- [ ] Test subsequent runs (skip setup)

---

## 4b.4 Distribution Packaging

**Status**: 🔄 Pending

### Files to Create:
- [ ] `packaging/GETTING_STARTED.txt`
- [ ] `packaging/README.txt`
- [ ] `packaging/LICENSE.txt`

### Tasks:
- [ ] Write installation instructions for Windows
- [ ] Write installation instructions for macOS
- [ ] Write installation instructions for Linux
- [ ] Create release package structure
- [ ] Include all necessary files

### Release Package Structure:
```
medical-bill-analyzer-v1.0.0-windows.zip
├── medical-bill-analyzer.exe
├── README.txt
├── LICENSE.txt
└── GETTING_STARTED.txt

medical-bill-analyzer-v1.0.0-macos.zip
├── medical-bill-analyzer
├── README.txt
├── LICENSE.txt
└── GETTING_STARTED.txt

medical-bill-analyzer-v1.0.0-linux.tar.gz
├── medical-bill-analyzer
├── README.txt
├── LICENSE.txt
└── GETTING_STARTED.txt
```

### Testing:
- [ ] Test package extraction
- [ ] Verify all files present
- [ ] Test README readability

---

## 4b.5 Executable Testing

**Status**: 🔄 Pending

### Testing Platforms:
- [ ] Windows 10/11 VM (clean, no Python)
- [ ] macOS VM (clean, no Python)
- [ ] Ubuntu/Debian VM (clean, no Python)

### Tests to Perform:
- [ ] Executable launches
- [ ] `--version` command works
- [ ] `--help` command works
- [ ] Setup wizard completes
- [ ] Config created in correct location
- [ ] Database created successfully
- [ ] Can add bills
- [ ] Can list bills
- [ ] TUI launches (if supported)
- [ ] CLI commands work

### Testing Checklist:
- [ ] Test on clean Windows 10/11
- [ ] Test on clean macOS (latest)
- [ ] Test on clean Ubuntu/Debian
- [ ] Test first-run setup wizard
- [ ] Test adding sample bill
- [ ] Test CLI commands
- [ ] Test TUI launch
- [ ] Test database persistence
- [ ] Test across reboots

---

## 4b.6 Size Optimization

**Status**: 🔄 Pending

### Tasks:
- [ ] Enable UPX compression in spec file
- [ ] Exclude unnecessary modules
- [ ] Strip debug symbols
- [ ] Test "onedir" vs. "onefile" modes
- [ ] Measure executable size
- [ ] Consider "lite" build (CLI only, no TUI)

### Size Targets:
- [ ] Base (Python + core): ~50-80 MB
- [ ] With TUI: +10-15 MB
- [ ] Total target: <100 MB

### Optimization Strategies:
- [ ] Use `--exclude-module` for unused packages
- [ ] Use UPX compression (`upx=True`)
- [ ] Consider "onedir" if "onefile" too large
- [ ] Create separate "lite" build without TUI

### Testing:
- [ ] Measure Windows executable size
- [ ] Measure macOS executable size
- [ ] Measure Linux executable size
- [ ] Test compressed vs. uncompressed
- [ ] Verify functionality after optimization

---

## 4b.7 GitHub Actions CI/CD (Optional)

**Status**: 🔄 Pending

### Files to Create:
- [ ] `.github/workflows/build.yml`
- [ ] `.github/workflows/test.yml`

### Tasks:
- [ ] Create test workflow (run on push/PR)
- [ ] Create build workflow (run on release)
- [ ] Configure matrix builds (Windows, macOS, Linux)
- [ ] Upload artifacts to GitHub Releases
- [ ] Add badges to README

### Test Workflow:
- Run on: push, pull_request
- Steps: checkout, setup Python, install deps, run pytest

### Build Workflow:
- Run on: release created
- Steps: checkout, setup Python, install deps, run tests, build executable, upload artifact

### Testing:
- [ ] Test workflow syntax
- [ ] Test on push (test workflow)
- [ ] Test on release (build workflow)
- [ ] Verify artifacts uploaded
- [ ] Test downloading and running artifacts

---

## 4b.8 Release Packaging

**Status**: 🔄 Pending

### Tasks:
- [ ] Create release checklist
- [ ] Tag release version (e.g., v1.0.0)
- [ ] Build executables for all platforms
- [ ] Create release packages (zip/tar.gz)
- [ ] Write release notes
- [ ] Upload to GitHub Releases
- [ ] Test downloads

### Release Checklist:
- [ ] All tests pass
- [ ] Version number updated
- [ ] CHANGELOG.md updated
- [ ] Documentation updated
- [ ] Executables built for Windows, macOS, Linux
- [ ] Release packages created
- [ ] Release notes written
- [ ] GitHub Release created
- [ ] Artifacts uploaded
- [ ] Downloads tested

### Testing:
- [ ] Download Windows package
- [ ] Download macOS package
- [ ] Download Linux package
- [ ] Extract and test each
- [ ] Verify release notes accurate

---

## 4b.9 Installation Documentation

**Status**: 🔄 Pending

### Files to Update:
- [ ] `docs/installation.md`
- [ ] `packaging/GETTING_STARTED.txt`

### Tasks:
- [ ] Write Windows installation instructions
- [ ] Write macOS installation instructions
- [ ] Write Linux installation instructions
- [ ] Include troubleshooting section
- [ ] Add screenshots/examples
- [ ] Document first-run setup

### Documentation Sections:
- [ ] System requirements
- [ ] Download instructions
- [ ] Installation steps (per platform)
- [ ] First-run setup
- [ ] Basic usage examples
- [ ] Troubleshooting
- [ ] Uninstallation instructions

### Testing:
- [ ] Follow instructions on Windows
- [ ] Follow instructions on macOS
- [ ] Follow instructions on Linux
- [ ] Verify accuracy
- [ ] Get feedback from test users

---

## Phase 4b Acceptance Criteria

- [ ] ✅ Can build standalone executable for Windows, macOS, Linux
- [ ] ✅ Executable runs on clean machine without Python installed
- [ ] ✅ Setup wizard works correctly on first run
- [ ] ✅ Config and data stored in appropriate user directory (not app directory)
- [ ] ✅ Executable size <100 MB
- [ ] ✅ Clear installation instructions for each platform
- [ ] ✅ Version information accessible via `--version`
- [ ] ✅ All Phase 1-4a functionality works in packaged executable

---

## Notes

- **Platform Testing**: Critical to test on clean VMs without Python
- **User Directory**: Config/data must be in user directory, not app directory
- **Size**: Target <100 MB, but functionality > size
- **Documentation**: Clear instructions essential for non-technical users
- **Updates**: Manual download approach (no auto-update for v1.0)
- **Code Signing**: Optional for v1.0 (macOS may show warning)

---

Last Updated: 2025-12-12
