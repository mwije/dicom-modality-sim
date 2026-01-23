
from pynetdicom import AE
from datetime import datetime
import os
from pathlib import Path

class StorageService:
    """DICOM Storage (C-STORE) operations"""
    
    def __init__(self, config):
        self.config = config
    
    def send_to_pacs(
        self,
        assoc_factory,
        ds,
        server_host,
        server_port,
        client_ae_title,
        server_ae_title
            ):
        """Send DICOM file to PACS via C-STORE"""

        print("\nSending to PACS...")
        ae = AE(ae_title=self.config.ae_title)
        ae.add_requested_context(ds.SOPClassUID)
        
        result = assoc_factory.create_assoc(
            [ds.SOPClassUID],
            server_host=server_host,
            server_port=server_port,
            client_ae_title=client_ae_title,
            server_ae_title=server_ae_title,
        )

        if not result.ok():
            print(result.explain("C-STORE"))
            return False

        try:
            status = result.assoc.send_c_store(ds)

            if status and status.Status == 0x0000:
                print("✓ Successfully sent to PACS")
                print(f"  SOP Instance UID: {ds.SOPInstanceUID}")
                return True

            print(f"✗ PACS rejected: Status {status.Status:#06x}")
            return False

        except Exception as e:
            print(f"✗ Error sending to PACS: {e}")
            return False

        finally:
            result.assoc.release()
    
    def save_local(self, ds):
        """Save DICOM file locally"""

        if not self.config.save_local:
            return
        
        filename = f"{ds.PatientID}_{ds.Modality}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dcm"
        filepath = os.path.join(self.config.local_dir, filename)
        
        try:
            ds.save_as(filepath, write_like_original=False)
            print(f"✓ Saved locally: {filepath}")
        except Exception as e:
            print(f"✗ Error saving locally: {e}")
