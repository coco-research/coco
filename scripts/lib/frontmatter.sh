#!/usr/bin/env bash
# frontmatter_name FILE
# Print the first `name` value between the opening `---` line and the next
# `---`, or nothing. The opening fence must be line 1; a later fence is body
# text and the caller falls back to the directory name. Spaces or tabs may
# follow the colon. A trailing CR is removed, then trailing spaces and tabs,
# then one matching pair of surrounding quotes. A `name:` line outside that
# block is ignored. Sourced by the installers.

frontmatter_name() {
  local file=$1 line in_fm=0 value first=1
  [[ -f "$file" ]] || return 0
  while IFS= read -r line || [[ -n "${line:-}" ]]; do
    line=${line%$'\r'}
    if [[ "$first" -eq 1 ]]; then
      first=0
      [[ "$line" == "---" ]] || return 0
    fi
    if [[ "$line" == "---" ]]; then
      if [[ "$in_fm" -eq 1 ]]; then
        return 0
      fi
      in_fm=1
      continue
    fi
    [[ "$in_fm" -eq 1 ]] || continue
    [[ "$line" == name:* ]] || continue
    value=${line#name:}
    value=${value#"${value%%[![:space:]]*}"}
    value=${value%"${value##*[![:blank:]]}"}
    case "$value" in
      \"*\") value=${value#\"}; value=${value%\"} ;;
      \'*\') value=${value#\'}; value=${value%\'} ;;
    esac
    # A name is one path component under the user's skills directory, so anything else is ignored.
    if [[ "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] && [[ "$value" != *..* ]]; then
      printf '%s\n' "$value"
    fi
    return 0
  done <"$file"
}
