# Copyright (c) 2026 Malinda Wijeratne
# SPDX-License-Identifier: MIT

import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

class ModalityConfig:
    """Configuration management for DICOM Modality Simulator"""
    """Load and manage configuration from .env file"""

    def __init__(self):
        load_dotenv()
        
        self.pacs_store_host = os.getenv('PACS_STORE_HOST', 'localhost')
        self.pacs_store_port = int(os.getenv('PACS_STORE_PORT', '11112'))
        self.pacs_mwl_host = os.getenv('PACS_MWL_HOST', 'localhost')
        self.pacs_mwl_port = int(os.getenv('PACS_MWL_PORT', '11112'))

        self.pacs_store_ae_title = os.getenv('STORE_AE_TITLE', 'DEMO_PACS')
        self.pacs_mwl_ae_title = os.getenv('MWL_AE_TITLE', 'WORKLIST')
        self.ae_title = os.getenv('AE_TITLE', 'DEMO_MODALITY')
        
        self.modality_type = os.getenv('MODALITY_TYPE', '*')
        self.station_name = os.getenv('STATION_NAME', 'DEMO_STATION_1')
        self.save_local = os.getenv('SAVE_LOCAL', 'false').lower() == 'true'
        self.local_dir = os.getenv('LOCAL_DIR', './dicom_output')
        
        # Workflow settings
        self.transfer_syntax = os.getenv('TRANSFER_SYNTAX', 'explicit')
        self.filter_level = os.getenv('FILTER_LEVEL', 'query')  # 'query', 'display', 'none'
        self.filter_by_ae = os.getenv('FILTER_BY_AE', 'false').lower() == 'true'
        self.verify_connection = os.getenv('VERIFY_CONNECTION', 'true').lower() == 'true'
        self.perform_mpps = os.getenv('PERFORM_MPPS', 'true').lower() == 'true'
        self.mpps_enabled = self.perform_mpps

        # Image settings
        self.image_width = int(os.getenv('IMAGE_WIDTH', '512'))
        self.image_height = int(os.getenv('IMAGE_HEIGHT', '512'))
        self.auto_acquire = os.getenv('AUTO_ACQUIRE', 'false').lower() == 'true'
        
        # Acquisition source
        self.acquisition_source = os.getenv('ACQUISITION_SOURCE', 'webcam')  # webcam, file, default
        self.acquisition_colors = os.getenv('COLOR_ACQUISITION', False)  # color or grayscale
    
    def display(self):
        """Display current configuration"""

        print("\n" + "=" * 50)
        print("CURRENT CONFIGURATION".center(50))
        print("=" * 50)
        print(f"Modality AE Title:      {self.ae_title}")
        print(f"Modality Type:          {self.modality_type} {'(All)' if self.modality_type == '*' else ''}")
        print(f"Station Name:           {self.station_name}")

        print(f"PACS Storage Host:  {self.pacs_store_host}:{self.pacs_store_port}")
        print(f"Store AE Title:     {self.pacs_store_ae_title}")
        print(f"PACS MWL Host:          {self.pacs_mwl_host}:{self.pacs_mwl_port}")
        print(f"MWL AE Title:           {self.pacs_mwl_ae_title}")
        
        print(f"Transfer Syntax:         {self.transfer_syntax}")
        print(f"Query Filter Level:      {self.filter_level}")
        print(f"Filter by AE:            {self.filter_by_ae}")
        
        print(f"Acquisition Source:       {self.acquisition_source}")
        print(f"Color Acquisition:        {self.acquisition_colors}")
        print(f"Image Size:             {self.image_width}x{self.image_height}")
        print(f"Save Local:              {self.save_local}")
    
        if self.save_local:
            print(f"Local Directory:   {self.local_dir}")
        print(f"Auto C-ECHO:             {self.verify_connection}")
        print(f"Auto Perform MPPS:       {self.perform_mpps}")
        print("=" * 50 + "\n")
    
    def get_config(self):
        return [
            "# DICOM Modality Simulator Configuration\n",
            "\n# PACS Connection\n",
            f"PACS_STORE_HOST={self.pacs_store_host}\n",
            f"PACS_MWL_HOST={self.pacs_mwl_host}\n",
            f"PACS_STORE_PORT={self.pacs_store_port}\n",
            f"PACS_MWL_PORT={self.pacs_mwl_port}\n",
            f"\n",
            f"STORE_AE_TITLE={self.pacs_store_ae_title}\n",
            f"MWL_AE_TITLE={self.pacs_mwl_ae_title}\n",
            f"\n",
            "\n# Modality Settings\n",
            f"MODALITY_TYPE={self.modality_type}\n",
            f"STATION_NAME={self.station_name}\n",
            f"AE_TITLE={self.ae_title}\n",
            f"\n",
            "\n# Workflow\n",
            f"TRANSFER_SYNTAX={self.transfer_syntax}\n",
            f"FILTER_LEVEL={self.filter_level}\n",
            f"FILTER_BY_AE={str(self.filter_by_ae).lower()}\n",
            f"\n",
            "\n# Local Storage\n",
            f"SAVE_LOCAL={str(self.save_local).lower()}\n",
            f"LOCAL_DIR={self.local_dir}\n",
            f"\n",
            "\n# Image Settings\n",
            f"ACQUISITION_SOURCE={self.acquisition_source}\n",
            f"COLOR_ACQUISITION={self.acquisition_colors}\n",
            f"IMAGE_WIDTH={self.image_width}\n",
            f"IMAGE_HEIGHT={self.image_height}\n",
            f"\n",
            "\n# Workflow Steps\n",
            f"VERIFY_CONNECTION={str(self.verify_connection).lower()}\n",
            f"PERFORM_MPPS={str(self.perform_mpps).lower()}\n",
        ]
    def save(self):
        """Save current configuration to .env file"""

        config_lines = self.get_config()
        
        with open('.env', 'w') as f:
            f.writelines(config_lines)
        
        print("✓ Configuration saved to .env")
    
    def save_as_profile(self, profile_name):
        """Save current configuration as a named profile"""

        profiles_dir = Path('.profiles')
        profiles_dir.mkdir(exist_ok=True)
        
        profile_path = profiles_dir / f"{profile_name}.env"
        
        config_lines = [
            f"# Profile: {profile_name}\n",
            f"# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"\n",
            *self.get_config()
        ]
        
        with open(profile_path, 'w') as f:
            f.writelines(config_lines)
        
        print(f"✓ Configuration profile saved: {profile_name}")
    
    def load_from_profile(self, profile_name):
        """Load configuration from a named profile"""

        profiles_dir = Path('.profiles')
        profile_path = profiles_dir / f"{profile_name}.env"
        
        if not profile_path.exists():
            print(f"✗ Profile not found: {profile_name}")
            return False
        
        load_dotenv(profile_path, override=True)
        self.__init__()
        
        print(f"✓ Configuration loaded from profile: {profile_name}")
        return True
    
    @staticmethod
    def list_profiles():
        """List all available configuration profiles"""

        profiles_dir = Path('.profiles')

        if not profiles_dir.exists():
            return []
        
        profiles = []
        for profile_file in profiles_dir.glob('*.env'):
            profiles.append(profile_file.stem)
        
        return profiles