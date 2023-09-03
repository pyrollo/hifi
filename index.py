# pip install ftfy --break-system-packages

import sqlite3
import os.path
import hashlib
import time

import infos

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
		self.verbose = True
		if not os.path.isfile(db_file_path):
			raise Exception("Index file " + db_file_path + " not found!")
		self.db_file_path = db_file_path
		self.db = sqlite3.connect(db_file_path, isolation_level=None)
		self.db.execute('PRAGMA synchronous=OFF')
		row = self.db.execute("SELECT value FROM config WHERE key='HASHMETHOD'").fetchone()
		if row is None:
			raise Exception("Bad configuration in database!")
		(self.hashmethod, ) = row

	def _info(self, message):
		if self.verbose:
			print(message, flush=True)

	#
	def _hashFiles(self):
		(count, total_size) = self.db.execute("SELECT count(*), sum(size) FROM files WHERE hash IS NULL").fetchone()
		if count == 0:
			return
		done_size = 0
		print("\rHashing %d files (%d bytes)..." % (count, total_size))
		for (path, size,) in self.db.execute("SELECT path, size FROM files WHERE hash IS NULL"):
			with open(path, "rb") as f:
				hash_date = time.time()
				hash_value = hashlib.file_digest(f, self.hashmethod).hexdigest()
			
			self.db.execute("UPDATE files SET hash=?, last_inspected=? WHERE path = ?",
				(hash_value, hash_date, path, ))
			done_size += size
			print("\r\033[2K%d%% %s" % (100 * done_size / total_size, path), end="")

		print("\r\033[2KDone.")

	#
	def _checkFile(self, entry):
		stat_time = time.time()
		stat = entry.stat()

		# TODO: Manage concurrency (DB and file, file can be deleted meanwhile)
		try:
			path = entry.path.encode('utf-8', 'strict').decode('utf-8')
		except UnicodeEncodeError:
			print("IGNORE (encoding) " + entry.path)
			return

		row = self.db.execute("SELECT size, last_checked, last_inspected FROM files WHERE path = ?", (path,)).fetchone()
		if row is None:
			self.db.execute("INSERT INTO files(path, size, last_checked) values (?, ?, ?)",
				(path, stat.st_size, stat_time));
			self._info("ADD " + path)
		else:
			(size, last_checked, last_inspected) = row
			if last_inspected == None or last_inspected < stat.st_mtime or size != stat.st_size: # TODO: OR deepcheck enabled
				# If size changed or file marked as modified, we reinspect it
				self.db.execute("UPDATE files SET size=?, hash=NULL, last_inspected=NULL, last_checked=? WHERE path = ?",
					(stat.st_size, stat_time, path, ))
				self._info("UPDATE " + path)
			else:
				# Fast check
				self.db.execute("UPDATE files SET last_checked=? WHERE path = ?",
					(stat_time, path, ))

	#
	def _checkDirectory(self, path):
		with os.scandir(path) as it:
			for entry in it:
				if entry.is_symlink():
					self._info("IGNORE (link) " + entry.path)
					continue
				if entry.is_dir():
					self._checkDirectory(entry.path)
					continue
				if entry.is_file():
					self._checkFile(entry)
					continue
				self._info("IGNORE (unknown) " + entry.path)
			it.close()

	# TODO: Make a first fast pass on files to determine amount of bytes to hash
	def addPath(self, path):
		self._checkDirectory(os.path.realpath(path))
		self._hashFiles()

	def cleanUp(self):
		for (path,) in self.db.execute("SELECT path FROM files"):
			if not os.path.isfile(path):
				self.db.execute("DELETE FROM files WHERE path = ?", (path,))
				self._info("REMOVE " + path)

	def databaseInformation(self):
		size = os.stat(self.db_file_path).st_size
		(count,) = self.db.execute("SELECT COUNT(*) FROM files").fetchone()
		return infos.DatabaseInformation(self.db_file_path, size, count)

	def pathInformation(self, path):
		path = os.path.realpath(path)
		(size, count) = self.db.execute("SELECT COALESCE(SUM(size), 0), COUNT(*) FROM files WHERE path LIKE ? OR path = ?", (path + "/%", path,)).fetchone()
		return infos.PathInformation(path, size, count)

	def findUnique(self, path):
		path = os.path.realpath(path)

		print("Fast scanning %s..." % (path,), end="", flush=True)
		self.addPath(path)
		print(" done!")	
		print("Cleaning up...", end="", flush=True)
		self.cleanUp()
		print(" done!")

		print("Files only found in %s:" % (path, ), flush=True)
		for (file,) in self.db.execute("""
			SELECT f1.path
			  FROM files f1
			 WHERE (f1.path LIKE ? OR f1.path = ?)
			   AND NOT EXISTS (
				SELECT 1 FROM files f2
				 WHERE f2.hash = f1.hash AND f2.size = f1.size
				   AND f2.path NOT LIKE ? AND f2.path <> ?
			   )
			ORDER BY f1.path
		""", ( path + "/%", path, path + "/%", path )):
			print("%s" % (file))

	def findCommon(self, path1, path2):
		path1 = os.path.realpath(path1)
		path2 = os.path.realpath(path2)

		print("Fast scanning %s..." % (path1,), end="", flush=True)
		self.addPath(path1)
		print(" done!")	
		print("Fast scanning %s..." % (path2,), end="", flush=True)
		self.addPath(path2)
		print(" done!")	
		print("Cleaning up...", end="", flush=True)
		self.cleanUp()
		print(" done!")

		print("Comparing...", end="", flush=True)
		for (file1, file2) in self.db.execute("""
			SELECT f1.path, f2.path
			  FROM files f1, files f2
			 WHERE f1.hash = f2.hash AND f1.size = f2.size
			   AND f1.path LIKE ? and f2.path LIKE ?
			   AND f1.path <> f2.path
			 ORDER BY f1.path
		""", ( path1 + "/%", path2 + "/%" )):
			print("%s => %s" % (file1, file2))
