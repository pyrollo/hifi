# TODOS: Database should be locked for update operations (scan)

import sqlite3
import os.path
import hashlib

def createIndex(db_file_path, hash_method):
	if os.path.isfile(db_file_path):
		raise Exception("Index file " + db_file_path + " already exists!")

	print("Creating new database file: " + db_file_path)
	db = sqlite3.connect(db_file_path)
	cur = db.cursor()
	script = open('structure.sql', mode='r')
	cur.executescript(script.read())
	script.close()	
	cur.execute("INSERT INTO config VALUES('HASHMETHOD', ?)", (hash_method, ))
	db.commit()

class Index:
	def __init__(self, db_file_path):
		if not os.path.isfile(db_file_path):
			raise Exception("Index file " + db_file_path + " not found!")
		self.db = sqlite3.connect(db_file_path, isolation_level=None)
		row = self.db.execute("SELECT value FROM config WHERE key='HASHMETHOD'").fetchone()
		if row is None:
			raise Exception("Bad configuration in database!")
		(self.hashmethod, ) = row

	def getHash(self, path):
		with open(path, "rb") as f:
			hash = hashlib.file_digest(f, self.hashmethod)
		return hash.hexdigest()

	def addRoot(self, path):
		path = path.encode(encoding='utf-8') # all path in database are bytes, not strings
		# Missing: check path exists?
		id = self._getOrCreateDirectory(path)
		row = self.db.execute("SELECT 1 FROM root WHERE directory_id=?", (id,)).fetchone()
		if row is None:
			self.db.execute("INSERT INTO root VALUES(?)", (id, ))
			self._check()
		else:
			print(path.decode('utf8','replace') + " already a root path")

	def getRoots(self):
		result = []
		for row in self.db.execute("SELECT d.path FROM root r, directory d WHERE r.directory_id=d.id"):
			(path, ) = row
			result.append(path.decode('utf8','replace'))
		return result

	def _getOrCreateDirectory(self, path):
		row = self.db.execute("SELECT id FROM directory WHERE path=?", (path,)).fetchone()
		if row is None:
			row = self.db.execute("INSERT INTO directory(path) values (?) RETURNING id", (path, )).fetchone()
		(id, ) = row
		return id

	def recheck(self):
		self.db.execute("UPDATE directory SET checked = FALSE")
		self._check()

	def _check(self):
		# Remove not existing anymore
		for row in self.db.execute("SELECT id, path FROM directory"):
			(id, path) = row
			if not os.path.isdir(path):
				print("REMOVED DIR: " + path.decode('utf8', 'remplace') + " does not exist anymore")
				self.db.execute("DELETE FROM directory WHERE id = ?", (id, ));

		for row in self.db.execute('SELECT d.id, f.name, d.path FROM file f, directory d WHERE f.directory_id = d.id'):
			(id, name, path) = row
			if not os.path.isfile(os.path.join(path, name)):
				print("REMOVED FILE: " + os.path.join(path, name).decode('utf8', 'remplace') + " does not exist anymore")
				self.db.execute("DELETE FROM file WHERE directory_id = ? AND name = ?", (id, name))
		
		# Add missing stuff
		remaining = True
		while remaining:
			remaining = False
			for row in self.db.execute("SELECT id, path FROM directory WHERE checked = FALSE"):
				(directory_id, path) = row

				indexed_files = {}
				for row in self.db.execute("SELECT name, last_modified FROM file WHERE directory_id=?", (directory_id,)):
					indexed_files[row[0]] = row[1]

				# Check subdirs and files at once
				for entry in os.scandir(path):
					if entry.is_dir():
						if not self.db.execute(
								"INSERT INTO directory(path) VALUES (?) ON CONFLICT DO NOTHING RETURNING id", 
								(os.path.join(path, entry.name),)).fetchone() is None:
							print("ADDED DIR " + entry.name.decode('utf8','replace'))
							remaining = True
					if entry.is_file():
						if entry.name in indexed_files:
							if entry.stat().st_mtime > indexed_files[entry.name]:
								print("UPDATED FILE " + entry.name.decode('utf8','replace'))
								self.db.execute("UPDATE file SET last_modified=?, size=?, hash=? where directory_id = ? and name = ?",
									(entry.stat().st_mtime, entry.stat().st_size, self.getHash(os.path.join(basePath, entry.name)), directory_id, entry.name, ));
						else:
							print("ADDED FILE " + entry.name.decode('utf8','replace'))
							self.db.execute("INSERT INTO file(directory_id, name, last_modified, size, hash) values (?, ?, ?, ?, ?)",
								(directory_id, entry.name, entry.stat().st_mtime, entry.stat().st_size, self.getHash(os.path.join(path, entry.name)), ));

				# Mark this directory as checked
				self.db.execute("UPDATE directory SET checked = TRUE WHERE id = ?", (row[0], ));
				
	def printDuplicates(self):
		self._check()
		old_size = -1
		old_hash = ""
		for row in self.db.execute("""
			SELECT f.size, f.hash, d.path, f.name
			  FROM file f, directory d
			 WHERE f.directory_id = d.id
		       AND EXISTS(
				SELECT 1 FROM file f2
				 WHERE f2.hash = f.hash AND f2.size = f.size
				   AND (f2.directory_id <> f.directory_id OR f2.name <> f.name))
			  ORDER BY hash, size"""):
			(size, hash, path, name) = row
			if old_size != size or old_hash != hash:
				print(hash + " (" + str(size) + " bytes):")
				old_size = size
				old_hash = hash
			print("  " + os.path.join(path, name).decode('utf8','replace'))

	def findSameFile(self, file_path):
		self._check()
		if not os.path.isfile(file_path):
			print(file_path + " is not a file")
			return
		size = os.stat(file_path).st_size
		hash = self.getHash(file_path)
		for row in self.db.execute(
				"SELECT d.path, f.name FROM file f, directory d WHERE f.directory_id = d.id AND f.size = ? AND f.hash = ?",
				(size, hash, )):
			print(os.path.join(row[0], row[1]))


