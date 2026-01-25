# Copyright (c) 2026 Malinda Wijeratne
# SPDX-License-Identifier: MIT

from pydicom.dataset import Dataset
from pynetdicom import AE
from pynetdicom.sop_class import ModalityWorklistInformationFind

class WorklistService:
    """DICOM Worklist (MWL) operations"""
    
    def __init__(self, config):
        self.config = config
    
    def apply_display_filter(self):
        """Apply display-level filtering to worklist"""

        if self.config.filter_level != 'display':
            self.filtered_worklist = self.current_worklist
            return
        
        filtered = []
        for item in self.current_worklist:
            # Filter by modality
            if self.config.modality_type != '*':
                sps = item.ScheduledProcedureStepSequence[0] if hasattr(item, 'ScheduledProcedureStepSequence') else None
                modality = getattr(sps, 'Modality', '') if sps else ''
                if modality != self.config.modality_type:
                    continue
            
            # Filter by AE title
            if self.config.filter_by_ae:
                sps = item.ScheduledProcedureStepSequence[0] if hasattr(item, 'ScheduledProcedureStepSequence') else None
                ae_title = getattr(sps, 'ScheduledStationAETitle', '') if sps else ''
                if ae_title != self.config.ae_title:
                    continue
            
            filtered.append(item)
        
        self.filtered_worklist = filtered
        if len(filtered) < len(self.current_worklist):
            print(f"  Display filter: {len(filtered)}/{len(self.current_worklist)} items shown")

    def query(
        self,
        assoc_factory,
        server_host,
        server_port,
        client_ae_title,
        server_ae_title,
        modality_filter=None,
        ae_filter=None,
        ):
        """Query MWL from PACS with optional filtering"""
        
        print("\nQuerying worklist from PACS...")
        ae = AE(ae_title=self.config.ae_title)
        ae.add_requested_context(ModalityWorklistInformationFind)
        
        ds = Dataset()
        ds.PatientName = ""
        ds.PatientID = ""
        ds.PatientBirthDate = ""
        ds.PatientSex = ""

        # Order / Requested Procedure
        ds.AccessionNumber = ""
        ds.RequestedProcedureID = ""
        ds.RequestedProcedureDescription = ""
        ds.StudyInstanceUID = ""
        ds.Modality = ""

        # Scheduled Procedure Step
        sps = Dataset()
        sps.ScheduledProcedureStepID = ""
        sps.ScheduledProcedureStepStartDate = ""
        sps.ScheduledProcedureStepStartTime = ""
        sps.Modality = ""
        sps.ScheduledStationAETitle = ""
        sps.ScheduledProcedureStepDescription = ""
        sps.ScheduledPerformingPhysicianName = ""
        sps.StudyInstanceUID = ""  # PACS may provide
        ds.ScheduledProcedureStepSequence = [sps]
        
        # Apply query-level filtering
        if self.config.filter_level == 'query':
            if self.config.modality_type != '*':
                ds.ScheduledProcedureStepSequence[0].Modality = self.config.modality_type
                print(f"  Filtering by modality: {self.config.modality_type}")
            else:
                ds.ScheduledProcedureStepSequence[0].Modality = ""
            
            if self.config.filter_by_ae:
                ds.ScheduledProcedureStepSequence[0].ScheduledStationAETitle = self.config.ae_title
                print(f"  Filtering by AE Title: {self.config.ae_title}")
            else:
                ds.ScheduledProcedureStepSequence[0].ScheduledStationAETitle = ""
        else:
            ds.ScheduledProcedureStepSequence[0].Modality = ""
            ds.ScheduledProcedureStepSequence[0].ScheduledStationAETitle = ""
        
        worklist = []

        result = assoc_factory.create_assoc(
            [ModalityWorklistInformationFind],
            server_host=server_host,
            server_port=server_port,
            client_ae_title=client_ae_title,
            server_ae_title=server_ae_title
        )

        if result.ok() is not True:
            print(result.explain("MWL query"))
            return []

        try:
            responses = result.assoc.send_c_find(
                ds, ModalityWorklistInformationFind
            )

            for status, identifier in responses:
                if status and identifier:
                    worklist.append(identifier)

            print(f"✓ Retrieved {len(worklist)} worklist items")

        except Exception as e:
            print(f"✗ Error querying worklist: {e}")

        finally:
            result.assoc.release()

        self.current_worklist = worklist
        self.apply_display_filter()

        return self.filtered_worklist
