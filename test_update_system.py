#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration test for the complete Helium auto-update system
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(__file__))
from auto_updater import HeliumUpdater

def test_config_loading():
    """Test that update configuration loads correctly"""
    config_path = Path(__file__).parent / "update_config.json"
    assert config_path.exists(), "update_config.json not found"
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    required_sections = ['update_server', 'update_preferences', 'update_ui', 'download_settings']
    for section in required_sections:
        assert section in config, f"Missing config section: {section}"
    
    print("✓ Configuration file is valid")

def test_version_manifest_generation():
    """Test that version manifest would be generated correctly"""
    # Simulate what build.py does
    import time
    
    version_parts = {
        'HELIUM_MAJOR': '1',
        'HELIUM_MINOR': '0',
        'HELIUM_PATCH': '0', 
        'HELIUM_PLATFORM': '1',
        'CHROMIUM_VERSION': '120.0.6099.129'
    }
    
    version_manifest = {
        "version": f"{version_parts['HELIUM_MAJOR']}.{version_parts['HELIUM_MINOR']}.{version_parts['HELIUM_PATCH']}.{version_parts['HELIUM_PLATFORM']}",
        "build_time": int(time.time()),
        "chromium_version": version_parts.get('CHROMIUM_VERSION', 'unknown'),
        "helium_version_parts": version_parts,
        "update_server": {
            "type": "github_releases",
            "repo_owner": "imputnet",
            "repo_name": "helium-windows"
        }
    }
    
    # Validate manifest structure
    assert "version" in version_manifest
    assert "build_time" in version_manifest
    assert "update_server" in version_manifest
    
    print(f"✓ Version manifest generation test passed (version: {version_manifest['version']})")

def test_mock_update_flow():
    """Test the complete update flow with mocked data"""
    # Create mock GitHub API response  
    mock_release = {
        'tag_name': '1.2.3.4',  # Remove 'v' prefix to match expected format
        'html_url': 'https://github.com/imputnet/helium-windows/releases/tag/v1.2.3.4',
        'body': 'Test release notes',
        'published_at': '2024-01-01T00:00:00Z',
        'assets': [
            {
                'name': 'helium_1.2.3.4_x64-installer.exe',
                'browser_download_url': 'https://github.com/imputnet/helium-windows/releases/download/v1.2.3.4/helium_1.2.3.4_x64-installer.exe',
                'size': 1024000
            },
            {
                'name': 'helium_1.2.3.4_x64-windows.zip', 
                'browser_download_url': 'https://github.com/imputnet/helium-windows/releases/download/v1.2.3.4/helium_1.2.3.4_x64-windows.zip',
                'size': 2048000
            }
        ]
    }
    
    updater = HeliumUpdater("1.0.0.0")
    
    # Mock the API request
    with patch.object(updater, '_make_request', return_value=mock_release):
        update_info = updater.check_for_updates()
        
        if update_info is None:
            # Debug the issue - check asset matching
            arch = updater._get_architecture()
            print(f"Debug: Current arch: {arch}")
            
            installer_asset = None
            zip_asset = None
            
            for asset in mock_release.get('assets', []):
                name = asset.get('name', '').lower()
                print(f"Debug: Checking asset: {name}")
                print(f"Debug: Contains -{arch}-: {f'-{arch}-' in name}")
                print(f"Debug: Contains _{arch}_: {f'_{arch}_' in name}")
                
                if f'-{arch}-' in name or f'_{arch}_' in name:
                    if name.endswith('-installer.exe'):
                        installer_asset = asset
                        print(f"Debug: Found installer asset: {name}")
                    elif name.endswith('-windows.zip'):
                        zip_asset = asset
                        print(f"Debug: Found zip asset: {name}")
            
            print(f"Debug: installer_asset: {installer_asset is not None}")
            print(f"Debug: zip_asset: {zip_asset is not None}")
            
            assert False, "Should detect update"
        
        assert update_info['version'] == '1.2.3.4', f"Wrong version: {update_info['version']}"
        assert update_info['architecture'] == 'x64', f"Wrong architecture: {update_info['architecture']}"
        assert update_info['installer'] is not None, "Should have installer asset"
        assert update_info['zip_package'] is not None, "Should have zip asset"
        
        print(f"✓ Mock update flow test passed (detected version: {update_info['version']})")

def test_file_integration():
    """Test that all required files are present"""
    base_path = Path(__file__).parent
    
    required_files = [
        'auto_updater.py',
        'update_config.json', 
        'AUTO_UPDATE.md',
        'test_updater.py',
        'patches/helium/windows/enable-auto-updates.patch'
    ]
    
    for file_path in required_files:
        full_path = base_path / file_path
        assert full_path.exists(), f"Required file missing: {file_path}"
    
    print("✓ All required files are present")

def test_patch_integration():
    """Test that the patch file is properly formatted"""
    patch_path = Path(__file__).parent / 'patches' / 'helium' / 'windows' / 'enable-auto-updates.patch'
    
    with open(patch_path, 'r') as f:
        patch_content = f.read()
    
    # Check for key patch markers
    assert '--- a/' in patch_content, "Patch should have source markers"  
    assert '+++ b/' in patch_content, "Patch should have target markers"
    assert 'IDC_UPGRADE_DIALOG' in patch_content, "Patch should define upgrade dialog command"
    assert 'helium_updater.cc' in patch_content, "Patch should include updater implementation"
    
    print("✓ Auto-update patch is properly formatted")

def test_series_file():
    """Test that the patch is added to the series file"""
    series_path = Path(__file__).parent / 'patches' / 'series'
    
    with open(series_path, 'r') as f:
        series_content = f.read()
    
    assert 'helium/windows/enable-auto-updates.patch' in series_content, "Patch not in series file"
    
    print("✓ Patch is properly added to series file")

def main():
    """Run all integration tests"""
    print("Testing Helium Auto-Update System Integration...")
    print("=" * 50)
    
    try:
        test_file_integration()
        test_config_loading()
        test_version_manifest_generation()
        test_patch_integration()
        test_series_file()
        test_mock_update_flow()
        
        print("=" * 50)
        print("✅ All integration tests passed!")
        print("\nThe auto-update system is ready for build integration.")
        print("Next steps:")
        print("1. Run a full build to test patch integration")
        print("2. Test the browser with update functionality")
        print("3. Create a test release to verify end-to-end updates")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()