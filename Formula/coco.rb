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
  url "https://github.com/coco-research/coco/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "8b34573808129125d123bced8fdf770c2be58c33718e0acf4b444a5989a8187e"
  license "MIT"
  version "1.0.0"

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
        coco                              # auto-detect (Claude Code, Cursor, Codex, generic)
        coco --adapter claude-code        # override
        coco --systems gsd,brain,team     # add bundles

      To uninstall the symlinks (without removing the formula):
        find ~/.claude ~/.cursor -type l -lname "*#{libexec}*" -delete
    EOS
  end

  test do
    assert_match "Coco", shell_output("#{bin}/coco --help 2>&1 || true")
  end
end
