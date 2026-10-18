-- 🔗 ehco schema
CREATE TABLE tunnels(id INTEGER PRIMARY KEY, name TEXT UNIQUE, listen TEXT DEFAULT '0.0.0.0:8443', proto TEXT DEFAULT 'tcp', tls INTEGER DEFAULT 0, cert_path TEXT, lb TEXT DEFAULT 'least-conn', created_at DATETIME);
CREATE TABLE upstreams(id INTEGER PRIMARY KEY, tunnel_id INTEGER REFERENCES tunnels(id), addr TEXT, weight INTEGER DEFAULT 1, healthy INTEGER DEFAULT 1, last_check DATETIME);
CREATE TABLE stats(id INTEGER PRIMARY KEY, tunnel_id INTEGER REFERENCES tunnels(id), bytes INTEGER DEFAULT 0, at DATETIME);
