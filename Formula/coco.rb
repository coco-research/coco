# Homebrew formula for Coco
#
# Distribution path A — homebrew-tap (recommended):
#   1. Create a github.com/rkz91/homebrew-coco repo
#   2. Copy this file to that repo as `Formula/coco.rb`
#   3. Tag a release on rkz91/coco with `v0.1.0`
#   4. Update sha256 below to match the release tarball
#   5. Users install via: `brew install rkz91/coco/coco`
#
# Distribution path B — homebrew-core (later, requires popularity threshold):
#   - Submit this formula to https://github.com/Homebrew/homebrew-core
#   - Users install via: `brew install coco`

class Coco < Formula
  desc "Open-source AI workflow framework — skills, agents, commands, multi-agent orchestration"
  homepage "https://github.com/rkz91/coco"
  url "https://github.com/rkz91/coco/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "REPLACE_WITH_RELEASE_SHA256"
  license "MIT"
  version "0.1.0"

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
