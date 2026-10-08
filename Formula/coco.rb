# Homebrew formula for Coco
#
# Distribution path A — homebrew-tap (recommended):
#   1. Create a github.com/coco-research/homebrew-coco repo
#   2. Copy this file to that repo as `Formula/coco.rb`
#   3. Tag a release on coco-research/coco with `v1.0.0`
#   4. Update sha256 below to match the release tarball
#   5. Users install via: `brew install coco-research/coco/coco`
#
# Distribution path B — homebrew-core (later, requires popularity threshold):
#   - Submit this formula to https://github.com/Homebrew/homebrew-core
#   - Users install via: `brew install coco`

class Coco < Formula
  desc "Open-source AI workflow framework — skills, agents, commands, multi-agent orchestration"
  homepage "https://github.com/coco-research/coco"
  url "https://github.com/coco-research/coco/archive/refs/tags/v1.5.1.tar.gz"
  sha256 "bc2971276a4ee11f5ad3a3347ef1083eb9cd93ab95127e538bbfb97c82e5fd9d"
  # Open-core: MIT core (see LICENSE) + proprietary Super Intelligence
  # (see systems/superintelligence/LICENSE). Not a single SPDX identifier.
  license :cannot_represent
  version "1.5.1"

  depends_on "git"
  depends_on "bash"

  def install
    libexec.install Dir["*"]
    (bin/"coco").write <<~SH
      #!/usr/bin/env bash
      exec bash "#{libexec}/install.sh" "$@"
    SH
    chmod 0755, bin/"coco"
  end

  def caveats
    <<~EOS
      Coco was installed to:
        #{libexec}

      To install Coco artifacts into your AI tool's expected paths:
        coco                              # auto-detect; installs every default bundle
        coco --adapter claude-code        # override
        coco --systems gsd,brain          # replaces the default set: ONLY these bundles
        coco --core-only                  # no bundles

      The links point into the versioned path above. Re-run coco after
      `brew upgrade` or `brew cleanup` so they follow the new version.

      To uninstall the symlinks (without removing the formula):
        find ~/.claude ~/.cursor ~/.grok ~/.copilot -type l -lname "#{libexec}/*" -delete
        for app in "Code" "Code - Insiders" "VSCodium" "VSCodium - Insiders"; do for base in "$HOME/Library/Application Support" "${XDG_CONFIG_HOME:-$HOME/.config}"; do [ -d "$base/$app/User" ] && find "$base/$app/User" -type l -lname "#{libexec}/*" -delete; done; done
      Generated files (Super Intelligence commands, the Coco block in
      ~/.claude/CLAUDE.md) are real files, not links; see the Uninstall section of
      https://github.com/coco-research/coco/blob/main/docs/install.md
    EOS
  end

  test do
    assert_match "Coco", shell_output("#{bin}/coco --help 2>&1 || true")
  end
end
