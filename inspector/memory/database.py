"""Artifact Memory Core - SQLite database for AI-generated assets."""
import sqlite3, os, json

DB_PATH = "artifact_memory.db"

def get_path():
    return os.environ.get("ARTIFACT_DB_PATH", os.path.join(os.getcwd(), DB_PATH))

def init():
    db = get_path()
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS artifacts (id INTEGER PRIMARY KEY AUTOINCREMENT, file_hash TEXT UNIQUE, file_path TEXT, file_size INTEGER DEFAULT 0, type TEXT DEFAULT 'image', source TEXT, model TEXT, prompt TEXT, negative TEXT, seed INTEGER DEFAULT -1, steps INTEGER DEFAULT 0, cfg REAL DEFAULT 0.0, sampler TEXT, workflow_json TEXT, artifact_json TEXT, created TEXT, scanned TEXT DEFAULT (datetime('now')))")
    c.execute("CREATE TABLE IF NOT EXISTS artifact_nodes (id INTEGER PRIMARY KEY AUTOINCREMENT, artifact_id INTEGER, node_type TEXT, node_label TEXT)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_source ON artifacts(source)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_model ON artifacts(model)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_prompt ON artifacts(prompt)")
    conn.commit()
    return conn

def save(artifact_result, file_path):
    conn = init()
    c = conn.cursor()
    gen = getattr(artifact_result, 'generation', None)
    source = getattr(artifact_result, 'source_tool', '') or ''
    fsize = getattr(artifact_result, 'file_size', 0)
    wf = getattr(artifact_result, 'workflow_json', '') or ''
    fh = str(hash(file_path))
    if fh.startswith('-'): fh = fh[1:]
    try:
        c.execute("INSERT OR IGNORE INTO artifacts (file_hash, file_path, file_size, source, model, prompt, negative, seed, steps, cfg, sampler, workflow_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (fh, file_path, fsize, source,
             gen.model if gen else '',
             gen.prompt if gen and gen.prompt else '',
             gen.negative_prompt if gen and gen.negative_prompt else '',
             gen.seed if gen else -1,
             gen.steps if gen else 0,
             gen.cfg if gen else 0.0,
             gen.sampler if gen else '',
             wf[:50000] if wf else ''))
        rows = c.execute("SELECT id FROM artifacts WHERE file_hash = ?", (fh,))
        row = rows.fetchone()
        aid = row[0] if row else None
        if aid:
            if wf:
                try:
                    nodes = json.loads(wf)
                    for nid, node in nodes.items():
                        if isinstance(node, dict):
                            ct = node.get("class_type", "Unknown")
                            c.execute("INSERT INTO artifact_nodes (artifact_id, node_type, node_label) VALUES (?,?,?)", (aid, ct, ct[:40]))
                except Exception:
                    pass
            conn.commit()
        conn.close()
        return aid
    except Exception as e:
        conn.close()
        return None

def search(query, limit=20):
    conn = init()
    c = conn.cursor()
    q = '%' + query + '%'
    rows = c.execute("SELECT id, file_path, source, model, prompt, seed, steps, cfg, sampler, scanned FROM artifacts WHERE prompt LIKE ? OR model LIKE ? OR source LIKE ? ORDER BY scanned DESC LIMIT ?", (q, q, q, limit))
    results = []
    for r in rows:
        items = {"id": r[0], "file": os.path.basename(r[1]) if r[1] else '', "path": r[1] or '', "source": r[2] or '', "model": r[3] or '', "prompt": (r[4] or '')[:80], "seed": r[5], "steps": r[6], "cfg": r[7], "sampler": r[8] or '', "scanned": r[9] or ''}
        results.append(items)
    conn.close()
    return results

def list_all(limit=100):
    conn = init()
    c = conn.cursor()
    rows = c.execute("SELECT id, file_path, source, model, prompt, seed, scanned FROM artifacts ORDER BY scanned DESC LIMIT ?", (limit,))
    results = []
    for r in rows:
        results.append({"id": r[0], "file": os.path.basename(r[1]) if r[1] else '', "source": r[2] or '', "model": r[3] or '', "prompt": (r[4] or '')[:60], "seed": r[5], "scanned": r[6] or ''})
    conn.close()
    return results

def get_stats():
    conn = init()
    c = conn.cursor()
    c.execute("SELECT COUNT(*), COUNT(DISTINCT source), COUNT(DISTINCT model) FROM artifacts")
    total, sources, models = c.fetchone()
    conn.close()
    return {"total": total, "sources": sources, "models": models}

def get_by_id(aid):
    conn = init()
    c = conn.cursor()
    rows = c.execute("SELECT id, file_path, source, model, prompt, negative, seed, steps, cfg, sampler, workflow_json, scanned FROM artifacts WHERE id = ?", (aid,))
    for r in rows:
        conn.close()
        return {"id": r[0], "file": r[1], "source": r[2] or '', "model": r[3] or '', "prompt": r[4] or '', "negative": r[5] or '', "seed": r[6], "steps": r[7], "cfg": r[8], "sampler": r[9] or '', "scanned": r[10] or ''}
    conn.close()
    return None
