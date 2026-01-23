"""DICOM UID utilities and sanitization"""
from pydicom.uid import generate_uid

def sanitize_uid(uid_value):
    """Sanitize DICOM UID by removing whitespace"""
    if not uid_value:
        return uid_value
    uid_clean = str(uid_value).strip()
    uid_clean = ''.join(c for c in uid_clean if c.isprintable())
    uid_clean = uid_clean.rstrip('.')
    return uid_clean

def generate_safe_uid():
    """Generate a new DICOM UID"""
    return generate_uid()