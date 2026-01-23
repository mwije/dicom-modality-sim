"""Menu display and navigation utilities"""

def show_main_menu(selected_item=None, selection_details=None):
    """Display main menu"""
    
    print("\n" + "=" * 50)
    print("DICOM Modality Emulator".center(50))
    print("=" * 50)
    if selection_details:
        print(f"Selected: {selection_details}".center(50))
        print("-" * 50)
    print("E - DICOM C-ECHO (Verify PACS)")
    print("1 - Query Worklist")
    print("2 - View Worklist (DEFAULT)")
    print("3 - Select Patient")
    print("4 - Perform Acquisition")
    print("5 - Perform MPPS")
    print("6 - Show Configuration")
    print("C - Configure Settings")
    print("P - Profile Management")
    print("Q - Exit")
    print("=" * 50)

def show_worklist_table(filtered_worklist):
    """Display current worklist"""

    if not filtered_worklist:
        print("\nNo worklist items available.")
    
    print("\n" + "=" * 80)
    print("WORKLIST".center(80))
    print("=" * 80)
    print(f"{'#':<4} {'Patient Name':<25} {'ID':<12} {'Mod':<5} {'AE Title':<15} {'Acc#':<10}")
    print("-" * 80)
    
    for i, item in enumerate(filtered_worklist):
        name = str(getattr(item, 'PatientName', 'Unknown'))[:24]
        pid = str(getattr(item, 'PatientID', 'Unknown'))[:11]
        sps = item.ScheduledProcedureStepSequence[0] if hasattr(item, 'ScheduledProcedureStepSequence') else None
        modality = str(getattr(sps, 'Modality', 'N/A') if sps else 'N/A')[:4]
        ae_title = str(getattr(sps, 'ScheduledStationAETitle', 'N/A') if sps else 'N/A')[:14]
        accession = str(getattr(item, 'AccessionNumber', 'N/A'))[:9]
        
        print(f"{i+1:<4} {name:<25} {pid:<12} {modality:<5} {ae_title:<15} {accession:<10}")
    
    print("=" * 80 + "\n")

def show_config(config):
    """Configuration menu"""
    
    print("\n" + "=" * 50)
    print("CONFIGURATION MENU".center(50))
    print("=" * 50)
    print("1. PACS Store")
    print("2. PACS MWL")
    print("3. Client Modality")
    print("4. Modality Type")
    print("8. Query Filter Settings")
    print("9. Image Acquisition")
    print("P. Profile Management")
    print("D. Display Current Config")
    print("=" * 50)
    
def prompt_fulfill_or_related():
    """Prompt for fulfill order vs related study"""

    print("\n=== Study Assignment ===")
    print("1. Fulfill this order (use MWL Study UID) - DEFAULT")
    print("2. Related imaging (generate new Study UID)")
    return input("Select [1]: ").strip() != '2'