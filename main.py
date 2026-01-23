#!/usr/bin/env python3
"""
DICOM Modality Emulator - for RIS/PACS Workflow Testing
"""

import sys
from pathlib import Path
from config.settings import ModalityConfig
from ui.cli import ModalitySimulatorCLI

def create_example_env():
    """Create example .env file if it doesn't exist"""
    env_path = Path('.env')
    if env_path.exists():
        return
    
    example_content = """# DICOM Modality Emulator Configuration

# PACS Connection
PACS_STORE_HOST=127.0.0.1
PACS_MWL_HOST=127.0.0.1
PACS_STORE_PORT=11112
PACS_MWL_PORT=11112

STORE_AE_TITLE=DCM4CHEE
MWL_AE_TITLE=WORKLIST

# Modality Settings
MODALITY_TYPE=*
STATION_NAME=DEMO_STATION_1
AE_TITLE=DEMO1

# Workflow
TRANSFER_SYNTAX=explicit
FILTER_LEVEL=query
FILTER_BY_AE=false

# Local Storage
SAVE_LOCAL=true
LOCAL_DIR=./dicom_output

# Image Settings
ACQUISITION_SOURCE=ask
IMAGE_WIDTH=512
IMAGE_HEIGHT=512

VERIFY_CONNECTION=false
PERFORM_MPPS=true

"""
    
    with open('.env', 'w') as f:
        f.write(example_content)
    
    print("✓ Created example .env file")

def main():
    """Main entry point"""
    create_example_env()
    
    config = ModalityConfig()
    cli = ModalitySimulatorCLI(config)
    
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()
