// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;

contract CertificateStore {

    // A single, unified struct to hold data for ALL certificate types
    struct Certificate {
        string studentName;
        string studentEmail;
        string institutionName;
        string courseName;
        string certificateId; // CID
        string certType;      // 'degree' or 'additional'
        uint256 timestamp;    // Timestamp of when it was stored

        // --- Degree Certificate Fields ---
        string studentId;     // Register Number
        string stream;
        string batch;
        string department;
        string cgpa;
        string issueDate;

        // --- Additional Certificate Fields ---
        string issuingBody;   // For external certs like Coursera
        string startDate;
        string endDate;
    }

    // Mapping from the certificate hash (bytes32) to the Certificate struct
    mapping(bytes32 => Certificate) public certificates;

    // An array to keep track of every hash stored
    bytes32[] public allCertificateHashes;

    event CertificateStored(bytes32 indexed certificateHash, string studentEmail);

    /**
     * @dev Stores the comprehensive details of any certificate on the blockchain.
     * Unused fields for a specific cert type should be passed as empty strings.
     */
    function storeCertificate(
        bytes32 _hash,
        string memory _studentName,
        string memory _studentEmail,
        string memory _institutionName,
        string memory _courseName,
        string memory _certificateId,
        string memory _certType,
        // Degree fields
        string memory _studentId,
        string memory _stream,
        string memory _batch,
        string memory _department,
        string memory _cgpa,
        string memory _issueDate,
        // Additional fields
        string memory _issuingBody,
        string memory _startDate,
        string memory _endDate
    ) public {
        // Ensure the certificate doesn't already exist
        require(bytes(certificates[_hash].studentEmail).length == 0, "Certificate hash already exists.");

        // Add the new hash to our array for tracking
        allCertificateHashes.push(_hash);

        // Create and store the new certificate struct in the mapping
        certificates[_hash] = Certificate({
            studentName: _studentName,
            studentEmail: _studentEmail,
            institutionName: _institutionName,
            courseName: _courseName,
            certificateId: _certificateId,
            certType: _certType,
            timestamp: block.timestamp,
            studentId: _studentId,
            stream: _stream,
            batch: _batch,
            department: _department,
            cgpa: _cgpa,
            issueDate: _issueDate,
            issuingBody: _issuingBody,
            startDate: _startDate,
            endDate: _endDate
        });

        emit CertificateStored(_hash, _studentEmail);
    }

    /**
     * @dev Retrieves all details for a given certificate hash.
     */
    function getCertificateDetails(bytes32 _hash) public view returns (Certificate memory) {
        return certificates[_hash];
    }

    /**
     * @dev Returns the array of all certificate hashes stored in the contract.
     */
    function getAllCertificateHashes() public view returns (bytes32[] memory) {
        return allCertificateHashes;
    }
}