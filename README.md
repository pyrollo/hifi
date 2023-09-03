# HIFI - Hash Indexed File Inventory

HIFI maintains a hash indexed file inventory in a local database.

This database can be used to compare volumes or directory either to perform backups or cleanups.

## Usage

### Get information

```
> ./hifi.py info database
/home/XXXX/.config/hifi/hifi.db: 2221389 files (1044295680 bytes) indexed.
```
Displays information about database: path of database file, number and total size of indexed files.

```
./hifi.py info path /path/to/get/information/from
/path/to/get/information/from: 37 files (17839733 bytes) indexed.
```
Displays information about indexed files in a given path. This will not trigger file indexation if path was not indexed yet.

### Scan path

Most of Hifi commands trigger path indexation but it can also be triggered manually:
```
./hifi.py scan /path/to/scan
```
This will recursively index all files in given path. Indexing includes computing hash, which could take some time.

### Examine path

Here is the interresting part. A little warning, all find commands start with a path scan. If a path has not been indexed yet, first run may take time (depending on the amount of data it contains).

Hifi's aim is to help tidy up files. It can compare two path:

```
./hifi.py find common /path/1 /path/2
```
This will display files (regarding to their hash and size, not their name) that can be found under both path.

Using this command on the same path detects duplicate files:
```
./hifi.py find common /path/to/search /path/to/search
```

Another usefull query:
```
./hifi.py find unique /path/to/search
```
This will print files unknown in database (of course, file may not be known to the database if it is on a non indexed part of the filesystem). It can help identify files to save from the given path.

## Files

Database is stored at `~/.config/hifi/hifi.db`. It is a sqlite3 database. Files indexed once are kept in database as long as they exist.

## Status

This is a POC. Here are some todos:

* Manage removable medias;
* Manage watched path (with background indexation);
* Allow some path to be stat only (no hash, use only stat from files);
* Forced rescans (recompute hash even if file has not changed);
* Improve code;
* Find a proper development language once POC is ok;
* Think about how this can be involved in a sync software;

