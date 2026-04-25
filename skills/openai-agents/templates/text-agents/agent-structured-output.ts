/**
 * Structured Output with Zod Schemas
 *
 * Demonstrates:
 * - Defining output schemas with Zod
 * - Type-safe structured responses
 * - Extracting specific data formats
 * - Using reasoning in structured outputs
 */

import { z } from 'zod';
import { Agent, run } from '@openai/agents';

// ========================================
// Example 1: Contact Information Extraction
// ========================================

const contactInfoSchema = z.object({
  name: z.string().describe('Full name of the person'),
  email: z.string().email().describe('Email address'),
  phone: z.string().optional().describe('Phone number if mentioned'),
  company: z.string().optional().describe('Company name if mentioned'),
  reasoning: z.string().describe('Brief explanation of how you extracted this information'),
});

const contactExtractorAgent = new Agent({
  name: 'Contact Extractor',
  instructions: 'Extract contact information from text. Be thorough but only extract information that is explicitly mentioned.',
  outputType: contactInfoSchema,
});

// ========================================
// Example 2: Sentiment Analysis
// ========================================

const sentimentSchema = z.object({
  sentiment: z.enum(['positive', 'negative', 'neutral', 'mixed']),
  confidence: z.number().min(0).max(1).describe('Confidence score from 0 to 1'),
  keyPhrases: z.array(z.string()).describe('Key phrases that indicate the sentiment'),
  reasoning: z.string().describe('Explanation of the sentiment analysis'),
});

const sentimentAgent = new Agent({
  name: 'Sentiment Analyzer',
  instructions: 'Analyze the sentiment of the given text. Consider tone, word choice, and context.',
  outputType: sentimentSchema,
});

// ========================================
// Example 3: Task Breakdown
// ========================================

const taskSchema = z.object({
  title: z.string(),
  priority: z.enum(['low', 'medium', 'high', 'urgent']),
  estimatedHours: z.number(),
  dependencies: z.array(z.string()),
});

const taskBreakdownSchema = z.object({
  projectName: z.string(),
  tasks: z.array(taskSchema),
  totalEstimatedHours: z.number(),
  reasoning: z.string().describe('Explanation of how you broke down the project'),
});

const taskPlannerAgent = new Agent({
  name: 'Task Planner',
  instructions: 'Break down project descriptions into concrete tasks with priorities and time estimates.',
  outputType: taskBreakdownSchema,
});

// ========================================
// Usage Examples
// ========================================

async function exampleContactExtraction() {
  const text = `
    Hi, I'm Sarah Johnson from TechCorp.
    You can reach me at sarah.j@techcorp.com or call me at (555) 123-4567.
  `;

  const result = await run(contactExtractorAgent, text);

  console.log('\n📇 Contact Extraction:');
  console.log('Name:', result.finalOutput.name);
  console.log('Email:', result.finalOutput.email);
  console.log('Phone:', result.finalOutput.phone);
  console.log('Company:', result.finalOutput.company);
  console.log('Reasoning:', result.finalOutput.reasoning);
}

async function exampleSentimentAnalysis() {
  const review = `
    I absolutely love this product! The design is beautiful and it works flawlessly.
    However, the customer service could be better. Overall, very satisfied with my purchase.
  `;

  const result = await run(sentimentAgent, review);

  console.log('\n😊 Sentiment Analysis:');
  console.log('Sentiment:', result.finalOutput.sentiment);
  console.log('Confidence:', result.finalOutput.confidence);
  console.log('Key Phrases:', result.finalOutput.keyPhrases);
  console.log('Reasoning:', result.finalOutput.reasoning);
}

async function exampleTaskPlanning() {
  const project = `
    Build a user authentication system with email/password login,
    social OAuth, password reset, and two-factor authentication.
    Should integrate with our existing PostgreSQL database.
  `;

  const result = await run(taskPlannerAgent, project);

  console.log('\n📋 Task Breakdown:');
  console.log('Project:', result.finalOutput.projectName);
  console.log('Total Hours:', result.finalOutput.totalEstimatedHours);
  console.log('\nTasks:');
  result.finalOutput.tasks.forEach((task, i) => {
    console.log(`\n${i + 1}. ${task.title}`);
    console.log(`   Priority: ${task.priority}`);
    console.log(`   Hours: ${task.estimatedHours}`);
    console.log(`   Dependencies: ${task.dependencies.join(', ') || 'None'}`);
  });
  console.log('\nReasoning:', result.finalOutput.reasoning);
}

async function main() {
  try {
    await exampleContactExtraction();
    await exampleSentimentAnalysis();
    await exampleTaskPlanning();
  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  }
}

// Uncomment to run
// main();

export {
  contactExtractorAgent,
  sentimentAgent,
  taskPlannerAgent,
  contactInfoSchema,
  sentimentSchema,
  taskBreakdownSchema,
};
