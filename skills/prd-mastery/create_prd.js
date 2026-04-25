#!/usr/bin/env node

/**
 * Helper script to create a new PRD
 * 
 * Usage: node create_prd.js "Feature Name"
 * 
 * This script:
 * 1. Determines the next PRD number
 * 2. Creates the PRD folder structure
 * 3. Copies the template
 * 4. Updates the PRD with basic info
 * 5. Outputs next steps
 */

const fs = require('fs');
const path = require('path');

// Configuration
const PRDS_DIR = path.join(process.cwd(), 'prds');
const TEMPLATE_PATH = path.join(PRDS_DIR, 'templates', 'prd-template.md');

function toKebabCase(str) {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function getNextPrdNumber() {
  if (!fs.existsSync(PRDS_DIR)) {
    return 1;
  }

  const entries = fs.readdirSync(PRDS_DIR);
  const prdFolders = entries.filter(entry => {
    const match = entry.match(/^prd-(\d+)/);
    return match && fs.statSync(path.join(PRDS_DIR, entry)).isDirectory();
  });

  if (prdFolders.length === 0) {
    return 1;
  }

  const numbers = prdFolders.map(folder => {
    const match = folder.match(/^prd-(\d+)/);
    return parseInt(match[1], 10);
  });

  return Math.max(...numbers) + 1;
}

function createPrdFolder(featureName) {
  const prdNumber = getNextPrdNumber();
  const prdId = String(prdNumber).padStart(3, '0');
  const kebabName = toKebabCase(featureName);
  const folderName = `prd-${prdId}-${kebabName}`;
  const folderPath = path.join(PRDS_DIR, folderName);

  // Create prds directory if it doesn't exist
  if (!fs.existsSync(PRDS_DIR)) {
    fs.mkdirSync(PRDS_DIR, { recursive: true });
    console.log(`✅ Created prds/ directory`);
  }

  // Create PRD folder
  if (fs.existsSync(folderPath)) {
    console.error(`❌ Error: Folder ${folderName} already exists`);
    process.exit(1);
  }

  fs.mkdirSync(folderPath);
  console.log(`✅ Created folder: ${folderName}/`);

  // Copy template
  if (fs.existsSync(TEMPLATE_PATH)) {
    let template = fs.readFileSync(TEMPLATE_PATH, 'utf-8');
    
    // Replace placeholders
    const today = new Date().toISOString().split('T')[0];
    template = template.replace(/\[Feature Name\]/g, featureName);
    template = template.replace(/PRD-XXX/g, `PRD-${prdId}`);
    template = template.replace(/YYYY-MM-DD/g, today);
    
    const prdPath = path.join(folderPath, 'prd.md');
    fs.writeFileSync(prdPath, template, 'utf-8');
    console.log(`✅ Created prd.md from template`);
  } else {
    console.warn(`⚠️  Template not found at ${TEMPLATE_PATH}`);
    console.warn(`   Creating basic prd.md...`);
    
    const basicPrd = `# ${featureName} - PRD

**ID**: PRD-${prdId}  
**Status**: Draft  
**Owner**: [Name]  
**Created**: ${new Date().toISOString().split('T')[0]}  
**Last Updated**: ${new Date().toISOString().split('T')[0]}

---

## Summary

[Add summary here]

---

## Problem Statement

**User Need**: 

**Business Goal**: 

**Success Metric**: 

---

## Requirements

### Must Have (P0)
- [ ] 

### Should Have (P1)
- [ ] 

---

*Fill out the rest of the PRD using the template guidelines*
`;
    
    const prdPath = path.join(folderPath, 'prd.md');
    fs.writeFileSync(prdPath, basicPrd, 'utf-8');
    console.log(`✅ Created basic prd.md`);
  }

  // Create mockups directory
  const mockupsPath = path.join(folderPath, 'mockups');
  fs.mkdirSync(mockupsPath);
  fs.writeFileSync(path.join(mockupsPath, '.gitkeep'), '', 'utf-8');
  console.log(`✅ Created mockups/ directory`);

  return {
    prdId,
    folderName,
    folderPath,
    prdPath: path.join(folderPath, 'prd.md'),
  };
}

function printNextSteps(info) {
  console.log('\n📋 Next Steps:\n');
  console.log(`1. Edit your PRD:`);
  console.log(`   ${info.prdPath}`);
  console.log('');
  console.log(`2. Add supporting documents (optional):`);
  console.log(`   - ${path.join(info.folderPath, 'research.md')}`);
  console.log(`   - ${path.join(info.folderPath, 'technical-specs.md')}`);
  console.log(`   - ${path.join(info.folderPath, 'decisions.md')}`);
  console.log('');
  console.log(`3. Add design mockups to:`);
  console.log(`   ${path.join(info.folderPath, 'mockups/')}`);
  console.log('');
  console.log(`4. Update ${path.join(PRDS_DIR, 'README.md')} to include PRD-${info.prdId}`);
  console.log('');
  console.log(`5. Commit your changes:`);
  console.log(`   git add prds/${info.folderName}/`);
  console.log(`   git commit -m "Add PRD-${info.prdId}: [Feature Name]"`);
  console.log('');
}

function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    console.log('Usage: node create_prd.js "Feature Name"');
    console.log('');
    console.log('Example:');
    console.log('  node create_prd.js "AI Code Review"');
    console.log('  node create_prd.js "User Authentication"');
    process.exit(0);
  }

  const featureName = args[0];
  
  console.log(`\n🚀 Creating new PRD for: ${featureName}\n`);
  
  const info = createPrdFolder(featureName);
  
  console.log(`\n✅ PRD ${info.prdId} created successfully!\n`);
  console.log(`📁 Location: ${info.folderPath}`);
  
  printNextSteps(info);
}

if (require.main === module) {
  main();
}

module.exports = { createPrdFolder, getNextPrdNumber, toKebabCase };
