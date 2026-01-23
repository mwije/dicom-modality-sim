# DICOM Modality Simulator

**Testing PACS integrations without physical imaging equipment.**

A Python-based DICOM modality simulator for developing and validating radiology workflows. Enables pre-production testing in isolated environments and reducing integration risks without equipment dependencies.

Built from experience with PACS deployments where validating RIS/PACS/modality workflows, without disrupting clinical operations or coordinating limited equipment access.

Simulates the complete DICOM communication pattern of imaging modalities—enabling comprehensive pre-production testing in isolated environments.

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

🟢 Actively maintained
🧪 Used in real-world PACS integration testing  
📦 Stable for non-production use

---

## Why This Exists

Testing PACS integrations requires either disrupting live clinical systems or coordinating limited access to expensive imaging equipment. This creates bottlenecks during:
- PACS upgrades and migrations
- New modality integrations
- RIS/PACS workflow development
- Vendor interoperability validation

This tool simulates the DICOM communication patterns of imaging modalities, enabling integration testing in controlled test environments without equipment access.

---

## What It Does

Emulates the complete acquisition-to-storage workflow that modalities perform:

```
Query Worklist → Select Patient → Acquire Image → Send to PACS → Report Procedure Status
```

### DICOM Services (as SCU)

| Service | Purpose | Status |
|---------|---------|--------|
| **C-ECHO** | Verify PACS connectivity | ✅ Implemented |
| **C-FIND** | Query Modality Worklist (MWL) | ✅ Implemented |
| **C-STORE** | Send images to PACS | ✅ Implemented |
| **MPPS** | Report procedure status (N-CREATE, N-SET) | ✅ Implemented |

### Key Features

- **Profile Management** - Save/load configurations for different modality types (CT, MR, CR, etc.)
- **MPPS Workflow** - Complete procedure status reporting (IN PROGRESS, COMPLETED, DISCONTINUED)
- **Multiple Image Sources** - Test patterns (recommended), file import, or webcam capture
- **Worklist Filtering** - Unfiltered or filter by AE Title and modality type
- **Local Storage** - Optional DICOM file retention for inspection

---

## Quick Start

```bash
: Clone and setup
git clone https://github.com/mwije/dicom-modality-sim.git
cd dicom-modality-sim
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

: Run
python main.py
```
```bash
# First-time configuration
C → Configure PACS endpoints (host, port, AE titles)
E → Verify connectivity (C-ECHO)
1 → Query worklist (C-FIND)
4 → Acquire and send test image (C-STORE)
```

### Essential Configuration

```ini
# Storage SCP (where images go)
PACS_STORE_HOST=127.0.0.1
PACS_STORE_PORT=11112
STORE_AE_TITLE=PACS_STORE

# MWL SCP (where worklist comes from)
PACS_MWL_HOST=127.0.0.1
PACS_MWL_PORT=11112
MWL_AE_TITLE=WORKLIST

# This modality's identity
AE_TITLE=SIM_MODALITY1
STATION_NAME=DEMO_SIMULATOR
MODALITY_TYPE=CT
```

---

## Use Cases

### Radiology Workflow Testing
Validate that your PACS correctly handles:
- Worklist queries with various filter criteria
- Image storage from different modality types
- MPPS status updates for procedure tracking
- Testing DICOM conformance patterns

### Troubleshooting & QA
Reproduce and isolate integration issues:
- Network connectivity problems (C-ECHO validation)
- Worklist query failures (attribute mismatches)
- Storage failures (transfer syntax negotiation)
- MPPS workflow issues

### Vendor Evaluation
During PACS procurement, validate:
- Vendor DICOM conformance claims
- Support for your specific modality fleet

---

## Menu Reference

### Main Menu
```
E - DICOM C-ECHO (Verify PACS)
1 - Query Worklist
2 - View Worklist (cached results)
3 - Select Patient
4 - Perform Acquisition
5 - Perform MPPS
6 - Show Configuration
C - Configure Settings
P - Profile Management
Q - Exit
```

### MPPS Workflow
```
1. Send IN PROGRESS (N-CREATE)   - Start procedure
2. Send COMPLETED (N-SET)         - Finish successfully
3. Send DISCONTINUED (N-SET)      - Cancel procedure
4. Clear MPPS UID                 - Reset for new procedure
```

### Profile Management
```
1. List Profiles          - View saved configurations
2. Save Current as Profile - Store current settings
3. Load Profile           - Switch to saved configuration
4. Delete Profile         - Remove configuration
```

---

## Technical Details

### DICOM Conformance
- **Transfer Syntaxes:** Implicit VR Little Endian, Explicit VR Little Endian
- **Implementation Class UID:** Auto-generated per instance
- **MPPS Specification:** DICOM PS3.4 Section F
- **Supported Modalities:** CT, MR, CR, DX, US, NM, PT, etc (configurable)

### Architecture Notes
**Separate MWL/Storage Hosts:** Many healthcare environments serve MWL from RIS and Storage from PACS. This tool supports both unified and split architectures.

**Profile System:** Profile-based configuration enables rapid switching between test scenarios, reflecting real-world integration testing needs during PACS deployments.

**Image Generation:** Creates valid DICOM instances with proper metadata structure. Test patterns are synthetic and suitable for non-clinical testing only.

### Dependencies
- **pynetdicom** - DICOM network protocol implementation
- **pydicom** - DICOM file format handling
- **opencv-python** - Image capture (optional for webcam)

---

## Appropriate Use

**Designed for:**
- ✅ Isolated test PACS instances
- ✅ Development environments with synthetic data
- ✅ Training and educational settings
- ✅ Pre-production validation
- ✅ Vendor demonstration and evaluation

**Not suitable for:**
- ❌ Production clinical networks
- ❌ Systems with real patient data (PHI)
- ❌ Clinical decision-making
- ❌ Regulatory compliance validation without additional controls

**Data Safety:** Tool generates only synthetic test data. Always use fabricated demographics in test environments.

---

## Roadmap

**Near-term:**
- [ ] REST API for automated testing and CI/CD integration
- [ ] Web-based interface for non-CLI users
- [ ] Docker containerization for portable deployment

**Future considerations:**
- [ ] Storage Commitment (N-ACTION/N-EVENT-REPORT)
- [ ] Advanced SPS filtering (time ranges, specific procedure codes)
- [ ] Compressed transfer syntax support (JPEG, JPEG2000)
- [ ] Multi-study/multi-series simulation

---

## Contributing

Contributions welcome! This project benefits from real-world PACS integration experience.

**Particularly valuable:**
- Modality behavior patterns from actual vendor implementations
- Edge case scenarios encountered during deployments
- DICOM attribute variations across different PACS systems
- Documentation improvements based on your testing workflows
- Bug reports with DICOM network captures (kindly anonymize)

Please open an issue before significant changes to discuss approach.

---

## Resources

**DICOM & Healthcare IT:**
- [DICOM Standard](https://www.dicomstandard.org/) - Official protocol specifications
- [IHE Radiology Technical Framework](https://www.ihe.net/resources/technical_frameworks/#radiology) - Integration profiles
- [pynetdicom Documentation](https://pydicom.github.io/pynetdicom/) - Python implementation

**Related Projects:**
- [DCM4CHEE](https://www.dcm4che.org/) - Clinical image archive
- [Orthanc](https://www.orthanc-server.com/) - Lightweight DICOM server
- [OHIF Viewer](https://ohif.org/) - Web-based DICOM viewer

---

## License

MIT License - See [LICENSE](LICENSE)

This project is open source to benefit the healthcare IT community. Commercial use permitted under MIT terms.

---

## Contact & Support

**Issues & Questions:** Please use [GitHub Issues](https://github.com/mwije/dicom-modality-sim/issues)

**Collaboration:** Open to collaboration on healthcare informatics projects. Contact via GitHub.

---

**Disclaimer:** This is a development and testing tool for healthcare IT professionals. It is not a medical device, not FDA cleared, and not intended for clinical use or with real patient data.