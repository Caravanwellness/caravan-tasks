const fs = require('fs');
const path = require('path');

// Load the American to British spellings dictionary
const spellings = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'american_spellings.json'), 'utf8')
);

// Define paths
const inputDir = path.join(__dirname, 'files', 'English-vtt-files');
const outputDir = path.join(__dirname, 'files', 'British-vtt-files');
const logFile = path.join(__dirname, 'files', 'conversion_log.json');

// Create output directory if it doesn't exist
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

// Initialize the conversion log
const conversionLog = {};

// Function to convert text from American to British spelling
function convertToBritish(text, lineNumber, fileName) {
  let convertedText = text;
  const changes = [];

  // Sort keys by length (longest first) to handle longer phrases before shorter ones
  const sortedKeys = Object.keys(spellings).sort((a, b) => b.length - a.length);

  for (const american of sortedKeys) {
    const british = spellings[american];

    // Create regex with word boundaries to match whole words only
    // Use case-insensitive flag and check for exact case matches
    const regex = new RegExp(`\\b${escapeRegExp(american)}\\b`, 'gi');

    const matches = [...convertedText.matchAll(regex)];

    for (const match of matches) {
      const originalWord = match[0];
      let replacement;

      // Preserve the original case pattern
      if (originalWord === american) {
        // Exact match (lowercase)
        replacement = british;
      } else if (originalWord === american.toUpperCase()) {
        // ALL CAPS
        replacement = british.toUpperCase();
      } else if (originalWord[0] === originalWord[0].toUpperCase()) {
        // Title Case
        replacement = british.charAt(0).toUpperCase() + british.slice(1);
      } else {
        replacement = british;
      }

      // Only replace if it actually changes something
      if (originalWord !== replacement) {
        convertedText = convertedText.replace(originalWord, replacement);

        changes.push({
          line: lineNumber,
          original: originalWord,
          changed: replacement
        });
      }
    }
  }

  return { convertedText, changes };
}

// Helper function to escape special regex characters
function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Process all VTT files in the input directory
const files = fs.readdirSync(inputDir).filter(file => file.endsWith('_en.vtt'));

console.log(`Found ${files.length} files to process...`);

files.forEach((fileName, index) => {
  console.log(`Processing ${index + 1}/${files.length}: ${fileName}`);

  const inputPath = path.join(inputDir, fileName);
  const outputFileName = fileName.replace('_en.vtt', '_uk.vtt');
  const outputPath = path.join(outputDir, outputFileName);

  // Read the file content
  const content = fs.readFileSync(inputPath, 'utf8');
  const lines = content.split('\n');

  // Initialize log for this file
  conversionLog[fileName] = {
    outputFile: outputFileName,
    changes: []
  };

  // Process each line
  const convertedLines = lines.map((line, lineIndex) => {
    const lineNumber = lineIndex + 1;

    // Skip timestamp lines and empty lines for conversion
    if (line.trim() === '' || /^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}$/.test(line.trim()) || line.trim() === 'WEBVTT') {
      return line;
    }

    const { convertedText, changes } = convertToBritish(line, lineNumber, fileName);

    // Add changes to log
    if (changes.length > 0) {
      conversionLog[fileName].changes.push(...changes);
    }

    return convertedText;
  });

  // Write the converted content to the output file
  fs.writeFileSync(outputPath, convertedLines.join('\n'), 'utf8');
});

// Write the conversion log
fs.writeFileSync(logFile, JSON.stringify(conversionLog, null, 2), 'utf8');

console.log('\nConversion complete!');
console.log(`- Processed ${files.length} files`);
console.log(`- Output directory: ${outputDir}`);
console.log(`- Conversion log: ${logFile}`);

// Print summary statistics
let totalChanges = 0;
Object.values(conversionLog).forEach(fileLog => {
  totalChanges += fileLog.changes.length;
});
console.log(`- Total spelling changes made: ${totalChanges}`);
