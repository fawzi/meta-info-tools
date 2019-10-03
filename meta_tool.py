import os
from meta_info import MetaInfo, MetaDictionary, writeFile
import logging
import shutil

defaultBasePath=os.path.realpath(os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__),'../meta_info'))))

def cascade(explodedDir, dictionaryDir, deleteOldBk=False):
	"""Reformats and propagate from exploded to single file dictionaries"""
	explodedDone=set()
	dictDone=set()
	if deleteOldBk:
		dirToClean = []
		if explodedDir:
			dirToClean.append(explodedDir)
		if dictionaryDir:
			dirToClean.append(dictionaryDir)
		for dir in dirToClean:
			for dFile in os.listdir(dir):
				dPath=os.path.join(dir, dFile)
				if os.path.isdir(dPath):
					if dFile.endswith('.bk'):
						try:
							shutils.rmtree(dPath)
						except:
							logging.exception(f"error cleaning up {dPath}")
					else:
						for dFile2 in os.listdir(dPath):
							if dFile2.endswith('.bk'):
								dPath2=os.path.join(dPath, dFile2)
								try:
									os.remove(dPath2)
								except:
									logging.exception(f"error cleaning up {dPath2}")
				elif dFile.endswith('.bk'):
					try:
						os.remove(dPath)
					except:
						logging.exception(f"error cleaning up {dPath}")
	if explodedDir:
		for dFile in os.listdir(explodedDir):
			try:
				if not dFile.endswith('.meta_dictionary'):
					logging.warn(f"Ignoring unknown entry {dFile}")
				else:
					dPath=os.path.join(explodedDir,dFile)
					d=MetaDictionary.loadAtPath(dPath)
					d.standardize()
					d.writeExploded(explodedDir)
					if d.metadict_name + '.meta_dictionary'!= dFile:
						safeRemove([dPath])
					explodedDone.add(d.metadict_name)
				if dictionaryDir:
					dPath=os.path.join(dictionaryDir,d.metadict_name + '.meta_dictionary.json')
					writeFile(dPath, lambda f: d.write(f))
					dictDone.add(d.metadict_name)
			except:
				logging.exception(f'Error handling {dFile}')
	if dictionaryDir:
		for dFile in os.listdir(dictionaryDir):
			try:
				name=dFile[:-len('.meta_dictionary.json')]
				if not dFile.endswith('.meta_dictionary.json'):
					if not dFile.endswith('.bk'):
						logging.warn(f'Ignoring unexpected entry {dFile}')
				elif name not in dictDone:
					dPath = os.path.join(dictionaryDir, dFile)
					d=MetaDictionary.loadAtPath(dPath)
					d.standardize()
					dOutPath=os.path.join(dictionaryDir,d.metadict_name + '.meta_dictionary.json')
					writeFile(dOutPath, lambda f: d.write(f))
					dictDone.add(d.metadict_name)
					if name != d.metadict_name:
						safeRemove([dPath])
			except:
				logging.exception(f'Error handling {dFile}')


def cascadeCmd(args):
	if not args.exploded_directory and not args.dict_directory:
		if not args.base_directory:
			args.base_directory=defaultBasePath
		args.exploded_directory=os.path.join(args.base_directory, "meta_info_exploded")
		args.dict_directory=os.path.join(args.base_directory,"meta_info/meta_dictionary")
	cascade(args.exploded_directory, args.dict_directory, deleteOldBk=args.delete_old_bk)


def rewriteCmd(args):
	for inF in args.inPath:
		try:
			d=MetaDictionary.loadAtPath(inF)
			d.standardize(compact=args.compact)
			if args.target_dir:
				target_dir=args.target_dir
			else:
				target_dir=os.path.dirname(inF)
				if inF.endswith('/') or os.path.basename(inF) == '_.meta_dictionary.json':
					target_dir=os.path.normpath(os.path.join(target_dir,'..'))
			outFormat = args.out_format
			if not outFormat:
				if inF.endswith(".meta_dictionary") or inF.endswith('/') or os.path.basename(inF) == '_.meta_dictionary.json':
					outFormat='exploded'
			else:
				outFormat='single'
			if outFormat=='exploded':
				d.writeExploded(target_dir)
			else:
				writeFile(os.path.join(target_dir, d.metadict_name + '.meta_dictionary.json'), lambda outF: d.write(outF))
		except:
			logging.exception(f'Error rewriting {inF}')


if __name__ == '__main__':
	logging.getLogger().setLevel(logging.INFO)
	import argparse	
	
	# create the top-level parser
	parser = argparse.ArgumentParser(prog='meta_tool')
	subparsers = parser.add_subparsers(help='sub-command help')
	# create the parser for the "cascade" command
	parser_cascade = subparsers.add_parser('cascade', help='reformat and propagate changes from exploded to single file dictionaries')
	parser_cascade.add_argument('--base-directory', type=str,
		help='top directory of the meta info, used to automatically set the the exploded (<base-directory>/meta_info_exploded) and single file (<base-directory>/meta_info/meta_dictionary) dictionaries. If no directories are set this defaults to {defaultBasePath}')
	parser_cascade.add_argument('--exploded-directory', type=str,
		help='path to the exploded directory')
	parser_cascade.add_argument('--dict-directory', type=str,
		help='path to the directory with the .meta_dictionary.json dictionaries')
	parser_cascade.add_argument('--delete-old-bk', action='store_true')
	parser_cascade.set_defaults(func=cascadeCmd)
	# create the parser for the "rewrite" command
	parser_r = subparsers.add_parser('rewrite', help='rewrites a dictionary possibly changing its format')
	parser_r.add_argument('--target-dir', type=str,
		help='target dir if not given defaults to the directory of the first argument (in place)')
	parser_r.add_argument('inPath', type=str, nargs='+',
		help='an input path to convert')
	parser_r.add_argument('--out-format', choices=['exploded', 'single'],
		help='set output format of the dictionary')
	parser_r.add_argument('--compact', action='store_true',
	help='is given stores all descriptions in a single string, not a list of strings.')
	parser_r.set_defaults(func=rewriteCmd)
	args=parser.parse_args(['rewrite', '../meta_info/meta_info/meta_dictionary/common.meta_dictionary.json'])
	args=parser.parse_args(['cascade','--delete-old-bk'])
	args.func(args)

