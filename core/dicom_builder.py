"""DICOM dataset construction"""
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import generate_uid, ExplicitVRLittleEndian, ImplicitVRLittleEndian, CTImageStorage, MRImageStorage, \
    DigitalXRayImageStorageForPresentation, ComputedRadiographyImageStorage, XRayRadiofluoroscopicImageStorage, \
    XRayAngiographicImageStorage, DigitalMammographyXRayImageStorageForPresentation, UltrasoundImageStorage, \
    NuclearMedicineImageStorage, PositronEmissionTomographyImageStorage, \
    SecondaryCaptureImageStorage
import numpy as np
from datetime import datetime
from .uid_utils import sanitize_uid

# Modality type to SOP Class UID mapping
MODALITY_SOP_CLASS = {
    'CT': CTImageStorage,
    'MR': MRImageStorage,
    'CR': ComputedRadiographyImageStorage,
    'DX': DigitalXRayImageStorageForPresentation,
    'XA': XRayAngiographicImageStorage,  # Different from DX
    'US': UltrasoundImageStorage,  # Common in many facilities
    'NM': NuclearMedicineImageStorage,  # Nuclear medicine
    'PT': PositronEmissionTomographyImageStorage,  # PET scans
    'MG': DigitalMammographyXRayImageStorageForPresentation,  # Mammography
    'RF': XRayRadiofluoroscopicImageStorage,  # Fluoroscopy
    'SC': SecondaryCaptureImageStorage,  # Fallback
}

TRANSFER_SYNTAX_OPTIONS = {
    'explicit': ExplicitVRLittleEndian,  # Default, most compatible
    'implicit': ImplicitVRLittleEndian,
}

class DicomBuilder:
    """Build DICOM datasets from images and metadata"""
    
    def __init__(self, config):
        self.config = config
    
    def create_dicom_from_image(self, image, mwl_item, fulfill_order):
        """Create DICOM file from image with metadata from MWL item"""
        # Determine SOP Class based on modality
        sps = mwl_item.ScheduledProcedureStepSequence[0] if hasattr(mwl_item, 'ScheduledProcedureStepSequence') else Dataset()
        modality = getattr(sps, 'Modality', self.config.modality_type)
        if modality == '*':
            modality = 'CT'
        
        sop_class = MODALITY_SOP_CLASS.get(modality, CTImageStorage)
        
        file_meta = Dataset()
        file_meta.MediaStorageSOPClassUID = sop_class
        file_meta.MediaStorageSOPInstanceUID = generate_uid()
        file_meta.TransferSyntaxUID = TRANSFER_SYNTAX_OPTIONS(self.config.transfer_syntax or ExplicitVRLittleEndian)
        file_meta.ImplementationClassUID = generate_uid()
        
        ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
        
        # Patient demographics from MWL
        ds.PatientName = getattr(mwl_item, 'PatientName', 'TEST^PATIENT')
        ds.PatientID = getattr(mwl_item, 'PatientID', 'TEST123')
        ds.PatientBirthDate = getattr(mwl_item, 'PatientBirthDate', '')
        ds.PatientSex = getattr(mwl_item, 'PatientSex', 'O')
        
            # Study/Series info from MWL
        sps = mwl_item.ScheduledProcedureStepSequence[0] if hasattr(mwl_item, 'ScheduledProcedureStepSequence') else Dataset()
    
        if fulfill_order:
            # Use MWL-provided Study UID (fulfilling the order)
            ds.StudyInstanceUID = getattr(mwl_item, 'StudyInstanceUID', generate_uid())
            ds.AccessionNumber = getattr(mwl_item, 'AccessionNumber', '')
            # Copy procedure information
            if hasattr(mwl_item, 'RequestedProcedureID'):
                ds.RequestedProcedureID = mwl_item.RequestedProcedureID
            if hasattr(sps, 'ScheduledProcedureStepID'):
                ds.PerformedProcedureStepID = sps.ScheduledProcedureStepID
            if hasattr(mwl_item, 'StudyDescription'):
                ds.StudyDescription = mwl_item.StudyDescription
            print("  → Fulfilling order: Using MWL Study UID")
        else:
            # Generate new Study UID (related study for same patient)
            ds.StudyInstanceUID = generate_uid()
            ds.AccessionNumber = ''  # No accession for ad-hoc study
            ds.StudyDescription = f"Related Study - {modality}"
            print("  → Related study: New Study UID generated")
                
        ds.SeriesInstanceUID = generate_uid()
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        ds.SOPClassUID = sop_class
        ds.Modality = modality
        ds.StationName = self.config.station_name
        
        # Requested procedure info
        if hasattr(mwl_item, 'RequestedProcedureID'):
            ds.RequestedProcedureID = mwl_item.RequestedProcedureID
        if hasattr(sps, 'ScheduledProcedureStepID'):
            ds.PerformedProcedureStepID = sps.ScheduledProcedureStepID
        
        # Study/Series metadata
        now = datetime.now()
        ds.StudyDate = now.strftime('%Y%m%d')
        ds.StudyTime = now.strftime('%H%M%S')
        ds.SeriesDate = ds.StudyDate
        ds.SeriesTime = ds.StudyTime
        ds.ContentDate = ds.StudyDate
        ds.ContentTime = ds.StudyTime
        ds.AcquisitionDate = ds.StudyDate
        ds.AcquisitionTime = ds.StudyTime
        ds.SeriesNumber = 1
        ds.InstanceNumber = 1
        
        # Image data
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.Rows, ds.Columns = image.shape
        ds.BitsAllocated = 16
        ds.BitsStored = 16
        ds.HighBit = 15
        ds.PixelRepresentation = 0
        
        # Convert 8-bit to 16-bit
        img_16 = image.astype(np.uint16) * 256
        ds.PixelData = img_16.tobytes()
        
        return ds
    
    def get_sop_class_for_modality(self, modality):
        """Get SOP Class UID for modality type"""
        return MODALITY_SOP_CLASS.get(modality, CTImageStorage)