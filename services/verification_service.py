
from pynetdicom.sop_class import Verification

class VerificationService:
    def __init__(self, assoc_factory):
        self.assoc_factory = assoc_factory

    def verify_connection(
        self,
        server_host,
        server_port,
        client_ae_title,
        server_ae_title
        ):

        result = self.assoc_factory.create_assoc(
            [Verification],
            server_host=server_host,
            server_port=server_port,
            client_ae_title=client_ae_title,
            server_ae_title=server_ae_title,
            )

        if result.ok is not True:
            print(f"✗ TCP unreachable {server_host}:{server_port}")

            return False
        
        status = result.assoc.send_c_echo()
        result.assoc.release()

        if status and status.Status == 0x0000:
            print(f"✓ C-ECHO successful {server_ae_title} @ {server_host}:{server_port}")
            return True

        print(f"✗ C-ECHO failed: {server_ae_title} @ {server_host}:{server_port}\n{status.Status:#06x}")
        return False
