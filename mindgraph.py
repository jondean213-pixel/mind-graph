#!/usr/bin/env python3
"""MindGraph — an AI agent with a real memory.

The agent stores what it learns as a graph, not a list: people, projects,
facts, and promises, all connected to each other. It remembers by writing
to a Relate graph, and it recalls by following the connections — who knows
who, who works on what, what depends on what — and reasoning over them.

The memory lives in one file: data/mindgraph.rl (a Relate single-file
store). Close the program, reopen it, and the memory is still there.
That is the whole point: a memory that survives a restart.

Usage:
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

    python mindgraph.py help
        Show this help.

Requires: pip install relate-db
"""

import os
import sys

import relate

STORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "data", "mindgraph.rl")


def connect():
    """Open the memory store, creating it (and its folder) if needed."""
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    return relate.connect(STORE_PATH)


def seed(conn):
    """Load the demo graph: a small team, a project, a promise."""
    conn.execute("""
        CREATE (ada:Person {name: 'Ada', role: 'engineer'}),
               (grace:Person {name: 'Grace', role: 'engineer'}),
               (noor:Person {name: 'Noor', role: 'maintainer'}),
               (mindgraph:Project {name: 'MindGraph'}),
               (ada)-[:WORKS_ON {since: 2026}]->(mindgraph),
               (grace)-[:WORKS_ON {since: 2026}]->(mindgraph),
               (noor)-[:MAINTAINS]->(mindgraph),
               (ada)-[:KNOWS]->(grace),
               (grace)-[:KNOWS]->(noor),
               (grace)-[:PROMISED {due: '2026-12-01'}]->
                   (:Promise {text: 'ship the demo'})
    """)
    print("Seeded the demo graph: 3 people, 1 project, 1 promise.")


def remember_person(conn, name, role=""):
    conn.execute(
        "MERGE (p:Person {name: $name}) "
        "ON CREATE SET p.role = $role "
        "ON MATCH SET p.role = $role",
        {"name": name, "role": role},
    )
    print(f"Remembered {name}" + (f" ({role})" if role else "") + ".")


def remember_works(conn, person, project, since=None):
    conn.execute(
        "MERGE (p:Person {name: $person}) "
        "MERGE (j:Project {name: $project}) "
        "MERGE (p)-[w:WORKS_ON]->(j) "
        "SET w.since = $since",
        {"person": person, "project": project, "since": since},
    )
    line = f"Remembered: {person} works on {project}"
    if since:
        line += f" since {since}"
    print(line + ".")


def remember_knows(conn, person, other):
    conn.execute(
        "MERGE (a:Person {name: $a}) "
        "MERGE (b:Person {name: $b}) "
        "MERGE (a)-[:KNOWS]->(b)",
        {"a": person, "b": other},
    )
    print(f"Remembered: {person} knows {other}.")


def remember_fact(conn, person, fact):
    conn.execute(
        "MERGE (p:Person {name: $person}) "
        "CREATE (f:Fact {text: $fact}) "
        "MERGE (p)-[:ABOUT]->(f)",
        {"person": person, "fact": fact},
    )
    print(f"Remembered a fact about {person}: {fact}")


def remember_promise(conn, person, promise, due=None):
    conn.execute(
        "MERGE (p:Person {name: $person}) "
        "CREATE (pr:Promise {text: $promise, due: $due}) "
        "MERGE (p)-[:PROMISED {due: $due}]->(pr)",
        {"person": person, "promise": promise, "due": due},
    )
    line = f"Remembered: {person} promised: {promise}"
    if due:
        line += f" (due {due})"
    print(line + ".")


def recall(conn, name):
    """Show everything connected to a name, and how it connects."""
    rows = list(conn.execute(
        "MATCH (n)-[r]-(m) "
        "WHERE n.name = $name "
        "RETURN labels(n) AS from_labels, n.name AS from_name, "
        "       type(r) AS rel, properties(r) AS rel_props, "
        "       labels(m) AS to_labels, "
        "       coalesce(m.name, m.text) AS to_name "
        "ORDER BY rel, to_name",
        {"name": name},
    ))
    if not rows:
        # Maybe it is a fact or promise text, not a name.
        rows = list(conn.execute(
            "MATCH (n) WHERE n.text CONTAINS $name "
            "RETURN labels(n) AS from_labels, n.text AS from_name, "
            "       '' AS rel, {} AS rel_props, [] AS to_labels, "
            "       '' AS to_name",
            {"name": name},
        ))
    if not rows:
        print(f"Nothing in memory about '{name}' yet.")
        return
    print(f"Memory for '{name}':")
    for row in rows:
        rel = row["rel"]
        if rel:
            props = row["rel_props"] or {}
            extra = ""
            if props.get("since"):
                extra = f" (since {props['since']})"
            elif props.get("due"):
                extra = f" (due {props['due']})"
            print(f"  - {rel} -> {row['to_name']}{extra}")
        else:
            print(f"  - {row['from_name']}")


def who(conn, project):
    rows = list(conn.execute(
        "MATCH (p:Person)-[w:WORKS_ON]->(:Project {name: $project}) "
        "RETURN p.name AS name, p.role AS role, w.since AS since "
        "ORDER BY since",
        {"project": project},
    ))
    if not rows:
        print(f"No one recorded as working on '{project}' yet.")
        return
    print(f"Who works on {project}:")
    for row in rows:
        line = f"  - {row['name']}"
        if row["role"]:
            line += f" ({row['role']})"
        if row["since"]:
            line += f" since {row['since']}"
        print(line)


def show_graph(conn):
    nodes = list(conn.execute(
        "MATCH (n) RETURN labels(n) AS labels, "
        "coalesce(n.name, n.text) AS name ORDER BY labels, name"
    ))
    rels = list(conn.execute(
        "MATCH (a)-[r]->(b) "
        "RETURN coalesce(a.name, a.text) AS a, type(r) AS rel, "
        "coalesce(b.name, b.text) AS b ORDER BY a, rel, b"
    ))
    print(f"Memory graph: {len(nodes)} nodes, {len(rels)} relationships.")
    print("Nodes:")
    for row in nodes:
        print(f"  - [{', '.join(row['labels'])}] {row['name']}")
    print("Relationships:")
    for row in rels:
        print(f"  - {row['a']} -{row['rel']}-> {row['b']}")


def main(argv):
    if len(argv) < 2 or argv[1] in ("help", "-h", "--help"):
        print(__doc__)
        return 0

    cmd = argv[1]
    conn = connect()
    try:
        if cmd == "seed":
            seed(conn)
        elif cmd == "remember" and len(argv) >= 4 and argv[2] == "person":
            remember_person(conn, argv[3], argv[4] if len(argv) > 4 else "")
        elif cmd == "remember" and len(argv) >= 5 and argv[2] == "works":
            remember_works(conn, argv[3], argv[4],
                           argv[5] if len(argv) > 5 else None)
        elif cmd == "remember" and len(argv) >= 5 and argv[2] == "knows":
            remember_knows(conn, argv[3], argv[4])
        elif cmd == "remember" and len(argv) >= 5 and argv[2] == "fact":
            remember_fact(conn, argv[3], " ".join(argv[4:]))
        elif cmd == "remember" and len(argv) >= 5 and argv[2] == "promise":
            rest = argv[4:]
            due = None
            if "--due" in rest:
                i = rest.index("--due")
                due = rest[i + 1] if i + 1 < len(rest) else None
                rest = rest[:i]
            remember_promise(conn, argv[3], " ".join(rest), due)
        elif cmd == "recall" and len(argv) >= 3:
            recall(conn, " ".join(argv[2:]))
        elif cmd == "who" and len(argv) >= 3:
            who(conn, " ".join(argv[2:]))
        elif cmd == "graph":
            show_graph(conn)
        else:
            print(f"Unknown command: {' '.join(argv[1:])}\n")
            print(__doc__)
            return 2
        return 0
    except relate.Error as e:
        print(f"Relate error ({type(e).__name__}): {e}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
