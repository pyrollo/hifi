#!/usr/bin/python3

import os
import argparse
import pathlib

import index

def getIndex():
	configdir = os.path.join(os.environ['HOME'], ".config", "hifi")
	configdb = os.path.join(configdir, "hifi.db")

	os.makedirs(configdir, exist_ok=True)
	if not os.path.isfile(configdb):
		index.createIndex(configdb, "md5")

	return index.Index(configdb)

def realPath(path):
	try:
		return os.path.realpath(path, strict=True)
	except FileNotFoundError:
		print("Path not found: %s" % path)
		exit(1)

main_parser = argparse.ArgumentParser(
	prog='hifi',
	description='Hash indexed file inventory - Indexes files by hash and perform duplicate detection, file search and so on',
	epilog='')

commands = main_parser.add_subparsers(dest='command')

command = commands.add_parser('info', help='Information about database and indexed files')
subcommands = command.add_subparsers(dest="subcommand")
subcommand = subcommands.add_parser('database', help='information about database')
subcommand = subcommands.add_parser('path', help='information about a perticular path')
subcommand.add_argument('path', type=pathlib.Path, help = 'path to get information from')

command = commands.add_parser('scan', help='Scan files')
command.add_argument('path', type=pathlib.Path, help = 'path to scan')

command = commands.add_parser('find', help='Find files (this will scan all given path)')
subcommands = command.add_subparsers(dest="subcommand")
subcommand = subcommands.add_parser('unique', help='find unique files')
subcommand.add_argument('path', type=pathlib.Path, help = 'path to check for unique files')
subcommand = subcommands.add_parser('common', help='find common files')
subcommand.add_argument('path1', type=pathlib.Path, help = 'first path to compare')
subcommand.add_argument('path2', type=pathlib.Path, help = 'second path compare')

args = main_parser.parse_args()

match args.command:
	case 'info':
		match args.subcommand:

			case 'database':
				info = getIndex().databaseInformation()
				print(str(info))

			case 'path':
				info = getIndex().pathInformation(realPath(args.path))
				print(str(info))

	case 'scan':
		getIndex().addPath(realPath(args.path))

	case 'clean':
		getIndex().cleanUp()

	case 'find':
		match args.subcommand:

			case 'unique':
				getIndex().findUnique(realPath(args.path))

			case 'common':
				getIndex().findCommon(realPath(args.path1), realPath(args.path2))

#configdir = os.path.join(os.environ['HOME'], ".config", "hifi")
#configdb = os.path.join(configdir, "hifi.db")

#os.makedirs(configdir, exist_ok=True)
#if not os.path.isfile(configdb):
#	index.createIndex(configdb, "md5")

#d = index.Index(configdb)
#d.addRoot("/home/pyrollo/Documents secondaires/")

#d.printDuplicates()
