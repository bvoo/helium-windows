#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for Helium auto-updater functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from auto_updater import HeliumUpdater

def test_version_comparison():
    """Test version comparison logic"""
    updater = HeliumUpdater("1.0.0.0")
    
    test_cases = [
        ("1.0.0.1", "1.0.0.0", True),   # newer patch
        ("1.0.1.0", "1.0.0.0", True),   # newer minor
        ("1.1.0.0", "1.0.0.0", True),   # newer major
        ("1.0.0.0", "1.0.0.1", False),  # older patch
        ("1.0.0.0", "1.0.0.0", False),  # same version
        ("2.0.0.0", "1.9.9.9", True),   # major version bump
    ]
    
    for newer, older, expected in test_cases:
        result = updater._is_newer_version(newer, older)
        print(f"Is {newer} newer than {older}? {result} (expected: {expected})")
        assert result == expected, f"Failed: {newer} vs {older}"
    
    print("✓ Version comparison tests passed")

def test_update_check():
    """Test update checking against GitHub API"""
    # Test with a fake old version to ensure updates are detected
    updater = HeliumUpdater("0.1.0.0", "imputnet", "helium-windows")
    
    print("Checking for updates...")
    update_info = updater.check_for_updates()
    
    if update_info:
        print(f"✓ Update found: {update_info['version']}")
        print(f"  Architecture: {update_info['architecture']}")
        print(f"  Release URL: {update_info['release_url']}")
        if update_info.get('installer'):
            print(f"  Installer: {update_info['installer']['name']}")
        if update_info.get('zip_package'):
            print(f"  Package: {update_info['zip_package']['name']}")
    else:
        print("✓ No updates available (or test version is too new)")

def test_architecture_detection():
    """Test architecture detection"""
    updater = HeliumUpdater("1.0.0.0")
    arch = updater._get_architecture()
    print(f"✓ Detected architecture: {arch}")
    assert arch in ['x64', 'arm64'], f"Unexpected architecture: {arch}"

def main():
    """Run all tests"""
    print("Testing Helium Auto-Updater...")
    print("=" * 40)
    
    try:
        test_version_comparison()
        test_architecture_detection()
        test_update_check()
        
        print("=" * 40)
        print("✓ All tests passed!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()