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

main_parser = argparse.ArgumentParser(
	prog='hifi',
	description='Hash indexed file inventory - Indexes files by hash and perform duplicate detection, file search and so on',
	epilog='')

commands = main_parser.add_subparsers(dest='command')

command = commands.add_parser('root', help='manage and display root indexed directories')
subcommands = command.add_subparsers(dest="subcommand")

subcommand = subcommands.add_parser('add', help='add new root path to index')
subcommand.add_argument('path', type=pathlib.Path,  help = 'path of the directory to be indexed')

subcommand = subcommands.add_parser('list', help='list indexed root directories')

command = commands.add_parser('find', help='find files in inventory')
subcommands = command.add_subparsers(dest="subcommand")

subcommand = subcommands.add_parser('duplicates', help='find duplicates in inventory')

subcommand = subcommands.add_parser('file', help='find files in inventory identical to given one')
subcommand.add_argument('path', type=pathlib.Path,  help = 'path of file to search for identical ones in inventory')

#parser.add_argument('-r', '--roots', action='store_true', help = 'show indexed root directories')
#parser.add_argument('--new-root', action='store', type=pathlib.Path, dest="root_path", help = 'add a new root directory to be indexed')
args = main_parser.parse_args()

match args.command:
	case 'root':
		match args.subcommand:
			case 'list':
				for path in getIndex().getRoots():
					print(path)
			case 'add':
				# TODO : manage exceptions
				path = os.path.realpath(args.path, strict=True)
				getIndex().addRoot(path)
	case 'find':
		match args.subcommand:
			case 'file':
				path = os.path.realpath(args.path, strict=True)
				getIndex().findSameFile(path)
			case 'duplicates':
				getIndex().printDuplicates()
#configdir = os.path.join(os.environ['HOME'], ".config", "hifi")
#configdb = os.path.join(configdir, "hifi.db")

#os.makedirs(configdir, exist_ok=True)
#if not os.path.isfile(configdb):
#	index.createIndex(configdb, "md5")

#d = index.Index(configdb)
#d.addRoot("/home/pyrollo/Documents secondaires/")

#d.printDuplicates()
