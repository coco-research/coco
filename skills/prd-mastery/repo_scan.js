#!/usr/bin/env node

/**
 * Repository Reconnaissance Script
 * 
 * Automatically scans a repository to determine:
 * - Project type (new vs existing)
 * - Technology stack
 * - Architecture patterns
 * - Key observations
 * 
 * Outputs findings to prelim_summary.md for context-aware PRD creation.
 */

const fs = require('fs');
const path = require('path');

// Configuration
const OUTPUT_FILE = 'prelim_summary.md';
const SCAN_ROOT = process.cwd();

// Helper functions
function fileExists(filePath) {
  return fs.existsSync(path.join(SCAN_ROOT, filePath));
}

function readJsonFile(filePath) {
  try {
    const fullPath = path.join(SCAN_ROOT, filePath);
    if (fs.existsSync(fullPath)) {
      return JSON.parse(fs.readFileSync(fullPath, 'utf-8'));
    }
  } catch (error) {
    console.warn(`Warning: Could not read ${filePath}:`, error.message);
  }
  return null;
}

function detectProjectType() {
  // Check for common project indicators
  const hasPackageJson = fileExists('package.json');
  const hasGit = fileExists('.git');
  const hasSrc = fileExists('src') || fileExists('app');
  
  if (!hasPackageJson && !hasGit && !hasSrc) {
    return 'New Project (No existing codebase detected)';
  }
  
  return 'Existing Project';
}

function detectFramework() {
  const packageJson = readJsonFile('package.json');
  const frameworks = [];
  
  if (packageJson) {
    const deps = { ...packageJson.dependencies, ...packageJson.devDependencies };
    
    if (deps['next']) frameworks.push(`Next.js ${deps['next']}`);
    if (deps['react']) frameworks.push(`React ${deps['react']}`);
    if (deps['vue']) frameworks.push(`Vue ${deps['vue']}`);
    if (deps['svelte']) frameworks.push(`Svelte ${deps['svelte']}`);
    if (deps['angular']) frameworks.push(`Angular ${deps['angular']}`);
    if (deps['express']) frameworks.push(`Express ${deps['express']}`);
    if (deps['fastify']) frameworks.push(`Fastify ${deps['fastify']}`);
  }
  
  return frameworks.length > 0 ? frameworks : ['None detected'];
}

function detectLanguage() {
  const languages = [];
  
  if (fileExists('tsconfig.json')) languages.push('TypeScript');
  if (fileExists('package.json')) languages.push('JavaScript');
  if (fileExists('requirements.txt') || fileExists('pyproject.toml')) languages.push('Python');
  if (fileExists('go.mod')) languages.push('Go');
  if (fileExists('Cargo.toml')) languages.push('Rust');
  if (fileExists('pom.xml') || fileExists('build.gradle')) languages.push('Java');
  
  return languages.length > 0 ? languages : ['None detected'];
}

function detectDatabase() {
  const packageJson = readJsonFile('package.json');
  const databases = [];
  
  if (packageJson) {
    const deps = { ...packageJson.dependencies, ...packageJson.devDependencies };
    
    if (deps['prisma'] || deps['@prisma/client']) databases.push('Prisma ORM');
    if (deps['mongoose']) databases.push('MongoDB (Mongoose)');
    if (deps['pg']) databases.push('PostgreSQL');
    if (deps['mysql'] || deps['mysql2']) databases.push('MySQL');
    if (deps['sqlite3']) databases.push('SQLite');
    if (deps['@upstash/vector']) databases.push('Upstash Vector DB');
    if (deps['redis']) databases.push('Redis');
  }
  
  if (fileExists('prisma/schema.prisma')) databases.push('Prisma (schema detected)');
  
  return databases.length > 0 ? databases : ['None detected'];
}

function detectArchitecture() {
  const patterns = [];
  
  // Check for common architecture patterns
  if (fileExists('app')) patterns.push('Next.js App Router');
  if (fileExists('pages')) patterns.push('Next.js Pages Router');
  if (fileExists('src/app')) patterns.push('Next.js App Router (src)');
  if (fileExists('src/pages')) patterns.push('Next.js Pages Router (src)');
  
  // Check for monorepo
  if (fileExists('pnpm-workspace.yaml')) patterns.push('pnpm Monorepo');
  if (fileExists('turbo.json')) patterns.push('Turborepo');
  if (fileExists('nx.json')) patterns.push('Nx Monorepo');
  
  // Check for microservices indicators
  if (fileExists('docker-compose.yml')) patterns.push('Docker Compose (multiple services)');
  if (fileExists('kubernetes')) patterns.push('Kubernetes');
  
  return patterns.length > 0 ? patterns : ['Standard structure'];
}

function detectAuthentication() {
  const packageJson = readJsonFile('package.json');
  const auth = [];
  
  if (packageJson) {
    const deps = { ...packageJson.dependencies, ...packageJson.devDependencies };
    
    if (deps['next-auth'] || deps['@auth/core']) auth.push('Auth.js / NextAuth');
    if (deps['@clerk/nextjs']) auth.push('Clerk');
    if (deps['@supabase/auth-helpers-nextjs']) auth.push('Supabase Auth');
    if (deps['passport']) auth.push('Passport.js');
    if (deps['jsonwebtoken']) auth.push('JWT');
  }
  
  return auth.length > 0 ? auth : ['None detected'];
}

function detectAIIntegrations() {
  const packageJson = readJsonFile('package.json');
  const ai = [];
  
  if (packageJson) {
    const deps = { ...packageJson.dependencies, ...packageJson.devDependencies };
    
    if (deps['ai'] || deps['@ai-sdk/core']) ai.push('Vercel AI SDK');
    if (deps['@anthropic-ai/sdk']) ai.push('Anthropic');
    if (deps['openai']) ai.push('OpenAI');
    if (deps['@google/generative-ai']) ai.push('Google AI');
    if (deps['langchain']) ai.push('LangChain');
  }
  
  return ai.length > 0 ? ai : ['None detected'];
}

function detectDeployment() {
  const deployment = [];
  
  if (fileExists('vercel.json') || fileExists('.vercel')) deployment.push('Vercel');
  if (fileExists('netlify.toml')) deployment.push('Netlify');
  if (fileExists('Dockerfile')) deployment.push('Docker');
  if (fileExists('.github/workflows')) deployment.push('GitHub Actions');
  if (fileExists('.gitlab-ci.yml')) deployment.push('GitLab CI');
  
  return deployment.length > 0 ? deployment : ['None detected'];
}

function analyzeDocumentation() {
  const docs = [];
  
  if (fileExists('README.md')) docs.push('README.md exists');
  if (fileExists('CONTRIBUTING.md')) docs.push('CONTRIBUTING.md exists');
  if (fileExists('docs')) docs.push('docs/ directory exists');
  if (fileExists('.claude/skills')) docs.push('Claude skills exist');
  
  return docs.length > 0 ? docs : ['No documentation detected'];
}

function getProjectStats() {
  const stats = {
    hasTests: fileExists('__tests__') || fileExists('tests') || fileExists('test'),
    hasCI: fileExists('.github/workflows') || fileExists('.gitlab-ci.yml'),
    hasLinting: fileExists('.eslintrc.json') || fileExists('.eslintrc.js') || fileExists('eslint.config.js'),
    hasPrettier: fileExists('.prettierrc') || fileExists('prettier.config.js'),
    hasTypeScript: fileExists('tsconfig.json'),
  };
  
  return stats;
}

function generateRecommendations(findings) {
  const recommendations = [];
  
  if (findings.projectType.includes('New')) {
    recommendations.push('Start with architecture decisions and tech stack selection');
    recommendations.push('Consider creating an Architecture Decision Record (ADR)');
    recommendations.push('Define core requirements before implementation');
  } else {
    recommendations.push('Review existing architecture before proposing changes');
    recommendations.push('Consider backward compatibility and migration paths');
    recommendations.push('Validate changes align with current patterns');
  }
  
  if (!findings.stats.hasTests) {
    recommendations.push('Consider adding testing infrastructure');
  }
  
  if (!findings.stats.hasCI) {
    recommendations.push('Consider setting up continuous integration');
  }
  
  if (findings.ai.length > 1 && !findings.ai.includes('None detected')) {
    recommendations.push('Multiple AI integrations detected - consider standardization');
  }
  
  return recommendations;
}

function generateMarkdownReport(findings) {
  const timestamp = new Date().toISOString();
  
  return `# Preliminary Project Summary

**Generated**: ${timestamp}  
**Scan Root**: ${SCAN_ROOT}

---

## Project Overview

**Project Type**: ${findings.projectType}

---

## Technology Stack

### Frameworks
${findings.frameworks.map(f => `- ${f}`).join('\n')}

### Languages
${findings.languages.map(l => `- ${l}`).join('\n')}

### Database
${findings.databases.map(d => `- ${d}`).join('\n')}

---

## Architecture

### Patterns
${findings.architecture.map(a => `- ${a}`).join('\n')}

### Authentication
${findings.authentication.map(a => `- ${a}`).join('\n')}

### AI Integrations
${findings.ai.map(a => `- ${a}`).join('\n')}

### Deployment
${findings.deployment.map(d => `- ${d}`).join('\n')}

---

## Project Health

- **Tests**: ${findings.stats.hasTests ? '✅ Yes' : '❌ No'}
- **CI/CD**: ${findings.stats.hasCI ? '✅ Yes' : '❌ No'}
- **Linting**: ${findings.stats.hasLinting ? '✅ Yes' : '❌ No'}
- **Code Formatting**: ${findings.stats.hasPrettier ? '✅ Yes' : '❌ No'}
- **TypeScript**: ${findings.stats.hasTypeScript ? '✅ Yes' : '❌ No'}

---

## Documentation

${findings.documentation.map(d => `- ${d}`).join('\n')}

---

## Key Observations

${findings.observations.join('\n')}

---

## Recommended Next Steps

${findings.recommendations.map((r, i) => `${i + 1}. ${r}`).join('\n')}

---

## Notes

This summary provides context for PRD creation. Use this information to:
- Frame context-aware questions
- Validate technical feasibility
- Identify integration constraints
- Understand project maturity

For new PRDs, reference this document to ensure alignment with existing architecture and patterns.

---

*Generated by PRD Mastery Repository Reconnaissance Script*
`;
}

function generateObservations(findings) {
  const observations = [];
  
  if (findings.frameworks.length > 2 && !findings.frameworks.includes('None detected')) {
    observations.push('- **Multiple Frameworks**: Consider consolidating to reduce complexity');
  }
  
  if (findings.ai.some(a => a.includes('AI SDK'))) {
    observations.push('- **AI Integration**: Project has AI capabilities - consider AI-driven features');
  }
  
  if (findings.authentication.includes('None detected')) {
    observations.push('- **No Authentication**: Consider adding auth if user features are planned');
  }
  
  if (findings.architecture.some(a => a.includes('App Router'))) {
    observations.push('- **Modern Next.js**: Using App Router - leverage server components and actions');
  }
  
  if (findings.databases.some(d => d.includes('Prisma'))) {
    observations.push('- **Prisma ORM**: Type-safe database access - ensure schema migrations are planned');
  }
  
  if (findings.databases.some(d => d.includes('Vector'))) {
    observations.push('- **Vector Database**: Semantic search capability - consider AI-powered search features');
  }
  
  if (observations.length === 0) {
    observations.push('- No specific concerns detected - standard project structure');
  }
  
  return observations;
}

// Main execution
function main() {
  console.log('🔍 Starting repository reconnaissance...\n');
  
  // Gather findings
  const findings = {
    projectType: detectProjectType(),
    frameworks: detectFramework(),
    languages: detectLanguage(),
    databases: detectDatabase(),
    architecture: detectArchitecture(),
    authentication: detectAuthentication(),
    ai: detectAIIntegrations(),
    deployment: detectDeployment(),
    documentation: analyzeDocumentation(),
    stats: getProjectStats(),
  };
  
  // Generate observations and recommendations
  findings.observations = generateObservations(findings);
  findings.recommendations = generateRecommendations(findings);
  
  // Generate markdown report
  const report = generateMarkdownReport(findings);
  
  // Write to file
  fs.writeFileSync(OUTPUT_FILE, report, 'utf-8');
  
  console.log('✅ Reconnaissance complete!');
  console.log(`📄 Report saved to: ${OUTPUT_FILE}\n`);
  console.log('Summary:');
  console.log(`  Project Type: ${findings.projectType}`);
  console.log(`  Frameworks: ${findings.frameworks.join(', ')}`);
  console.log(`  Languages: ${findings.languages.join(', ')}`);
  console.log(`  Architecture: ${findings.architecture.join(', ')}`);
  console.log('\n📖 Review the full report for detailed analysis.\n');
}

// Run the script
if (require.main === module) {
  main();
}

module.exports = {
  detectProjectType,
  detectFramework,
  detectLanguage,
  detectDatabase,
  detectArchitecture,
  detectAuthentication,
  detectAIIntegrations,
  detectDeployment,
  analyzeDocumentation,
  getProjectStats,
  generateRecommendations,
};
