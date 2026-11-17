<planning_config>

Configuration options for `.planning/` directory behavior.

<config_schema>
```json
"planning": {
  "commit_docs": true,
  "search_gitignored": false
},
"git": {
  "branching_strategy": "none",
  "base_branch": null,
  "phase_branch_template": "gsd/phase-{phase}-{slug}",
  "milestone_branch_template": "gsd/{milestone}-{slug}",
  "quick_branch_template": null
},
"manager": {
  "flags": {
    "discuss": "",
    "plan": "",
    "execute": ""
  }
}
```

| Option | Default | Description |
|--------|---------|-------------|
| `commit_docs` | `true` | Whether to commit planning artifacts to git |
| `search_gitignored` | `false` | Add `--no-ignore` to broad rg searches |
| `git.branching_strategy` | `"none"` | Git branching approach: `"none"`, `"phase"`, or `"milestone"` |
| `git.base_branch` | `null` (auto-detect) | Target branch for PRs and merges (e.g. `"master"`, `"develop"`). When `null`, auto-detects from `git symbolic-ref refs/remotes/origin/HEAD`, falling back to `"main"`. |
| `git.create_tag` | `true` | Create git tags on milestone completion |
