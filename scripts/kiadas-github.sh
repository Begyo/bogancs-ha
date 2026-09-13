#!/usr/bin/env bash
# GitHub kiadasok (Releases) letrehozasa a meglevo vX.Y.Z cimkekbol, a CHANGELOG.md-bol vett
# szoveggel. Ezt a HACS olvassa: kiadas nelkul a frissitesi kartyan COMMIT-AZONOSITO latszik
# (pl. "dc7f005 -> 66e64cf"), kiadassal a verzioszam es a "kiadasi megjegyzesek" hivatkozas.
#
# Hasznalat (a .241-en, /docker/bogancs-ha):
#   ./scripts/kiadas-github.sh            # minden cimkehez letrehozza/frissiti a kiadast
#   ./scripts/kiadas-github.sh v1.2.1     # csak egyhez
#
# Token: /root/.config/github-token (600), fine-grained PAT a Begyo/bogancs-ha repora,
# "Contents: Read and write" joggal. Cimke pusholasahoz NEM kell, csak a kiadasokhoz.
set -uo pipefail

REPO_SLUG="Begyo/bogancs-ha"
TOKEN_F="${GITHUB_TOKEN_FILE:-/root/.config/github-token}"
CHANGELOG="$(cd "$(dirname "$0")/.." && pwd)/CHANGELOG.md"

if [ ! -r "$TOKEN_F" ]; then
  echo "HIANYZIK a token: $TOKEN_F" >&2
  echo "Fine-grained PAT kell, csak a $REPO_SLUG repora, Contents: Read and write." >&2
  exit 2
fi
TOKEN="$(tr -d ' \n' < "$TOKEN_F")"
[ -f "$CHANGELOG" ] || { echo "Nincs CHANGELOG.md: $CHANGELOG" >&2; exit 2; }

api() { # api <method> <path> [body]
  local m="$1" p="$2" b="${3:-}"
  if [ -n "$b" ]; then
    curl -sS -m 20 -X "$m" -H "Authorization: Bearer $TOKEN" \
      -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
      -d "$b" "https://api.github.com/repos/$REPO_SLUG$p"
  else
    curl -sS -m 20 -X "$m" -H "Authorization: Bearer $TOKEN" \
      -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/$REPO_SLUG$p"
  fi
}

# A CHANGELOG "## vX.Y.Z (datum)" szakaszat adja vissza, a fejlec-sor nelkul.
szakasz() {
  python3 - "$CHANGELOG" "$1" <<'PY'
import re, sys
szoveg = open(sys.argv[1], encoding="utf-8").read()
cimke = sys.argv[2]
m = re.search(r"^## %s\b.*?$(.*?)(?=^## |\Z)" % re.escape(cimke), szoveg, re.M | re.S)
print((m.group(1).strip() if m else "").strip())
PY
}

CIMKEK=("$@")
if [ ${#CIMKEK[@]} -eq 0 ]; then
  mapfile -t CIMKEK < <(git tag -l 'v*' --sort=v:refname)
fi

for t in "${CIMKEK[@]}"; do
  body="$(szakasz "$t")"
  if [ -z "$body" ]; then
    echo "$t: NINCS szakasz a CHANGELOG.md-ben, kihagyva (a kiadas szoveg nelkul ertelmetlen)"
    continue
  fi
  letezo="$(api GET "/releases/tags/$t" | python3 -c 'import json,sys
d=json.load(sys.stdin); print(d.get("id",""))' 2>/dev/null)"
  payload="$(python3 - "$t" "$body" <<'PY'
import json, sys
print(json.dumps({"tag_name": sys.argv[1], "name": sys.argv[1], "body": sys.argv[2],
                  "draft": False, "prerelease": False}))
PY
)"
  if [ -n "$letezo" ]; then
    valasz="$(api PATCH "/releases/$letezo" "$payload")"
    muvelet="frissitve"
  else
    valasz="$(api POST "/releases" "$payload")"
    muvelet="letrehozva"
  fi
  url="$(echo "$valasz" | python3 -c 'import json,sys
d=json.load(sys.stdin); print(d.get("html_url") or ("HIBA: " + str(d.get("message"))))' 2>/dev/null)"
  echo "$t: $muvelet -> $url"
done
