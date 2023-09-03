CREATE TABLE path (
	id INTEGER PRIMARY KEY,
	parent_id INTEGER,
	name VARCHAR(500) NOT NULL,
	FOREIGN KEY(parent_id) REFERENCES path(id) ON DELETE CASCADE
);
CREATE TABLE file (
	parent_id INTEGER NOT NULL,
	name VARCHAR(500) NOT NULL,
	last_modified INTEGER NOT NULL,
	size INTEGER NOT NULL,
	md5sum CHAR(32) NOT NULL,
	PRIMARY KEY(parent_id, name),
	FOREIGN KEY(parent_id) REFERENCES path(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS file_md5sum_ix ON file(md5sum);

CREATE VIEW IF NOT EXISTS fullpath AS
WITH RECURSIVE fpath(id, name) AS (
	SELECT id, name FROM path WHERE parent_id IS NULL
	UNION ALL
	SELECT path.id, fpath.name || '/' || path.name
	  FROM path, fpath WHERE path.parent_id = fpath.id
) SELECT * FROM fpath;
