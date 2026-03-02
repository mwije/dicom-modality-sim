# Copyright (c) 2026 Malinda Wijeratne
# SPDX-License-Identifier: MIT

import os
from config.settings import ModalityConfig
from services.association_service import DicomAssociationFactory
from services.worklist_service import WorklistService
from services.storage_service import StorageService
from services.mpps_service import MPPSService
from services.verification_service import VerificationService
from core.image_acquisition import ImageAcquisitionService
from core.dicom_builder import DicomBuilder, MODALITY_SOP_CLASS
from ui.menu_handlers import show_main_menu, show_worklist_table, show_config

class ModalitySimulatorCLI:
    """Command-line interface for DICOM Modality Simulator"""
    
    def __init__(self, config):
        self.config = config
        
        # Initialize services
        self.assoc_factory = DicomAssociationFactory(config)
        self.worklist_svc = WorklistService(config)
        self.storage_svc = StorageService(config)
        self.mpps_svc = MPPSService(config)
        self.verification_svc = VerificationService(self.assoc_factory)
        self.image_acq = ImageAcquisitionService(config)
        self.dicom_builder = DicomBuilder(config)
        
        # State
        self.current_worklist = []
        self.filtered_worklist = []
        self.selected_item = None
        self.fulfill_order = True
        self.current_mpps_uid = None
        self.first_run = True
    
    def run(self):
        """Main interactive loop"""
        self.clear_screen()
        if self.first_run:
            self.config.display()
            if self.config.verify_connection:
                self.verification_svc.verify_connection()
            self.first_run = False
        
        while True:
            show_main_menu(self.selected_item, self.selection_details())
            choice = input("\nSelect option: ").strip().upper()
            self.clear_screen()
            if choice == '1':
                self.filtered_worklist = self.worklist_svc.query(
                    assoc_factory=self.assoc_factory,
                    server_host=self.config.pacs_mwl_host,
                    server_port=self.config.pacs_mwl_port,
                    client_ae_title=self.config.ae_title,
                    server_ae_title=self.config.pacs_mwl_ae_title,
                    modality_filter=None,
                    ae_filter=None,
                    )
            elif choice in ['', '2', 'ENTER']:
                show_worklist_table(self.filtered_worklist)
            elif choice == '3':
                self.select_patient()
            elif choice == '4':
                self.perform_acquisition()
            elif choice == '5':
                self.mpps_testing_menu()
            elif choice == '6':
                self.config.display()
            elif choice == 'C':
                self.config.display()
                self.configuration_menu()
            elif choice in ['E', '0']:
                self.verification_svc.verify_connection(
                    server_host=self.config.pacs_mwl_host,
                    server_port=self.config.pacs_mwl_port,
                    server_ae_title=self.config.pacs_mwl_ae_title,
                    client_ae_title=self.config.ae_title
                )

                if (self.config.pacs_mwl_ae_title != self.config.pacs_store_ae_title):
                    self.verification_svc.verify_connection(
                        server_host=self.config.pacs_store_host,
                        server_port=self.config.pacs_store_port,
                        server_ae_title=self.config.pacs_store_ae_title,
                        client_ae_title=self.config.ae_title
                    )
            elif choice == 'P':
                self.profile_management_menu()
            elif choice == 'Q':
                print("\nExiting...")
                break
            else:
                print("Invalid option. Try again.")
    
    def selection_details(self):
        name = getattr(self.selected_item, 'PatientName', 'Unknown')
        sex = getattr(self.selected_item, 'PatientSex', '')
        if sex:
            name = f"{name}({sex})"

        birthdate = getattr(self.selected_item, 'PatientBirthDate', '')
        if birthdate:
            name = f"{name} {birthdate}"

        study = getattr(self.selected_item, 'AccessionNumber', '')
        if self.fulfill_order == True:
            study_uid = getattr(self.selected_item, 'StudyInstanceUID', '')

            if study_uid:
                study = f"          [{study}]\n{study_uid}"
            
        info = f"{name}\n{study}"

        return info

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def select_patient(self):
        """Select patient from worklist"""
        if not self.filtered_worklist:
            print("No worklist items available.")
            return False        

        show_worklist_table(self.filtered_worklist)
        try:
            choice = input("Select item number (or ENTER to cancel): ").strip()
            if not choice:
                return False
            index = int(choice) - 1
        except ValueError:
            print("Invalid selection.")
            return False
        
        if 0 <= index < len(self.filtered_worklist):
            self.selected_item = self.filtered_worklist[index]
            name = getattr(self.selected_item, 'PatientName', 'Unknown')
            pid = getattr(self.selected_item, 'PatientID', 'Unknown')
            print(f"\n✓ Selected: {name} (ID: {pid})")
            
            print("\n=== Study Assignment ===")
            print("1. Fulfill this order (use MWL Study UID) - DEFAULT")
            print("2. Related imaging (generate new Study UID)")
            fulfill = input("Select [1]: ").strip()
            
            if fulfill == '2':
                self.fulfill_order = False
                print("→ Will create new related study")
            else:
                self.fulfill_order = True
                print("→ Will fulfill scheduled order")
            
            return True
        else:
            print("Invalid selection.")
            return False
    
    def perform_acquisition(self):
        """Perform acquisition workflow"""
        if not self.selected_item:
            print("\n✗ No worklist item selected. Select one first.")
            return
        
        # MPPS Update - In progress
        if self.config.mpps_enabled:
            self.current_mpps_uid = self.mpps_svc.send_in_progress(
                assoc_factory=self.assoc_factory,
                mwl_item=self.selected_item,
                server_host=self.config.pacs_mwl_host,
                server_port=self.config.pacs_mwl_port,
                client_ae_title=self.config.ae_title,
                server_ae_title=self.config.pacs_mwl_ae_title
                )

        # Acquire image
        image = self.image_acq.acquire(self.selected_item)
        if image is None:
            return
        
        # Create DICOM
        print("\nCreating DICOM file...")
        ds = self.dicom_builder.create_dicom_from_image(image, self.selected_item, self.fulfill_order)
        
        # Save locally if configured
        self.storage_svc.save_local(ds)
        
        # Send to PACS
        success = self.storage_svc.send_to_pacs(
            self.assoc_factory,
            ds,
            server_host=self.config.pacs_store_host,
            server_port=self.config.pacs_store_port,
            client_ae_title=self.config.ae_title,
            server_ae_title=self.config.pacs_store_ae_title
            )
        
        if success and self.config.auto_acquire:
            # Clear selection for next acquisition
            self.selected_item = None
            
            # MPPS Update - Completed
            if self.config.mpps_enabled:
                self.mpps_svc.send_completed(
                    assoc_factory=self.assoc_factory,
                    mpps_uid=self.current_mpps_uid,
                    dicom_instance=ds,
                    server_host=self.config.pacs_mwl_host,
                    server_port=self.config.pacs_mwl_port,
                    client_ae_title=self.config.ae_title,
                    server_ae_title=self.config.pacs_mwl_ae_title
                )
        else:
            # MPPS Update - Failed
            if self.config.mpps_enabled:
                self.mpps_svc.send_discontinued(
                    assoc_factory=self.assoc_factory,
                    mpps_uid=self.current_mpps_uid,
                    dicom_instance=ds,
                    server_host=self.config.pacs_mwl_host,
                    server_port=self.config.pacs_mwl_port,
                    client_ae_title=self.config.ae_title,
                    server_ae_title=self.config.pacs_mwl_ae_title,
                    reason='Acquisition failed'
                    )
    
    def mpps_testing_menu(self):
        """MPPS testing menu"""
        if not self.selected_item:
            print("✗ No worklist item selected. Select one first.")
            return
        
        while True:
            print("\n" + "=" * 50)
            print("MPPS TESTING MENU".center(50))
            print("=" * 50)
            print(f"Current MPPS UID: {str(self.current_mpps_uid) if self.current_mpps_uid else 'None'}")
            print(f"Selected : {self.selection_details()}")
            print("-" * 50)
            print("1. Send IN PROGRESS (N-CREATE)")
            print("2. Send COMPLETED (N-SET)")
            print("3. Send DISCONTINUED (N-SET)")
            print("4. Clear MPPS UID")
            print("0. Back to Main Menu")
            print("=" * 50)
            
            choice = input("\nSelect action: ").strip()

            self.clear_screen()
            if choice == '1':
                uid = self.mpps_svc.send_in_progress(
                    assoc_factory=self.assoc_factory,
                    mwl_item=self.selected_item,
                    server_host=self.config.pacs_mwl_host,
                    server_port=self.config.pacs_mwl_port,
                    client_ae_title=self.config.ae_title,
                    server_ae_title=self.config.pacs_mwl_ae_title
                    )
                if uid:
                    self.current_mpps_uid = uid
            
            elif choice == '2':
                if not self.current_mpps_uid:
                    print("✗ Send IN PROGRESS first")
                    continue
                
                self.mpps_svc.send_completed(
                    assoc_factory=self.assoc_factory,
                    mpps_uid=self.current_mpps_uid,
                    dicom_instance=None,
                    server_host=self.config.pacs_mwl_host,
                    server_port=self.config.pacs_mwl_port,
                    client_ae_title=self.config.ae_title,
                    server_ae_title=self.config.pacs_mwl_ae_title
                )
                
            elif choice == '3':
                if not self.current_mpps_uid:
                    print("✗ No active MPPS")
                    continue

                reason = input("Discontinuation reason (optional): ").strip()

                self.mpps_svc.send_discontinued(
                    assoc_factory=self.assoc_factory,
                    mpps_uid=self.current_mpps_uid,
                    dicom_instance=None,
                    server_host=self.config.pacs_mwl_host,
                    server_port=self.config.pacs_mwl_port,
                    client_ae_title=self.config.ae_title,
                    server_ae_title=self.config.pacs_mwl_ae_title
                )

            elif choice == '4':
                self.current_mpps_uid = None
                print("✓ MPPS UID cleared")
            
            elif choice in ['0', 'Q']:
                break
            
            else:
                print("Invalid option")
    
    def configuration_menu(self):
        """Configuration menu"""
        while True:
            show_config(self.config)
            choice = input("\nConfig option (S=save / Q=return): ").strip().upper()
            self.clear_screen()
            if choice == '1':
                self.config.pacs_store_host = input(f"PACS Host [{self.config.pacs_store_host}]: ").strip() or self.config.pacs_store_host
                port = input(f"Store Port [{self.config.pacs_store_port}]: ").strip()
                if port:
                    self.config.pacs_store_port = int(port)
                self.config.pacs_store_ae_title = input(f"PACS AE Title [{self.config.pacs_store_ae_title}]: ").strip() or self.config.pacs_store_ae_title

            elif choice == '2':
                self.config.pacs_mwl_host = input(f"PACS Host [{self.config.pacs_mwl_host}]: ").strip() or self.config.pacs_mwl_host
                port = input(f"Store Port [{self.config.pacs_mwl_port}]: ").strip()
                if port:
                    self.config.pacs_mwl_port = int(port)
                self.config.pacs_mwl_ae_title = input(f"PACS AE Title [{self.config.pacs_mwl_ae_title}]: ").strip() or self.config.pacs_mwl_ae_title
                
            elif choice == '3':
                self.config.ae_title = input(f"Client Modality AE Title [{self.config.ae_title}]: ").strip() or self.config.ae_title
                self.config.station_name = input(f"Station Name [{self.config.station_name}]: ").strip() or self.config.station_name
                
            elif choice == '4':
                MODALITY_DISPLAY = ', '.join(MODALITY_SOP_CLASS) + ', * (all)'
                print(f"\nAvailable modalities: {MODALITY_DISPLAY}")
                mod = input(f"Modality [{self.config.modality_type}]: ").strip().upper() or self.config.modality_type

                if mod in MODALITY_SOP_CLASS or mod == '*':
                    self.config.modality_type = mod
                else:
                    print("Invalid modality type. Choose from: {MODALITY_DISPLAY}")
            
            elif choice == '8':
                print("\nFilter Level: query (filter at PACS), display (filter locally), none")
                level = input(f"Filter Level [{self.config.filter_level}]: ").strip().lower() or self.config.filter_level
                if level in ['query', 'display', 'none']:
                    self.config.filter_level = level
                fae = input(f"Filter by AE Title? (yes/no) [{self.config.filter_by_ae}]: ").strip().lower()
                if fae:
                    self.config.filter_by_ae = fae in ['yes', 'y', 'true']
            
            elif choice == '9':
                print("\nAcquisition Sources: webcam, file, default, ask")
                src = input(f"Select Source [{self.config.acquisition_source}]: ").strip().lower() or self.config.acquisition_source
                if src in ['webcam', 'file', 'default', 'ask']:
                    self.config.acquisition_source = src
                else:
                    print("Invalid source")
                color = input(f"Enable color (yes/no) [{self.config.acquisition_colors}]: ").strip().lower()
                if color:
                    self.config.acquisition_colors = color in ['yes', 'y', 'true']

                print("\nAcquisition Image Dimensions (in pixels)")
                w = input(f"Image Width [{self.config.image_width}]: ").strip()
                if w:
                    self.config.image_width = int(w)
                h = input(f"Image Height [{self.config.image_height}]: ").strip()
                if h:
                    self.config.image_height = int(h)

                save = input(f"Save acquired images locally? (yes/no) [{self.config.save_local}]: ").strip().lower()
                if save:
                    self.config.save_local = save in ['yes', 'y', 'true']
                if self.config.save_local:
                    self.config.local_dir = input(f"Local directory for storage [{self.config.local_dir}]: ").strip() or self.config.local_dir

            elif choice == 'P':
                self.profile_management_menu()
            elif choice == 'D':
                self.config.display()
            elif choice in ['Q', 'X']:
                break
            elif choice == 'S':
                self.config.save()
                break
            else:
                print("Invalid option")
    
    def profile_management_menu(self):
        """Profile management menu"""
        
        while True:
            print("\n=== Profile Management ===")
            print("1. List Profiles")
            print("2. Save Current as Profile")
            print("3. Load Profile")
            print("4. Delete Profile")
            print("0. Return")
            
            choice = input("\nProfile option: ").strip()
            self.clear_screen()    
            if choice == '1':
                profiles = ModalityConfig.list_profiles()
                if profiles:
                    print("\nAvailable profiles:")
                    for i, profile in enumerate(profiles, 1):
                        print(f"  {i}. {profile}")
                else:
                    print("\nNo profiles found")

            elif choice == '2':
                name = input("Profile name: ").strip()
                if name:
                    self.config.save_as_profile(name)

            elif choice == '3':
                profiles = ModalityConfig.list_profiles()
                if not profiles:
                    print("\nNo profiles available")
                    continue
                
                print("\nAvailable profiles:")
                for i, profile in enumerate(profiles, 1):
                    print(f"  {i}. {profile}")
                
                choice_num = input("\nSelect profile number: ").strip()

                try:
                    idx = int(choice_num) - 1
                    if 0 <= idx < len(profiles):
                        if self.config.load_from_profile(profiles[idx]):
                            self.config.display()
                            break
                except ValueError:
                    print("Invalid selection")

            elif choice == '4':
                profiles = ModalityConfig.list_profiles()
                if not profiles:
                    print("\nNo profiles available")
                    continue
                
                print("\nAvailable profiles:")
                for i, profile in enumerate(profiles, 1):
                    print(f"  {i}. {profile}")
                
                choice_num = input("\nSelect profile to delete: ").strip()
                try:
                    idx = int(choice_num) - 1
                    if 0 <= idx < len(profiles):
                        profile_path = Path('.profiles') / f"{profiles[idx]}.env"
                        profile_path.unlink()
                        print(f"✓ Profile deleted: {profiles[idx]}")
                except (ValueError, IndexError):
                    print("Invalid selection")

            elif choice in ['0', 'Q']:
                self.clear_screen()
                break
            
            else:
                print("Invalid option")
