# Copyright (c) 2026 Malinda Wijeratne
# SPDX-License-Identifier: MIT

from pydicom.dataset import Dataset
from pynetdicom import AE
from pynetdicom.sop_class import ModalityPerformedProcedureStep, SecondaryCaptureImageStorage
from datetime import datetime
from collections import defaultdict
from pydicom.uid import generate_uid

class MPPSService:
    """DICOM MPPS (Modality Performed Procedure Step) operations"""
    """Handle MPPS N-CREATE and N-SET operations"""
    
    def __init__(self, config):
        self.config = config
    
    def send_in_progress(
        self,
        assoc_factory,
        mwl_item,
        server_host,
        server_port,
        client_ae_title,
        server_ae_title
        ):
        """Send MPPS N-CREATE (IN PROGRESS)"""

        ds = Dataset()
        ds.SOPClassUID = ModalityPerformedProcedureStep
        ds.SOPInstanceUID = generate_uid()
        
        # Scheduled Step Attributes Sequence (from MWL)
        ds.ScheduledStepAttributesSequence = [Dataset()]
        sched = ds.ScheduledStepAttributesSequence[0]
        sched.StudyInstanceUID = getattr(mwl_item, 'StudyInstanceUID', generate_uid())
        sched.AccessionNumber = getattr(mwl_item, 'AccessionNumber', '')
        sched.RequestedProcedureID = getattr(mwl_item, 'RequestedProcedureID', '1')
        sps = mwl_item.ScheduledProcedureStepSequence[0] if hasattr(mwl_item, 'ScheduledProcedureStepSequence') else Dataset()
        sched.ScheduledProcedureStepID = getattr(sps, 'ScheduledProcedureStepID', '1')
        sched.ReferencedStudySequence = []
        sched.ScheduledProcedureProtocolCodeSequence = []
        
        # Patient Demographics
        ds.PatientName = getattr(mwl_item, 'PatientName', 'TEST^PATIENT')
        ds.PatientID = getattr(mwl_item, 'PatientID', 'TEST123')
        ds.PatientBirthDate = getattr(mwl_item, 'PatientBirthDate', '')
        ds.PatientSex = getattr(mwl_item, 'PatientSex', 'O')
        ds.ReferencedPatientSequence = []
        
        # Performed Procedure Step Information
        ds.PerformedProcedureStepID = sched.ScheduledProcedureStepID
        ds.PerformedStationAETitle = self.config.ae_title
        ds.PerformedStationName = self.config.station_name
        ds.PerformedProcedureStepStartDate = datetime.now().strftime('%Y%m%d')
        ds.PerformedProcedureStepStartTime = datetime.now().strftime('%H%M%S')
        ds.PerformedProcedureStepStatus = 'IN PROGRESS'
        ds.PerformedProcedureStepEndDate = None
        ds.PerformedProcedureStepEndTime = None
        ds.PerformedProcedureCodeSequence = []
        
        # Modality
        ds.Modality = getattr(sps, 'Modality', self.config.modality_type)
        ds.StudyID = getattr(mwl_item, 'StudyID', '1')
        ds.PerformedProtocolCodeSequence = []
        ds.PerformedSeriesSequence = []
        
        # Send N-CREATE
        return self._send_n_create(
            ds,
            assoc_factory,
            server_host,
            server_port,
            client_ae_title,
            server_ae_title
            )
        
    def mpps_ds(self, mpps_uid, status):
        if not mpps_uid:
            print("✗ MPPS UID required for N-SET")
            return False
        
        ds = Dataset()
        ds.PerformedProcedureStepEndDate = datetime.now().strftime('%Y%m%d')
        ds.PerformedProcedureStepEndTime = datetime.now().strftime('%H%M%S')
        ds.PerformedProcedureStepStatus = status
        ds.SOPClassUID = ModalityPerformedProcedureStep
        ds.SOPInstanceUID = mpps_uid

        return ds
    
    def send_completed(self,
        assoc_factory,
        mpps_uid,
        dicom_instance,
        server_host,
        server_port,
        client_ae_title,
        server_ae_title
        ):
        """Send MPPS N-SET (COMPLETED)"""

        ds = self.mpps_ds(mpps_uid, "COMPLETED")
        
        if dicom_instance:
            series_map = defaultdict(list)
            for inst in dicom_instance:
                series_map[inst.SeriesInstanceUID].append(inst)

            ds.PerformedSeriesSequence = []

            for series_uid, series_instances in series_map.items():
                series = Dataset()
                series.SeriesInstanceUID = series_uid
                series.SeriesDescription = getattr(series_instances[0], 'SeriesDescription', '')
                series.RetrieveAETitle = client_ae_title
                series.ReferencedImageSequence = []

                for inst in series_instances:
                    ref = Dataset()
                    ref.ReferencedSOPClassUID = inst.SOPClassUID
                    ref.ReferencedSOPInstanceUID = inst.SOPInstanceUID
                    series.ReferencedImageSequence.append(ref)

                ds.PerformedSeriesSequence.append(series)
        else:
            series = Dataset()
            series.SeriesInstanceUID = generate_uid()
            series.SeriesDescription = 'TEST Images'

            ref = Dataset()
            ref.ReferencedSOPClassUID = SecondaryCaptureImageStorage
            ref.ReferencedSOPInstanceUID = generate_uid()

            series.ReferencedImageSequence = [ref]
            ds.PerformedSeriesSequence = [series]

        return self._send_n_set(
            ds,
            mpps_uid,
            assoc_factory,
            server_host,
            server_port,
            client_ae_title,
            server_ae_title
            )
    
    def send_discontinued(
        self,
        assoc_factory,
        mpps_uid,
        dicom_instance,
        server_host,
        server_port,
        client_ae_title,
        server_ae_title,
        reason=None):
        """Send MPPS N-SET (DISCONTINUED)"""

        ds = self.mpps_ds(mpps_uid, "DISCONTINUED")

        reason_code = Dataset()
        reason_code.CodeValue = '110514'
        reason_code.CodingSchemeDesignator = 'DCM'
        reason_code.CodeMeaning = reason or 'User cancelled'
        ds.PerformedProcedureStepDiscontinuationReasonCodeSequence = [reason_code]

        return self._send_n_set(
            ds,
            mpps_uid,
            assoc_factory,
            server_host,
            server_port,
            client_ae_title,
            server_ae_title
        )

    def _send_n_create(
        self,
        ds,
        assoc_factory,
        server_host,
        server_port,
        client_ae_title,
        server_ae_title
        ):
        """Internal: Send N-CREATE request"""

        assoc = assoc_factory.create_assoc(
            [ds.SOPClassUID],
            server_host=server_host,
            server_port=server_port,
            client_ae_title=client_ae_title,
            server_ae_title=server_ae_title,
        )

        if assoc.ok() is not True:
            print(assoc.explain("MPPS"))
            return False

        status_rsp, attr_list = assoc.assoc.send_n_create(
                ds,
                ModalityPerformedProcedureStep,
                ds.SOPInstanceUID
            )

        assoc.assoc.release()

        self.show_mpps_result(status_rsp, attr_list, ds.SOPInstanceUID)
        return ds.SOPInstanceUID
        
    def _send_n_set(
        self,
        ds,
        mpps_uid,
        assoc_factory,
        server_host,
        server_port,
        client_ae_title,
        server_ae_title
        ):
        """Internal: Send N-SET request"""

        assoc = assoc_factory.create_assoc(
            [ds.SOPClassUID],
            server_host=server_host,
            server_port=server_port,
            client_ae_title=client_ae_title,
            server_ae_title=server_ae_title,
        )

        if assoc.ok() is not True:
            print(assoc.explain("MPPS"))
            return False

        status_rsp, attr_list = assoc.assoc.send_n_set(
                ds,
                ModalityPerformedProcedureStep,
                mpps_uid
            )

        assoc.assoc.release()
        self.show_mpps_result(status_rsp, attr_list, mpps_uid)
        return mpps_uid
        
        
    def show_mpps_result(self, status_rsp, attr_list, mpps_uid):
        if status_rsp and status_rsp.Status == 0x0000:
            print(f"✓ MPPS {mpps_uid} sent")
            return True
        else:
            if status_rsp:
                status_str = f"{status_rsp.Status:#06x}"
            else:
                status_str = "timeout"

            print(f"✗ MPPS rejected: {status_str}")

            if status_rsp and hasattr(status_rsp, "ErrorComment"):
                print(f"PACS says: {status_rsp.ErrorComment}")

            return False
