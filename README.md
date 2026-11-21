# MindGraph

**An AI agent with a real memory.**

Most agents keep notes. Notes are a list. A mind doesn't work like a list — it works like a web. This person connects to that place, that place connects to this job, this job connects to that promise. MindGraph gives an agent a memory that works the way a mind does: a graph of people, projects, facts, and promises, all connected to each other. Ask it about someone and it doesn't search for a keyword — it follows the connections and tells you what it knows, and how it all fits together.

Built with [Relate](https://relatedb.ai) (Neo4j) for the Relate by Neo4j Hackathon.

## How it uses Relate

MindGraph runs Relate as an embedded graph database, right inside the Python process. There is no server to start and no signup. The agent talks to the graph in Cypher through the `relate-db` Python client (`import relate`).

**Mode: single file.** The whole memory lives in one file: `data/mindgraph.rl`. That file is the persistent store — it is in this repo so judges can inspect it, and it is also what the demo shows.

**Why single file:** a memory that disappears when the app stops is not a memory. A single file keeps the whole graph persistent and portable — one file to back up, one file to carry to another device. It fits a personal agent memory that has to survive restarts without a server. In-memory would forget everything on close, and a directory is extra moving parts for no benefit here.

**What the agent stores:**

| Node | What it holds |
|---|---|
| `Person` | A person, with a name and a role |
| `Project` | A project, with a name |
| `Fact` | A fact, as plain text |
| `Promise` | A promise, as plain text, with a due date |

| Relationship | Meaning |
|---|---|
| `KNOWS` | One person knows another |
| `WORKS_ON` | A person works on a project (with a `since` year) |
| `MAINTAINS` | A person maintains a project |
| `ABOUT` | A fact attached to a person |
| `PROMISED` | A promise someone made (with a `due` date) |

**How recall works:** when you ask about a name, the agent runs one Cypher query that matches that node and every relationship attached to it, in either direction, and prints each connection with its properties (the year someone started, the date a promise is due). That is the graph reasoning — it follows connections instead of matching keywords.

## Run it

Requires Python 3.9 or later.

```bash
pip install -r requirements.txt
python mindgraph.py seed      # load the demo graph
python mindgraph.py graph     # see the whole memory
python mindgraph.py recall Grace
python mindgraph.py who MindGraph
```

The first run creates `data/mindgraph.rl` if it is not there. Close the program, reopen it, and the memory is still there.

## Commands

```bash
python mindgraph.py seed
    Load the demo graph (a small team, a project, a promise).

python mindgraph.py remember person <name> [role]
    Add a person. Example: remember person Ada engineer

python mindgraph.py remember works <person> <project> [since]
    Record that someone works on a project.
    Example: remember works Ada MindGraph 2026

python mindgraph.py remember knows <person> <person>
    Record that one person knows another.
    Example: remember knows Ada Grace

python mindgraph.py remember fact <person> <fact...>
    Attach a fact to a person.
    Example: remember fact Ada prefers morning meetings

python mindgraph.py remember promise <person> <promise...> [--due DATE]
    Record a promise someone made.
    Example: remember promise Grace ship the demo --due 2026-12-01

python mindgraph.py recall <name>
    Show everything the graph knows about a person, project, or
    topic — every node connected to it, and how it connects.

python mindgraph.py who <project>
    Who works on a project, and since when.

python mindgraph.py graph
    List every node and every relationship in the memory.
```

## Try it

```bash
python mindgraph.py seed
python mindgraph.py graph
python mindgraph.py recall Grace
```

You will see Grace's whole picture: she works on MindGraph since 2026, she knows Ada and Noor, and she promised to ship the demo by 2026-12-01. That is the memory working — not a list of notes, but a web of connections.

## What's next

MindGraph is the memory layer for the brains I'm already building. Once it's proven here, it goes into Gemma, my assistant, so she doesn't just remember what I told her — she remembers how it all connects.
