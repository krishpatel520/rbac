#!/usr/bin/env python3
"""
Build and upload script for DWERP Common Utils package
"""
import subprocess
import sys
from decouple import config
from bump_version import bump_version

def run_command(cmd, cwd=None):
    """Run command and handle errors"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    print("result \n",result)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    print(result.stdout)
    return result

def clean_build():
    """Clean previous build artifacts"""
    print("Cleaning build artifacts...")
    for path in ["dist", "build", "*.egg-info"]:
        run_command(f"rmdir /s /q {path} 2>nul || echo Cleaned {path}")

def build_package():
    """Build the package"""
    print("Updating tools...")
    run_command("pip install --upgrade setuptools wheel build")
    print("Building package...")
    run_command("py -m build")

def upload_to_nexus(feed_url):
    """Upload to Azure DevOps Artifacts"""
    print("Uploading to Azure DevOps...")
    
    # Install twine if not available
    run_command("py -m pip install twine")
    
    # Upload using twine
    cmd = f'py -m twine upload --repository {feed_url}  dist/*'
    run_command(cmd)

def main():
    """Main build and upload process"""
    # Configuration
    NEXUS_FEED_URL = config('NEXUS_REPO', 'msbc')

    
    if not NEXUS_FEED_URL:
        print("Warning: AZURE_PAT environment variable not set. Upload will be skipped.")
    
    try:
        # Clean previous builds
        clean_build()
        
        # Build package
        build_package()
        
        # Upload to Azure if credentials available
        if NEXUS_FEED_URL:
            upload_to_nexus(NEXUS_FEED_URL)
        else:
            print("Skipping upload - no Azure PAT provided")
            print("To upload manually:")
            print(f"py -m twine upload --repository {NEXUS_FEED_URL}  dist/*")
        
        print("Build completed successfully!")
        
    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    bump_version()
    main()