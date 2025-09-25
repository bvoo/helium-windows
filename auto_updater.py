#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2025 The Helium Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.

"""
Auto-updater module for Helium Browser on Windows
"""

import json
import urllib.request
import urllib.error
import sys
import platform
from pathlib import Path
from typing import Dict, Optional, Tuple
import subprocess
import tempfile
import shutil

class HeliumUpdater:
    """Handles automatic updates for Helium Browser"""
    
    def __init__(self, current_version: str, repo_owner: str = "imputnet", repo_name: str = "helium-windows"):
        self.current_version = current_version
        self.repo_owner = repo_owner 
        self.repo_name = repo_name
        self.github_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.user_agent = f"Helium-Browser-Updater/{current_version}"
        
    def _get_architecture(self) -> str:
        """Determine the current architecture"""
        arch = platform.machine().lower()
        if arch in ('amd64', 'x86_64'):
            return 'x64'
        elif arch in ('arm64', 'aarch64'):
            return 'arm64'
        else:
            return 'x64'  # Default fallback
    
    def _make_request(self, url: str) -> Optional[Dict]:
        """Make a request to GitHub API with proper headers"""
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', self.user_agent)
            req.add_header('Accept', 'application/vnd.github.v3+json')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        except (urllib.error.URLError, json.JSONDecodeError, Exception) as e:
            print(f"Error making request to {url}: {e}")
            return None
    
    def check_for_updates(self) -> Optional[Dict]:
        """Check if a newer version is available"""
        latest_release = self._make_request(f"{self.github_api_url}/releases/latest")
        if not latest_release:
            return None
            
        latest_version = latest_release.get('tag_name', '').lstrip('v')
        if not latest_version:
            return None
            
        # Simple version comparison (assumes semantic versioning)
        if self._is_newer_version(latest_version, self.current_version):
            arch = self._get_architecture()
            
            # Find the appropriate installer for this architecture
            installer_asset = None
            zip_asset = None
            
            for asset in latest_release.get('assets', []):
                name = asset.get('name', '').lower()
                # Match patterns like "helium_1.2.3.4_x64-installer.exe" or "helium_1.2.3.4_x64-windows.zip"
                if f'_{arch}-' in name or f'-{arch}-' in name or f'_{arch}_' in name:
                    if name.endswith('-installer.exe'):
                        installer_asset = asset
                    elif name.endswith('-windows.zip'):
                        zip_asset = asset
            
            if installer_asset or zip_asset:
                return {
                    'version': latest_version,
                    'release_notes': latest_release.get('body', ''),
                    'release_url': latest_release.get('html_url'),
                    'published_at': latest_release.get('published_at'),
                    'installer': installer_asset,
                    'zip_package': zip_asset,
                    'architecture': arch
                }
        
        return None
    
    def _is_newer_version(self, version1: str, version2: str) -> bool:
        """Compare two version strings (simple semantic versioning)"""
        try:
            def parse_version(v):
                # Handle versions like "1.2.3.4" or "1.2.3-beta.1"
                v = v.split('-')[0]  # Remove pre-release suffix
                return [int(x) for x in v.split('.')]
            
            v1_parts = parse_version(version1)
            v2_parts = parse_version(version2)
            
            # Pad shorter version with zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            return v1_parts > v2_parts
        except ValueError:
            # If version parsing fails, assume no update available
            return False
    
    def download_update(self, update_info: Dict, progress_callback=None) -> Optional[str]:
        """Download the update installer/package"""
        asset = update_info.get('installer') or update_info.get('zip_package')
        if not asset:
            return None
            
        download_url = asset.get('browser_download_url')
        if not download_url:
            return None
            
        filename = asset.get('name')
        temp_dir = tempfile.gettempdir()
        local_path = Path(temp_dir) / filename
        
        try:
            req = urllib.request.Request(download_url)
            req.add_header('User-Agent', self.user_agent)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                
                with open(local_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded, total_size)
            
            return str(local_path)
        except Exception as e:
            print(f"Error downloading update: {e}")
            if local_path.exists():
                local_path.unlink()
            return None
    
    def install_update(self, installer_path: str) -> bool:
        """Install the downloaded update"""
        try:
            if installer_path.endswith('.exe'):
                # Run the installer silently
                result = subprocess.run([installer_path, '/S'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=300)
                return result.returncode == 0
            elif installer_path.endswith('.zip'):
                # For zip packages, we could implement extraction logic
                # For now, just return False to indicate manual installation needed
                return False
            return False
        except Exception as e:
            print(f"Error installing update: {e}")
            return False
    
    def cleanup_download(self, file_path: str):
        """Clean up downloaded files"""
        try:
            Path(file_path).unlink()
        except Exception:
            pass


def main():
    """CLI interface for testing the updater"""
    if len(sys.argv) != 2:
        print("Usage: python auto_updater.py <current_version>")
        sys.exit(1)
    
    current_version = sys.argv[1]
    updater = HeliumUpdater(current_version)
    
    print(f"Checking for updates (current version: {current_version})...")
    update_info = updater.check_for_updates()
    
    if update_info:
        print(f"New version available: {update_info['version']}")
        print(f"Architecture: {update_info['architecture']}")
        if update_info.get('installer'):
            print(f"Installer: {update_info['installer']['name']}")
        if update_info.get('zip_package'):
            print(f"Package: {update_info['zip_package']['name']}")
        print(f"Release URL: {update_info['release_url']}")
    else:
        print("No updates available")


if __name__ == '__main__':
    main()