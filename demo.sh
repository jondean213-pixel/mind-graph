#!/usr/bin/env bash
# MindGraph demo: runs every step by itself, with pauses, so one
# screen recording captures the whole thing (about 1.5 minutes).
# Run from the mind-graph folder:   bash demo.sh
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
P=${PAUSE:-6}

say() { echo; echo "=================================================="; echo ">> $*"; echo "=================================================="; sleep 3; }
run() { echo "\$ python mindgraph.py $*"; $PY mindgraph.py "$@"; sleep "$P"; }

clear
say "MindGraph: an AI agent with a real memory, built on Relate (Neo4j)"
echo "The whole memory lives in ONE file, stored by Relate:"
ls -la data/mindgraph.rl
sleep "$P"

if [ ! -s data/mindgraph.rl ]; then
  say "No memory yet, so load the demo graph"
  run seed
fi

say "1. The whole memory: people, projects, promises, and how they connect"
run graph

say "2. Ask about a person: the agent follows the connections in Cypher"
run recall Grace

say "3. Who works on the project, and since when"
run who MindGraph

say "4. Teach it something new"
run remember person Jon founder
run remember works Jon MindGraph 2026
run remember knows Jon Grace
run remember fact Jon builds AI agents on his phone
run remember promise Jon enter the Relate hackathon --due 2026-12-11

say "5. Recall the new person: everything is already linked"
run recall Jon

say "6. Close and reopen: the memory is still there (persistent single file)"
run recall Jon

say "Not a list of notes. A web of connections. That is MindGraph."
sleep 5
