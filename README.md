# 🧹 Duplicate File Cleaner

A lightweight, fast, and user-friendly Windows tool to find and delete duplicate files. Built with Python and tkinter — **zero external dependencies**.

## ✨ Features

- 🔒 **SHA256 Content Hashing** — Detects true duplicates (byte-for-byte identical), not just same filenames
- ⚡ **Size Pre-Filtering** — Skips impossible matches for maximum speed
- 🎨 **Modern Dark UI** — Clean, intuitive graphical interface
- ✅ **Selective Deletion** — Click to mark individual files, keep one per group, or bulk select
- 💾 **Space Savings Preview** — See recoverable disk space before deleting anything
- 📂 **Recursive Scanning** — Searches all subfolders automatically
- 🧵 **Threaded** — GUI stays responsive during large scans

## 🚀 Quick Start

### Option 1: Run with Python
```bash
python duplicate_cleaner.py