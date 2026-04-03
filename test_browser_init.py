#!/usr/bin/env python3
"""
Standalone Browser Initialization Test Script
Run this directly to test if Playwright browser can be initialized
Works on Windows, Linux, and macOS
"""

import sys
import platform
import os
from pathlib import Path
from datetime import datetime

# Setup logging
log_file = Path(__file__).parent / "test_browser_init.log"
log_lines = []

def log(message):
    """Print and log message"""
    print(message)
    log_lines.append(message)

def save_log():
    """Save log to file"""
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(log_lines))

# ============================================================================
# SECTION 1: ENVIRONMENT CHECK
# ============================================================================

log("=" * 70)
log("🔍 BROWSER INITIALIZATION TEST")
log("=" * 70)
log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log("")

log("📋 ENVIRONMENT INFO")
log("-" * 70)
log(f"Python Version: {sys.version}")
log(f"Python Executable: {sys.executable}")
log(f"Platform: {platform.system()} {platform.release()}")
log(f"Architecture: {platform.machine()}")
log(f"Current Directory: {os.getcwd()}")
log("")

# ============================================================================
# SECTION 2: CHECK PLAYWRIGHT INSTALLATION
# ============================================================================

log("📦 CHECKING PLAYWRIGHT INSTALLATION")
log("-" * 70)

try:
    import playwright
    log(f"✅ Playwright module found")
    try:
        log(f"   Version: {playwright.__version__}")
    except AttributeError:
        log(f"   Version: (version info not available)")
except ImportError as e:
    log(f"❌ Playwright not installed!")
    log(f"   Error: {e}")
    log("")
    log("SOLUTION: Run in PowerShell/CMD:")
    log("   cd C:\\path\\to\\luxury-cars-scraper")
    log("   python -m playwright install chromium")
    save_log()
    sys.exit(1)

log("")

# ============================================================================
# SECTION 3: CHECK PLAYWRIGHT SYNC API
# ============================================================================

log("🔗 CHECKING PLAYWRIGHT SYNC API")
log("-" * 70)

try:
    from playwright.sync_api import sync_playwright
    log("✅ sync_playwright imported successfully")
except ImportError as e:
    log(f"❌ Failed to import sync_playwright!")
    log(f"   Error: {e}")
    save_log()
    sys.exit(1)

log("")

# ============================================================================
# SECTION 4: CHECK CHROMIUM BINARY
# ============================================================================

log("🔍 CHECKING CHROMIUM BINARY")
log("-" * 70)

if platform.system() == "Windows":
    log("💻 Windows detected - checking Playwright cache directory")
    playwright_cache = Path.home() / ".cache" / "ms-playwright"
    if playwright_cache.exists():
        log(f"✅ Playwright cache found: {playwright_cache}")
        chromium_exe = list(playwright_cache.glob("**/chrome.exe"))
        if chromium_exe:
            log(f"✅ Chromium executable found: {chromium_exe[0]}")
        else:
            log("⚠️  Chromium executable not found in cache (will be downloaded on first use)")
    else:
        log("⚠️  Playwright cache not found (will be created on first use)")
else:
    log(f"🐧 {platform.system()} detected - checking system PATH")
    import shutil
    chromium_path = shutil.which("chromium") or shutil.which("chromium-browser")
    if chromium_path:
        log(f"✅ Chromium executable found: {chromium_path}")
    else:
        log("⚠️  Chromium executable not in PATH (will use bundled version)")

log("")

# ============================================================================
# SECTION 5: INITIALIZE PLAYWRIGHT CONTEXT
# ============================================================================

log("🚀 INITIALIZING PLAYWRIGHT CONTEXT")
log("-" * 70)

try:
    log("🔄 Starting sync_playwright()...")
    playwright_obj = sync_playwright().start()
    log("✅ sync_playwright() started successfully")
except Exception as e:
    log(f"❌ Failed to start sync_playwright!")
    log(f"   Error: {e}")
    import traceback
    log(f"   Traceback: {traceback.format_exc()}")
    save_log()
    sys.exit(1)

log("")

# ============================================================================
# SECTION 6: LAUNCH BROWSER
# ============================================================================

log("🔄 LAUNCHING CHROMIUM BROWSER")
log("-" * 70)

try:
    log("🔄 Launching browser...")
    log(f"   Platform: {platform.system()}")
    
    # Windows-specific args
    browser_args = [
        "--disable-blink-features=AutomationControlled",
    ]
    
    # Add platform-specific args (not for Windows)
    if platform.system() != "Windows":
        browser_args.extend([
            "--disable-dev-shm-usage",
            "--no-sandbox",
        ])
        log(f"   Args (Linux): {browser_args}")
    else:
        log(f"   Args (Windows): {browser_args}")
    
    browser = playwright_obj.chromium.launch(
        headless=True,
        args=browser_args,
    )
    log("✅ Browser launched successfully!")
except FileNotFoundError as e:
    log(f"❌ Chromium binary not found!")
    log(f"   Error: {e}")
    log("")
    log("SOLUTION: Install Playwright chromium binaries:")
    log("   python -m playwright install chromium")
    log("")
    log("Or full install with dependencies:")
    log("   python -m playwright install --with-deps")
    save_log()
    sys.exit(1)
except Exception as e:
    log(f"❌ Failed to launch browser!")
    log(f"   Error: {e}")
    import traceback
    log(f"   Traceback: {traceback.format_exc()}")
    log("")
    log("SOLUTION: This usually means Playwright binaries need to be installed:")
    log("   python -m playwright install --with-deps")
    save_log()
    sys.exit(1)

log("")

# ============================================================================
# SECTION 7: CREATE PAGE/TAB
# ============================================================================

log("📄 CREATING BROWSER PAGE")
log("-" * 70)

try:
    log("🔄 Creating new page...")
    page = browser.new_page()
    log("✅ Page created successfully!")
except Exception as e:
    log(f"❌ Failed to create page!")
    log(f"   Error: {e}")
    import traceback
    log(f"   Traceback: {traceback.format_exc()}")
    browser.close()
    playwright_obj.stop()
    save_log()
    sys.exit(1)

log("")

# ============================================================================
# SECTION 8: TEST NAVIGATION
# ============================================================================

log("🌐 TESTING NAVIGATION")
log("-" * 70)

try:
    log("🔄 Navigating to https://www.google.com...")
    page.goto("https://www.google.com", timeout=30000)
    log("✅ Navigation successful!")
    
    title = page.title()
    log(f"   Page title: {title}")
except Exception as e:
    log(f"⚠️  Navigation failed (but browser works)!")
    log(f"   Error: {e}")
    log("   This might be a network issue, not a browser issue")

log("")

# ============================================================================
# SECTION 9: CLEANUP
# ============================================================================

log("🧹 CLEANING UP")
log("-" * 70)

try:
    page.close()
    log("✅ Page closed")
    browser.close()
    log("✅ Browser closed")
    playwright_obj.stop()
    log("✅ Playwright stopped")
except Exception as e:
    log(f"⚠️  Cleanup error: {e}")

log("")

# ============================================================================
# FINAL RESULT
# ============================================================================

log("=" * 70)
log("✅ ALL TESTS PASSED!")
log("=" * 70)
log("")
log("Browser initialization is working correctly!")
log("You can now run the pipeline:")
log("   python run_pipeline_IMPROVED.py")
log("")
log(f"Log saved to: {log_file}")
log("")

save_log()
