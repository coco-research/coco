/**
 * Parallel Agent Execution
 *
 * Demonstrates:
 * - Running multiple agents in parallel
 * - Using Promise.all for concurrent execution
 * - Selecting best result from multiple agents
 * - Aggregating results from parallel tasks
 */

import { z } from 'zod';
import { Agent, run } from '@openai/agents';

// ========================================
// Example 1: Multiple Approaches to Same Problem
// ========================================

const creativeWriterAgent = new Agent({
  name: 'Creative Writer',
  instructions: 'Write engaging, creative marketing copy with emotional appeal and storytelling.',
  outputType: z.object({
    headline: z.string(),
    body: z.string(),
    cta: z.string(),
  }),
});

const technicalWriterAgent = new Agent({
  name: 'Technical Writer',
  instructions: 'Write clear, factual marketing copy focused on features and benefits.',
  outputType: z.object({
    headline: z.string(),
    body: z.string(),
    cta: z.string(),
  }),
});

const humorWriterAgent = new Agent({
  name: 'Humor Writer',
  instructions: 'Write fun, witty marketing copy that entertains while informing.',
  outputType: z.object({
    headline: z.string(),
    body: z.string(),
    cta: z.string(),
  }),
});

async function generateMarketingCopyVariants(product: string) {
  console.log('\n📝 Generating 3 marketing copy variants in parallel...\n');

  // Run all agents in parallel
  const [creative, technical, humor] = await Promise.all([
    run(creativeWriterAgent, `Write marketing copy for: ${product}`),
    run(technicalWriterAgent, `Write marketing copy for: ${product}`),
    run(humorWriterAgent, `Write marketing copy for: ${product}`),
  ]);

  console.log('✅ All variants generated!\n');

  // Display results
  console.log('📖 CREATIVE VERSION:');
  console.log('──────────────────────────────────────');
  console.log('Headline:', creative.finalOutput.headline);
  console.log('Body:', creative.finalOutput.body);
  console.log('CTA:', creative.finalOutput.cta);

  console.log('\n🔧 TECHNICAL VERSION:');
  console.log('──────────────────────────────────────');
  console.log('Headline:', technical.finalOutput.headline);
  console.log('Body:', technical.finalOutput.body);
  console.log('CTA:', technical.finalOutput.cta);

  console.log('\n😄 HUMOR VERSION:');
  console.log('──────────────────────────────────────');
  console.log('Headline:', humor.finalOutput.headline);
  console.log('Body:', humor.finalOutput.body);
  console.log('CTA:', humor.finalOutput.cta);

  console.log('\n📊 Token Usage Summary:');
  console.log('Creative:', creative.usage.totalTokens, 'tokens');
  console.log('Technical:', technical.usage.totalTokens, 'tokens');
  console.log('Humor:', humor.usage.totalTokens, 'tokens');
  console.log('Total:', creative.usage.totalTokens + technical.usage.totalTokens + humor.usage.totalTokens);

  return { creative, technical, humor };
}

// ========================================
// Example 2: Parallel Research Tasks
// ========================================

const summarizerAgent = new Agent({
  name: 'Summarizer',
  instructions: 'Create a concise summary of the topic in 2-3 sentences.',
});

const prosConsAgent = new Agent({
  name: 'Pros/Cons Analyzer',
  instructions: 'List the main pros and cons of this topic.',
  outputType: z.object({
    pros: z.array(z.string()),
    cons: z.array(z.string()),
  }),
});

const expertQuotesAgent = new Agent({
  name: 'Expert Quotes Generator',
  instructions: 'Generate 2-3 realistic expert quotes about this topic.',
  outputType: z.array(z.object({
    expert: z.string(),
    quote: z.string(),
  })),
});

const statisticsAgent = new Agent({
  name: 'Statistics Finder',
  instructions: 'Generate plausible statistics related to this topic.',
  outputType: z.array(z.object({
    statistic: z.string(),
    source: z.string(),
  })),
});

async function comprehensiveResearch(topic: string) {
  console.log(`\n🔍 Researching: ${topic}\n`);
  console.log('Running 4 agents in parallel...\n');

  // Execute all research tasks concurrently
  const [summary, proscons, quotes, stats] = await Promise.all([
    run(summarizerAgent, topic),
    run(prosConsAgent, topic),
    run(expertQuotesAgent, topic),
    run(statisticsAgent, topic),
  ]);

  console.log('✅ Research complete!\n');

  // Aggregate results into a comprehensive report
  console.log('=' .repeat(60));
  console.log(`RESEARCH REPORT: ${topic}`);
  console.log('='.repeat(60));

  console.log('\n📄 SUMMARY:');
  console.log(summary.finalOutput);

  console.log('\n✅ PROS:');
  proscons.finalOutput.pros.forEach((pro, i) => {
    console.log(`${i + 1}. ${pro}`);
  });

  console.log('\n❌ CONS:');
  proscons.finalOutput.cons.forEach((con, i) => {
    console.log(`${i + 1}. ${con}`);
  });

  console.log('\n💬 EXPERT QUOTES:');
  quotes.finalOutput.forEach(quote => {
    console.log(`"${quote.quote}" - ${quote.expert}`);
  });

  console.log('\n📊 STATISTICS:');
  stats.finalOutput.forEach(stat => {
    console.log(`• ${stat.statistic} (Source: ${stat.source})`);
  });

  console.log('\n' + '='.repeat(60));
  console.log('📊 Total tokens used:',
    summary.usage.totalTokens +
    proscons.usage.totalTokens +
    quotes.usage.totalTokens +
    stats.usage.totalTokens
  );
  console.log('='.repeat(60) + '\n');
}

// ========================================
// Example 3: Quality Voting (Select Best Result)
// ========================================

const evaluatorAgent = new Agent({
  name: 'Evaluator',
  instructions: 'Rate the quality of this marketing copy on a scale of 1-10 and explain why.',
  outputType: z.object({
    score: z.number().min(1).max(10),
    reasoning: z.string(),
  }),
});

async function selectBestVariant(product: string) {
  console.log('\n🏆 Generating variants and selecting the best one...\n');

  // Generate variants in parallel
  const variants = await generateMarketingCopyVariants(product);

  console.log('\n\n🎯 Evaluating all variants...\n');

  // Evaluate each variant in parallel
  const evaluations = await Promise.all([
    run(evaluatorAgent, `Evaluate this headline: ${variants.creative.finalOutput.headline}`),
    run(evaluatorAgent, `Evaluate this headline: ${variants.technical.finalOutput.headline}`),
    run(evaluatorAgent, `Evaluate this headline: ${variants.humor.finalOutput.headline}`),
  ]);

  // Find best variant
  const scores = [
    { name: 'Creative', score: evaluations[0].finalOutput.score, reasoning: evaluations[0].finalOutput.reasoning },
    { name: 'Technical', score: evaluations[1].finalOutput.score, reasoning: evaluations[1].finalOutput.reasoning },
    { name: 'Humor', score: evaluations[2].finalOutput.score, reasoning: evaluations[2].finalOutput.reasoning },
  ];

  const winner = scores.reduce((best, current) =>
    current.score > best.score ? current : best
  );

  console.log('🥇 WINNER:', winner.name, 'with score', winner.score, '/10');
  console.log('Reasoning:', winner.reasoning);
}

// ========================================
// Usage
// ========================================

async function main() {
  try {
    // Example 1: Marketing copy variants
    await generateMarketingCopyVariants(
      'AI-powered task management app for developers'
    );

    console.log('\n\n');

    // Example 2: Comprehensive research
    await comprehensiveResearch(
      'The impact of AI on software development productivity'
    );

    console.log('\n\n');

    // Example 3: Quality voting
    await selectBestVariant(
      'AI-powered task management app for developers'
    );

  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  }
}

// Uncomment to run
// main();

export {
  generateMarketingCopyVariants,
  comprehensiveResearch,
  selectBestVariant,
};
