#!/usr/bin/python3

import sqlite3
import os.path
import hashlib

def getDigest(path):
	with open(path, "rb") as f:
		digest = hashlib.file_digest(f, "md5")
	return digest.hexdigest()

class Database:
	def __init__(self, dbfile):
		self.dbfile = dbfile
		if os.path.isfile(dbfile):
			self.db = sqlite3.connect(self.dbfile)
			return

		print("Creating new database file: " + self.dbfile)
		self.db = sqlite3.connect(self.dbfile)
		cur = self.db.cursor()
		script = open('structure.sql', mode='r')
		cur.executescript(script.read())
		script.close()

	def addRoot(self, rootPath):
		cur = self.db.cursor()
		res = cur.execute("SELECT 1 FROM path WHERE parent_id IS NULL AND name=?", (rootPath,))
		if not res.fetchone() is None:
			print("Root " + rootPath.decode('utf8','replace') + " already indexed")
			return
		self._checkPath(rootPath, self._addPath(None, rootPath))
		self.db.commit()
	
	def checkRoot(self, rootPath):
		cur = self.db.cursor()
		res = cur.execute("SELECT id FROM path WHERE parent_id IS NULL AND name=?", (rootPath,))
		row = res.fetchone()
		if row is None:
			print("Unknown root " + rootPath.decode('utf8','replace'))
			return
		self._checkPath(rootPath, row[0])
		self.db.commit()

	def _addPath(self, parentId, name):
		cur = self.db.cursor()
		cur.execute("INSERT INTO path(parent_id, name) values (?, ?) RETURNING id", (parentId, name,))
		row = cur.fetchone()
		(id, ) = row if row else None
		return id

	def _checkPath(self, basePath, parentId):
		cur = self.db.cursor()
		print("Checking " + basePath.decode('utf8','replace'))
		# Fetch existing stuff
		files = {}
		dirs = {}
		for row in cur.execute("SELECT name, last_modified FROM file WHERE parent_id=?", (parentId,)):
			files[row[0]] = row[1]
		for row in cur.execute("SELECT name, id FROM path WHERE parent_id=?", (parentId,)):
			dirs[row[0]] = row[1]

		# Check for missing
		for entry in os.scandir(basePath):
			
			if entry.is_dir() and not entry.name in dirs:
				print("New dir: " + entry.name.decode('utf8','replace'))
				self._addPath(parentId, entry.name)

			if entry.is_file():
				if entry.name in files:
					if entry.stat().st_mtime > files[entry.name]:
						print("Modified: " + entry.name.decode('utf8','replace'))
						cur = self.db.cursor()
						cur.execute("UPDATE file SET last_modified=?, size=?, md5sum=? where parent_id = ? and name = ?",
							(entry.stat().st_mtime, entry.stat().st_size, getDigest(os.path.join(basePath, entry.name)), parentId, entry.name, ));
				else:
					print("New file: " + entry.name.decode('utf8','replace'))
					cur = self.db.cursor()
					cur.execute("INSERT INTO file(parent_id, name, last_modified, size, md5sum) values (?, ?, ?, ?, ?)",
						(parentId, entry.name, entry.stat().st_mtime, entry.stat().st_size, getDigest(os.path.join(basePath, entry.name)), ));

		# Check for extra
		for row in cur.execute("SELECT name FROM file WHERE parent_id=?", (parentId,)):
			if not os.path.isfile(os.path.join(basePath, row[0])):
				self.db.cursor().execute("DELETE FROM file WHERE parent_id=? AND name=?", (parentId, row[0],))
		
		for row in cur.execute("SELECT name, id FROM path WHERE parent_id=?", (parentId,)):
			childPath = os.path.join(basePath, row[0])
			if os.path.isdir(childPath):
				self._checkPath(childPath, row[1])
			else:
				self.db.cursor().execute("DELETE FROM path WHERE id=?", (row[1],))

	def fullPath(self, pathId):
		cur = self.db.cursor()
		res = cur.execute("SELECT name FROM fullpath WHERE id=?", (pathId,))
		row = cur.fetchone()
		(path, ) = row if row else None
		return path

	def printDuplicates(self):
		cur = self.db.cursor()
		oldSize = -1
		oldMd5sum = ""
		for row in cur.execute("""
			SELECT size, md5sum, p.name, f.name
			  FROM file f, fullpath p
			 WHERE f.parent_id = p.id
		       AND EXISTS(
				SELECT 1 FROM file f2
				 WHERE f2.md5sum = f.md5sum AND f2.size = f.size
				   AND (f2.parent_id <> f.parent_id OR f2.name <> f.name))
			  ORDER BY md5sum, size"""):
			(size, md5sum, path, name) = row
			if oldSize != size or oldMd5sum != md5sum:
				print(md5sum + " (" + str(size) + " bytes):")
				oldSize = size
				oldMd5sum = md5sum
			print("  " + os.path.join(path, name.decode('utf8','replace')))

	def findSameFile(self, filePath):
		if not os.path.isfile(filePath):
			print(filePath + " is not a file")
			return
		size = os.stat(filePath).st_size
		md5sum = getDigest(filePath)
		cur = self.db.cursor()
		for row in cur.execute(
				"SELECT p.name, f.name FROM file f, fullpath p WHERE f.parent_id = p.id AND f.size = ? AND f.md5sum = ?",
				(size, md5sum, )):
			print(os.path.join(row[0], row[1]))
		
		
		
d = Database("titi.db")
#d.addRoot(b"/home/pyrollo/Archives")
#d.checkRoot(b"/home/pyrollo/Archives")
d.printDuplicates()
#d.findSameFile("/home/pyrollo/dev/Linux tools/md5indexer/.git/refs/remotes/origin/main")

