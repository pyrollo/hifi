CREATE TABLE config(
	key TEXT PRIMARY KEY,
	value TEXT NOT NULL
);

CREATE TABLE files (
	path TEXT PRIMARY KEY,         -- Full path
	size INTEGER NOT NULL,         -- Size in bytes
	hash TEXT,                     -- Computed hash
	last_checked INTEGER NOT NULL, -- Last time file has been checked
	last_inspected INTEGER         -- Last time hash has been computed
);
CREATE INDEX file_hash_ix ON files(hash);
CREATE INDEX file_last_checked_ix ON files(last_checked);
CREATE INDEX file_last_inspected_ix ON files(last_inspected);
