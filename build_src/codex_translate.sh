#!/usr/bin/env bash
# Hand off the remaining Vietnamese poems to Codex (gpt-5.5) for translation.
# Resumable: each poem -> build_src/codex_out/<slug>.json; already-done slugs are skipped.
set -uo pipefail
cd /home/nhac/projects/verdantspring.github.io
OUTDIR=build_src/codex_out
mkdir -p "$OUTDIR"

mapfile -t ALL < <(python3 -c 'import json;[print(s) for s in json.load(open("build_src/codex_todo.json"))]')

# filter to remaining
TODO=()
for s in "${ALL[@]}"; do
  [ -s "$OUTDIR/$s.json" ] || TODO+=("$s")
done
echo "[codex] total ${#ALL[@]} | remaining ${#TODO[@]}"

BATCH=3
for ((i=0; i<${#TODO[@]}; i+=BATCH)); do
  CHUNK=("${TODO[@]:i:BATCH}")
  list=$(printf '  - %s\n' "${CHUNK[@]}")
  echo "[codex] batch $((i/BATCH+1)): ${CHUNK[*]}"
  prompt="You are translating the poetry of Hoàng-Ân, a Vietnamese poet of the diaspora (refugee, exile, Houston/USA), whose voice is lyrical, mystical, and syncretic (Biblical + Buddhist imagery braided together).

FIRST read build_src/swarm/_VOICE.txt — these are the poet's OWN English poems. Absorb her voice (cadence, diction, capitalized abstractions, em-dashes, ellipses) so your translations sound like HER, not generic translationese.

Then, for EACH of these slugs:
$list
do the following:
  1. Read build_src/swarm/<slug>.vn.txt (the Vietnamese poem).
  2. Translate it into genuine English poetry in her voice — faithful to the imagery FIRST, musical where English allows. Preserve stanza and line breaks exactly. Keep proper nouns, place names, dates, parenthetical datelines. Keep untranslatable lullaby/ritual sounds (e.g. 'À ơi', 'nam-mô') as-is. Do not add or drop lines.
  3. Write the result to build_src/codex_out/<slug>.json as compact JSON with EXACTLY these keys: {\"slug\": \"<slug>\", \"en_title\": \"...\", \"en_body\": \"...full translation with \\n line breaks...\", \"note\": \"one sentence on any allusion, or empty string\"}.

Write all ${#CHUNK[@]} files. Do not ask questions. Do not print the poems to stdout. When done, reply only: BATCH DONE."

  timeout 900 codex exec --ignore-user-config -s danger-full-access --skip-git-repo-check \
    -c approval_policy="never" "$prompt" >/dev/null 2>>build_src/codex_out/_errors.log
  done_n=$(ls "$OUTDIR"/*.json 2>/dev/null | grep -v _ | wc -l)
  echo "[codex] progress: $done_n / ${#ALL[@]} written"
done
echo "[codex] ALL BATCHES COMPLETE"
