# Helium Browser Auto-Update System

This document describes the auto-update functionality implemented in Helium Browser for Windows.

## Overview

The auto-update system allows Helium Browser to automatically check for and install new versions. It uses GitHub Releases as the update source and provides a seamless update experience for users.

## Architecture

The auto-update system consists of several components:

### 1. Update Configuration (`update_config.json`)
Contains settings for:
- Update server configuration (GitHub repository details)
- Update preferences (auto-check, auto-download, auto-install)
- UI settings (notifications, menu items)
- Download settings (retries, timeouts, signature verification)

### 2. Auto-Updater Module (`auto_updater.py`)
Core Python module that handles:
- Version checking against GitHub Releases API
- Architecture detection (x64/ARM64)
- Update downloading
- Update installation
- Version comparison logic

### 3. Browser Integration (via patches)
Chromium patches that add:
- Update menu item in the browser
- Update checking functionality
- UI notifications for available updates
- Integration with the auto-updater module

### 4. Version Manifest (`version_manifest.json`)
Generated during build, contains:
- Current version information
- Build timestamp
- Chromium version details
- Update server configuration

## How It Works

1. **Periodic Checks**: The browser periodically checks for updates (default: every 24 hours)
2. **Version Comparison**: Compares current version with latest GitHub release using semantic versioning
3. **Architecture Matching**: Finds the appropriate installer/package for the current architecture (x64/ARM64)
4. **User Notification**: Shows notification or menu badge when updates are available
5. **Download & Install**: Downloads and installs updates based on user preferences

## Configuration

Edit `update_config.json` to customize update behavior:

```json
{
  "update_preferences": {
    "auto_check": true,        // Automatically check for updates
    "auto_download": false,    // Automatically download updates
    "auto_install": false,     // Automatically install updates
    "notify_user": true,       // Show notifications
    "include_prereleases": false  // Include pre-release versions
  }
}
```

## Manual Update Check

Users can manually check for updates through:
- Browser menu: **Settings** → **About** → **Check for Updates**
- Command line: `python auto_updater.py <current_version>`

## Architecture Support

The auto-updater supports both:
- **x64** (Intel/AMD 64-bit)
- **ARM64** (ARM 64-bit)

It automatically detects the current architecture and downloads the appropriate installer.

## File Naming Convention

The system expects GitHub release assets to follow this naming pattern:
- Installers: `helium_<version>_<arch>-installer.exe`
- Packages: `helium_<version>_<arch>-windows.zip`

Where:
- `<version>` is the version number (e.g., "1.0.0.1")
- `<arch>` is the architecture ("x64" or "arm64")

## Security Considerations

- All downloads are performed over HTTPS
- File integrity is verified using checksums when available
- Update signatures are verified (when `verify_signatures` is enabled)
- Users are notified before any automatic installations

## Development & Testing

### Testing the Auto-Updater

Run the test suite:
```bash
python test_updater.py
```

### Manual Testing

Test update checking with a fake old version:
```bash
python auto_updater.py 0.1.0.0
```

### Build Integration

The auto-updater is automatically included in builds:
1. `auto_updater.py` is copied to the build directory
2. `update_config.json` is included
3. `version_manifest.json` is generated with current version info
4. Browser patches enable the update UI

## Troubleshooting

### Common Issues

1. **No updates found**: Check if GitHub Releases exist with proper naming
2. **403 Forbidden**: GitHub API rate limiting - wait or use authentication
3. **Architecture mismatch**: Ensure releases include both x64 and ARM64 builds
4. **Installation fails**: Check if installer runs with `/S` (silent) flag
5. **Version parsing errors**: Ensure versions follow semantic versioning (x.y.z.w)

### Debug Information

Enable debug logging by setting environment variable:
```bash
set HELIUM_UPDATE_DEBUG=1
```

## Integration with Build System

The auto-update system is integrated into the build process:

1. **Version Manifest Generation**: `build.py` generates `version_manifest.json`
2. **File Copying**: Auto-updater files are copied to build output
3. **Patch Application**: Browser patches are applied during build
4. **Configuration**: Update configuration is included in final package

## Future Enhancements

Potential improvements:
- Delta updates (only download changed files)
- Background downloads
- Rollback functionality
- Update channels (stable, beta, dev)
- Bandwidth throttling
- Update scheduling
- Enterprise policy support