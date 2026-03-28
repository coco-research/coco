import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, basename } from 'node:path';
import { homedir } from 'node:os';
import matter from 'gray-matter';

export interface Skill {
  name: string;           // e.g., "team-research"
  command: string;        // e.g., "/team research"
  description: string;    // first meaningful line from the file
  filePath: string;       // absolute path
  category: string;       // "team" | "gsd" | "email" | "pmstudio" | "standalone"
  isWriteOperation: boolean;
  keywords: string[];     // extracted trigger words for matching
}

const WRITE_PATTERNS = /\b(develop|fix|execute|build|create|edit|deploy|push|delete|remove|write)\b/i;

export class SkillRegistry {
  private skills: Map<string, Skill> = new Map();
  private keywordIndex: Map<string, string> = new Map(); // keyword -> skill name

  async loadAll(): Promise<void> {
    this.skills.clear();
    this.keywordIndex.clear();

    // Global commands
    const globalDir = join(homedir(), '.claude', 'commands');
    if (existsSync(globalDir)) {
      this.loadDirectory(globalDir);
    }

    // GSD subcommands
    const gsdDir = join(homedir(), '.claude', 'commands', 'gsd');
    if (existsSync(gsdDir)) {
      this.loadDirectory(gsdDir, 'gsd');
    }

    // Project-level commands (cwd)
    const projectDir = join(process.cwd(), '.claude', 'commands');
    if (existsSync(projectDir)) {
      this.loadDirectory(projectDir, 'project');
    }
  }

  private loadDirectory(dir: string, categoryOverride?: string): void {
    const files = readdirSync(dir).filter(f => f.endsWith('.md'));

    for (const file of files) {
      const filePath = join(dir, file);
      try {
        const skill = this.parseSkillFile(filePath, categoryOverride);
        if (skill) {
          this.skills.set(skill.name, skill);
          // Index keywords
          for (const kw of skill.keywords) {
            this.keywordIndex.set(kw.toLowerCase(), skill.name);
          }
        }
      } catch (e) {
        console.warn('Failed to parse skill:', filePath, (e as Error).message);
      }
    }
  }

  private parseSkillFile(filePath: string, categoryOverride?: string): Skill | null {
    const raw = readFileSync(filePath, 'utf-8');
    const name = basename(filePath, '.md');

    // Try to parse frontmatter (gray-matter)
    let description = '';
    let keywords: string[] = [];

    try {
      const parsed = matter(raw);
      if (parsed.data.description) {
        description = parsed.data.description;
      }
      if (parsed.data.keywords) {
        keywords = Array.isArray(parsed.data.keywords)
          ? parsed.data.keywords
          : String(parsed.data.keywords).split(',').map(k => k.trim());
      }
    } catch {
      // No frontmatter — that's fine
    }

    // Fallback: extract description from first heading or first non-empty line
    if (!description) {
      const lines = raw.split('\n');
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('# ')) {
          // Extract text after the command name: "# /team research — Research Pipeline" -> "Research Pipeline"
          const dashMatch = trimmed.match(/[—–-]\s*(.+)$/);
          if (dashMatch) {
            description = dashMatch[1].trim();
          } else {
            description = trimmed.replace(/^#\s*/, '');
          }
          break;
        }
        if (trimmed.startsWith('>')) {
          description = trimmed.replace(/^>\s*/, '');
          break;
        }
        if (trimmed && !trimmed.startsWith('#')) {
          description = trimmed;
          break;
        }
      }
    }

    // Auto-generate keywords from the name
    if (keywords.length === 0) {
      // "team-research" -> ["team", "research"]
      keywords = name.split('-').filter(k => k.length > 2);
      // Add description words (nouns/verbs)
      if (description) {
        const descWords = description
          .toLowerCase()
          .replace(/[^a-z\s]/g, '')
          .split(/\s+/)
          .filter(w => w.length > 3);
        keywords.push(...descWords.slice(0, 5));
      }
    }

    // Determine category
    let category = categoryOverride || 'standalone';
    if (name.startsWith('team-') || name === 'team') category = 'team';
    else if (name.startsWith('gsd') || name.startsWith('gsd:')) category = 'gsd';
    else if (name.startsWith('email')) category = 'email';
    else if (name.startsWith('pmstudio')) category = 'pmstudio';

    // Determine command format
    let command: string;
    if (category === 'team' && name.startsWith('team-')) {
      command = `/team ${name.replace('team-', '')}`;
    } else if (category === 'gsd' && categoryOverride === 'gsd') {
      command = `/gsd:${name}`;
    } else {
      command = `/${name}`;
    }

    const isWriteOperation = WRITE_PATTERNS.test(name) || WRITE_PATTERNS.test(description);

    return {
      name,
      command,
      description: description || name,
      filePath,
      category,
      isWriteOperation,
      keywords: [...new Set(keywords)], // dedupe
    };
  }

  // --- Lookups ---

  get(name: string): Skill | undefined {
    return this.skills.get(name);
  }

  findByKeyword(text: string): Skill | undefined {
    const lower = text.toLowerCase();

    // 1. Exact slash command match: "/team research" or "/email-read"
    for (const skill of this.skills.values()) {
      if (lower.startsWith(skill.command)) {
        return skill;
      }
    }

    // 2. Direct name match: "team-research"
    const directMatch = this.skills.get(lower);
    if (directMatch) return directMatch;

    // 3. Keyword match: score each skill by how many keywords appear in the input
    let bestSkill: Skill | undefined;
    let bestScore = 0;

    for (const skill of this.skills.values()) {
      let score = 0;
      for (const kw of skill.keywords) {
        if (lower.includes(kw.toLowerCase())) {
          score += kw.length; // longer keyword matches = higher confidence
        }
      }
      if (score > bestScore) {
        bestScore = score;
        bestSkill = skill;
      }
    }

    return bestScore > 3 ? bestSkill : undefined; // minimum threshold
  }

  getAll(): Skill[] {
    return Array.from(this.skills.values());
  }

  getByCategory(category: string): Skill[] {
    return this.getAll().filter(s => s.category === category);
  }

  toPromptContext(): string {
    const lines = ['Available skills:'];
    const byCategory = new Map<string, Skill[]>();

    for (const skill of this.skills.values()) {
      const list = byCategory.get(skill.category) || [];
      list.push(skill);
      byCategory.set(skill.category, list);
    }

    for (const [category, skills] of byCategory) {
      lines.push(`\n### ${category}`);
      for (const skill of skills) {
        const writeTag = skill.isWriteOperation ? ' [WRITE]' : '';
        lines.push(`- ${skill.command} — ${skill.description}${writeTag}`);
      }
    }

    return lines.join('\n');
  }

  get size(): number {
    return this.skills.size;
  }
}
