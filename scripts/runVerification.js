// --- REQUIRED LIBRARIES ---
const { Web3 } = require('web3');
const { initializeApp, cert } = require('firebase-admin/app');
const { getFirestore } = require('firebase-admin/firestore');
const nodemailer = require('nodemailer');

// --- CONFIGURATION ---
// IMPORTANT: Make sure these paths are correct relative to where you run the script from.
const contractABI = require('../contract_abi.json');
const contractABI = require('../build/contracts/CertificateStore.json').abi;

// --- ⬇️ ACTION REQUIRED ⬇️ ---
// PASTE YOUR NEW DEPLOYED CONTRACT ADDRESS HERE
const contractAddress = '0x0Bb5DB41ff71D4F931f9702b9972572dF796C256';

// --- INITIALIZATION ---
try {
    initializeApp({
      credential: cert(serviceAccount)
    });
} catch (error) {
    if (!/already exists/u.test(error.message)) {
      console.error('Firebase admin initialization error', error.stack);
    }
}

const db = getFirestore();
const web3 = new Web3(process.env.ALCHEMY_RPC_URL || 'https://eth-sepolia.g.alchemy.com/v2/alch_V8PE21KInArfXDrG-Sg6A');
const contract = new web3.eth.Contract(contractABI, contractAddress);
console.log('Connections to Firebase and Web3 have been configured.');

// --- MAIN VERIFICATION FUNCTION ---
async function runCrossVerification() {
  console.log('Starting comprehensive cross-verification process...');
  
  try {
    // 1. Get all hashes from the blockchain (returns bytes32[])
    const allHashes = await contract.methods.getAllCertificateHashes().call();
    console.log(`Found ${allHashes.length} certificates on the blockchain to verify.`);

    let discrepanciesFound = 0;

    for (const hash of allHashes) {
      console.log(`Verifying certificate hash: ${hash}`);

      // 2. Get the full certificate data struct from the blockchain
      const blockchainData = await contract.methods.getCertificateDetails(hash).call();
      
      // 3. Get corresponding data from Firebase
      const firebaseHash = hash.startsWith('0x') ? hash.substring(2) : hash;
      const firebaseData = await findCertificateInFirebase(firebaseHash);

      if (!firebaseData) {
        console.warn(`DISCREPANCY: Hash ${hash} exists on blockchain but is MISSING from Firebase.`);
        await logDiscrepancyToDashboard(hash, 'Missing from Firebase', { 
            error: 'Record found on-chain but not in the database.',
            blockchainData 
        });
        discrepanciesFound++;
        continue; // Move to the next hash
      }
      
      // 4. Perform a detailed comparison and log if issues are found
      const issues = compareData(firebaseData, blockchainData);
      if (issues.length > 0) {
          console.error(`DISCREPANCY: Mismatch found for hash: ${hash}`);
          await logDiscrepancyToDashboard(hash, 'Data Mismatch', {
              error: 'One or more fields do not match between Firebase and Blockchain.',
              mismatches: issues
          });
          discrepanciesFound++;
      } else {
        console.log(`✅ Certificate ${hash} is consistent.`);
      }
    }

    console.log(`\nVerification complete. Found ${discrepanciesFound} total discrepancies.`);
    if (discrepanciesFound > 0) {
        // Send one summary email at the end if any issues were found
        await sendWarningEmail(discrepanciesFound);
    }

  } catch (error) {
    console.error('🛑 An error occurred during the verification process:', error);
  }
}

// --- HELPER FUNCTIONS ---

/**
 * Finds a certificate in either of the Firebase collections.
 * @param {string} hash - The certificate hash (without '0x').
 * @returns {object|null} The document data or null if not found.
 */
async function findCertificateInFirebase(hash) {
    const degreeRef = db.collection('degree_certificates').doc(hash);
    const degreeDoc = await degreeRef.get();
    if (degreeDoc.exists) return degreeDoc.data();

    const additionalRef = db.collection('additional_certificates').doc(hash);
    const additionalDoc = await additionalRef.get();
    if (additionalDoc.exists) return additionalDoc.data();
    
    return null;
}

/**
 * A helper function to standardize various date formats to 'YYYY-MM-DD'.
 * @param {*} dateInput - Can be a Firestore Timestamp, a string, or other types.
 * @returns {string} The date formatted as 'YYYY-MM-DD' or an empty string.
 */
function formatDate(dateInput) {
    if (!dateInput) return '';
    
    // Handles Firestore Timestamp objects, which have a toDate() method
    if (typeof dateInput.toDate === 'function') {
        // Converts to a JavaScript Date, then to an ISO string (e.g., '2025-08-29T...'), and takes the date part.
        return dateInput.toDate().toISOString().substring(0, 10);
    }
    
    // Handles string dates (like '2025-08-29 00:00:00' from the blockchain)
    if (typeof dateInput === 'string') {
        return dateInput.substring(0, 10);
    }
    
    // Fallback for any other types
    return String(dateInput).substring(0, 10);
}

/**
 * Compares data from Firebase and the blockchain field by field,
 * with special handling for date formats.
 * @param {object} firebaseData - Data from Firestore.
 * @param {object} blockchainData - Data from the smart contract struct.
 * @returns {array} An array of discrepancy objects if any are found.
 */
function compareData(firebaseData, blockchainData) {
    const issues = [];
    const dateFields = ['issue_date', 'start', 'end']; // List of date fields to format

    const check = (fbKey, bcKey, fieldName) => {
        const originalFbValue = firebaseData[fbKey] || '';
        const originalBcValue = blockchainData[bcKey] || '';

        let formattedFbValue = originalFbValue;
        let formattedBcValue = originalBcValue;

        // If the field is a date, standardize its format before comparing
        if (dateFields.includes(fbKey)) {
            formattedFbValue = formatDate(originalFbValue);
            formattedBcValue = formatDate(originalBcValue);
        }

        // Compare the standardized (or original) values
        if (String(formattedFbValue).trim() !== String(formattedBcValue).trim()) {
            issues.push({
                field: fieldName,
                firebase: String(originalFbValue), // Log the original value for clarity
                blockchain: String(originalBcValue)
            });
        }
    };

    // Common fields
    check('name', 'studentName', 'Student Name');
    check('email', 'studentEmail', 'Student Email');
    check('course', 'courseName', 'Course Name');
    check('cid', 'certificateId', 'Certificate ID');
    check('institution_name', 'institutionName', 'Institution Name');
    
    // Type-specific fields
    if (blockchainData.certType === 'degree') {
        check('student_id', 'studentId', 'Student ID');
        check('stream', 'stream', 'Stream');
        check('batch', 'batch', 'Batch');
        check('department', 'department', 'Department');
        check('cgpa', 'cgpa', 'CGPA');
        check('issue_date', 'issueDate', 'Issue Date');
    } else if (blockchainData.certType === 'additional') {
        check('start', 'startDate', 'Start Date');
        check('end', 'endDate', 'End Date');
    }
    
    return issues;
}


/**
 * Logs a discrepancy to the 'discrepancies' collection in Firestore.
 * @param {string} hash - The certificate hash (with '0x').
 * @param {string} issue - A summary of the issue.
 * @param {object} details - An object with detailed information about the discrepancy.
 */
async function logDiscrepancyToDashboard(hash, issue, details) {
  const discrepancyRef = db.collection('discrepancies').doc(); // Auto-generate ID
  await discrepancyRef.set({
    certificateHash: hash,
    issue: issue,
    details: details,
    timestamp: new Date(),
    status: 'unresolved',
  });
  console.log(`Logged discrepancy for ${hash} to the dashboard.`);
}

/**
 * Sends a summary warning email to the admin.
 * @param {number} discrepancyCount - The total number of discrepancies found.
 */
async function sendWarningEmail(discrepancyCount) {
  if (!process.env.EMAIL_USER || !process.env.EMAIL_PASS) {
      console.error("Email credentials (EMAIL_USER, EMAIL_PASS) not set in environment variables. Skipping email.");
      return;
  }
  
  let transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
      user: process.env.EMAIL_USER,
      pass: process.env.EMAIL_PASS,
    },
  });

  let mailOptions = {
    from: `"CertChain Platform" <${process.env.EMAIL_USER}>`,
    to: 'admin_email@example.com', // The admin's email
    subject: `🚨 SECURITY ALERT: ${discrepancyCount} Data Discrepancies Detected!`,
    html: `
      <h2>The nightly cross-verification check has detected ${discrepancyCount} data inconsistencies on the platform.</h2>
      <p>Please log in to the <strong>admin dashboard</strong> immediately to investigate the 'Discrepancies' section.</p>
      <p>This automated check ensures the integrity of the data between the central database and the immutable blockchain.</p>
      <p>Timestamp: ${new Date().toISOString()}</p>
    `,
  };

  try {
    await transporter.sendMail(mailOptions);
    console.log(`Summary warning email sent to the admin.`);
  } catch (error) {
    console.error(`Failed to send summary email:`, error);
  }
}

(async () => {
  await runCrossVerification();
})();