import os
from meta_info import MetaInfo, MetaDictionary, writeFile
from meta_schema import MetaSchema
from meta_html import SiteWriter
from meta_check import doChecks, NameCheckLevel, ClashKinds, ClashException
import logging
import shutil

defaultBasePath=os.path.realpath(os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__),'../../nomad-meta-info'))))

def cleanDir(dir, maxDepth=4):
	"""removes the backup (*.bk) files and directories from the path dir up to a depth of maxDepth""" 
	if maxDepth <= 0 or not os.path.exists(dir):
		return
	for dFile in os.listdir(dir):
		dPath=os.path.join(dir, dFile)
		if os.path.isdir(dPath):
			if dFile.endswith('.bk'):
				try:
					shutil.rmtree(dPath)
				except:
					logging.exception(f"error cleaning up {dPath}")
			else:
				cleanDir(dPath, maxDepth - 1)
		elif dFile.endswith('.bk'):
			try:
				os.remove(dPath)
				logging.info(f'Removed old backup {dPath}')
			except:
				logging.exception(f"error cleaning up {dPath}")

def cascade(explodedDir, dictionaryDir, docsDir, args, deleteOldBk=False, continueOnError=True):
	"""Reformats and propagate from exploded to single file dictionaries"""
	explodedDone=set()
	dictDone=set()
	mInfo=MetaInfo(dictionaries={}, metaNameInDicts={})
	if deleteOldBk:
		dirToClean = []
		if explodedDir:
			dirToClean.append(explodedDir)
		if dictionaryDir:
			dirToClean.append(dictionaryDir)
		if docsDir and os.path.isdir(docsDir):
			dirToClean.append(docsDir)
		for dir in dirToClean:
			cleanDir(dir)
	if explodedDir:
		for dFile in os.listdir(explodedDir):
			try:
				if not dFile.endswith('.meta_dictionary'):
					logging.warn(f"Ignoring unknown entry {dFile}")
				else:
					dPath=os.path.join(explodedDir,dFile)
					d=MetaDictionary.loadAtPath(dPath)
					d.standardize()
					mInfo.addMetaDict(d)
					d.writeExploded(explodedDir)
					if d.metadict_name + '.meta_dictionary'!= dFile:
						safeRemove([dPath])
					explodedDone.add(d.metadict_name)
				if dictionaryDir:
					dPath=os.path.join(dictionaryDir,d.metadict_name + '.meta_dictionary.json')
					writeFile(dPath, lambda f: d.write(f))
					dictDone.add(d.metadict_name)
			except:
				if continueOnError:
					logging.exception(f'Error handling {dFile}')
				else:
					raise Exception(f'Error handling {dFile}')
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
					mInfo.addMetaDict(d)
					dOutPath=os.path.join(dictionaryDir,d.metadict_name + '.meta_dictionary.json')
					writeFile(dOutPath, lambda f: d.write(f))
					dictDone.add(d.metadict_name)
					if name != d.metadict_name:
						safeRemove([dPath])
			except:
				if continueOnError:
					logging.exception(f'Error handling {dFile}')
				else:
					raise Exception(f'Error handling {dFile}')
	# do checks
	for dName,d in sorted(mInfo.dictionaries.items()):
		try:
			schema=MetaSchema.forDictionary(dName, mInfo)
			checkWithArgs(schema, args)
		except:
				if continueOnError:
					logging.exception(f'Failure when checking dictionary {dName}.')
				else:
					raise Exception(f'Failure when checking dictionary {dName}.')
	if docsDir:
		indexBody=['<h1>Documentation for dictionaries</h1>\n<ul class="index">\n']
		regenPaths=[]
		siteWriter=None
		for dName,d in sorted(mInfo.dictionaries.items()):
			try:
				schema=MetaSchema.forDictionary(dName, mInfo)
				
				targetDir=os.path.join(docsDir,dName)
				siteWriter=SiteWriter(schema, targetDir)
				siteWriter.writeAll()
				siteWriter.cleanupUnknown()
				indexBody.append(f'<li><a href="{dName}/index.html"><label class="index">{dName}</label></a></li>\n')
				regenPaths.append(targetDir)
			except:
				logging.exception(f'Failure when generating documentation for dictionary {dName}.')
		indexBody.append('</ul>\n')
		if siteWriter:
			siteWriter.resetToPath(docsDir)
			if regenPaths:
				for d in regenPaths:
					siteWriter.addGeneratedPath(d)
				indexPath=os.path.join(docsDir,'index.html')
				siteWriter.writeLayout(indexPath, body=indexBody, basePath=os.path.basename(regenPaths[0]), title='Schemas Index')
			siteWriter.cleanupUnknown()
			
def cascadeCmd(args):
	if not args.exploded_directory and not args.dict_directory and not args.docs_directory:
		if not args.base_directory:
			args.base_directory=defaultBasePath
		args.exploded_directory=os.path.join(args.base_directory, "meta_dictionary_exploded")
		args.dict_directory=os.path.join(args.base_directory,"meta_dictionary")
		args.docs_directory=os.path.join(args.base_directory,"docs")
	cascade(args.exploded_directory, args.dict_directory, args.docs_directory, deleteOldBk=args.delete_old_bk, continueOnError=args.continue_on_error, args=args)


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

def docCmd(args):
	for inF in args.inPath:
		try:
			mInfo, d=MetaInfo.withPath(inF, extraPaths=args.extra_path)
			schema=MetaSchema.forDictionary(dictName = d.metadict_name, metaInfo=mInfo)
			if args.target_dir:
				target_dir=args.target_dir
			else:
				target_dir=os.path.dirname(inF)
				if inF.endswith('/') or os.path.basename(inF) == '_.meta_dictionary.json':
					target_dir=os.path.normpath(os.path.join(target_dir,'..'))
				target_dir=os.path.join(target_dir,'doc')
			if args.delete_old_bk:
				cleanDir(target_dir)
			siteWriter=SiteWriter(schema, target_dir)			
			siteWriter.writeAll()
			siteWriter.cleanupUnknown()
		except:
			logging.exception(f'documenting {inF}')

def checkWithArgs(schema, args):
	"""checks the given schema with the options given in args"""
	clashMap={
		'ignore-case': ClashKinds.IgnoreCase,
		'ignore-underscores': ClashKinds.IgnoreUnderscores,
		'unique-section-attributes': ClashKinds.UniqueSectionAttributes,
		'ignore-parent-section': ClashKinds.IgnoreParentSection,
		'ignore-type': ClashKinds.IgnoreType,
		'ignore-all': ClashKinds.IgnoreAll
	}
	clashList=args.name_clashes
	if len(clashList)>2:
		clashList=clashList[2:]
	clashKinds=0
	for el in clashList:
		clashKinds=clashKinds|clashMap[el].value
	clashList=args.name_clashes_warn
	if len(clashList)>1:
		clashList=clashList[1:]
	clashWarn=0
	for el in clashList:
		clashWarn=clashWarn|clashMap[el].value
	doChecks(schema, nameCheckLevel = args.name_check, clashKinds=clashKinds)
	try:
		doChecks(schema, nameCheckLevel = args.name_check, clashKinds=clashWarn)
	except ClashException as err:
		clashes="\n  ".join([str(e) for e in err.clashes])
		logging.warn(f'Discouraged name clashes detected in schema for dictionary {schema.mainDictionary}:\n  {clashes}')

def checkCmd(args):
	for path in args.inPath:
		try:
			mInfo, d=MetaInfo.withPath(path, extraPaths=args.extra_path)
			schema=MetaSchema.forDictionary(dictName = d.metadict_name, metaInfo=mInfo)
		except:
			logging.exception(f'Checking {path}')			
		else:
			checkWithArgs(schema, args)

def checkArgs(parser):
	"Adds the arguments for the checks to an argparse parser" 
	parser.add_argument('--extra-path', type=str, action='append',
	  help='extra path to load dependencies')
	parser.add_argument('--name-check', choices=list(NameCheckLevel), help='Constraints on the meta_name.\n strict: only lowercase ascii alphanumeric and underscore ([a-z_][a-zA-Z_]*);\n normal: ascii alphanumeric or underscore;\n weak: unicode alphanumerics and underscore',default=NameCheckLevel.strict)
	parser.add_argument('--name-clashes', action='append', help='Kind of clashes between names that should be checked. It gives the things that should be ignored when comparing, several onew can be given, the default is to ignore all of the listed things (ignore-all) and thus just compare lowercase meta_name stripped of undercores',
	default=['ignore-case', 'unique-section-attributes'],
	choices=['ignore-case', 'ignore-underscores', 'unique-section-attributes', 'ignore-parent-section', 'ignore-type', 'ignore-all'], nargs='+')
	parser.add_argument('--name-clashes-warn', action='append', help='Kind of clashes between names that should be checked. It gives the things that should be ignored when comparing, several onew can be given, the default is to ignore all of the listed things (ignore-all) and thus just compare lowercase meta_name stripped of undercores',
	default=["ignore-all"],
	choices=['ignore-case', 'ignore-underscore', 'unique-section-attributes', 'ignore-parent-section', 'ignore-type', 'ignore-all'], nargs='+')


if __name__ == '__main__':
	import tempfile, sys
	logger=logging.getLogger()
	tmpfile=tempfile.NamedTemporaryFile(delete=False, prefix='meta-', suffix='.log', encoding='utf8', mode='w')
	tmpfile.close()
	fh=logging.FileHandler(filename=tmpfile.name, mode='w', encoding='utf8')
	fh.setLevel(logging.DEBUG)
	df=logging.Formatter(fmt='%(asctime)s %(name)-12s %(levelname)-8s %(message)s', datefmt='%m-%d %H:%M')
	fh.setFormatter(df)
	while logger.hasHandlers():
		logger.removeHandler(logger.handlers[0])
	logger.setLevel(logging.DEBUG)
	logger.addHandler(fh)
	# define a Handler which writes INFO messages or higher to the sys.stderr
	console = logging.StreamHandler()
	consolef=logging.Formatter(fmt='%(levelname)-8s %(message)s')
	console.setFormatter(consolef)
	console.setLevel(logging.INFO)
	logger.addHandler(console)
	logging.info(f'Detailed log to {tmpfile.name}')
	import argparse	
	# create the top-level parser
	parser = argparse.ArgumentParser(prog='meta_tool')
	parser.add_argument('--verbose', help='increases the logging level', action='store_true')
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
	parser_cascade.add_argument('--continue-on-error', action='store_true')
	parser_cascade.add_argument('--docs-directory', type=str,
		help='path to the directory where to generate the documentation on the dictionaries')
	checkArgs(parser_cascade)
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
	parser_r.add_argument('--delete-old-bk', action='store_true')
	parser_r.set_defaults(func=rewriteCmd)
	# create the parser for the "doc" command
	parser_doc = subparsers.add_parser('doc', help='writes the documentation on the given dictionary')
	parser_doc.add_argument('--target-dir', type=str,
		help='target dir if not given defaults to the directory of the first argument +/doc')
	parser_doc.add_argument('inPath', type=str, nargs='+',
		help='a dictionary to document')
	parser_doc.add_argument('--extra-path', type=str, action='append',
	  help='extra path to load dependencies')
	parser_doc.add_argument('--delete-old-bk', action='store_true')
	parser_doc.set_defaults(func=docCmd)
	# create the parser for the "check" command
	parser_check = subparsers.add_parser('check', help='Checks the given dictionary')
	parser_check.add_argument('inPath', type=str, nargs='+',
		help='a dictionary to document')
	checkArgs(parser_check)
	parser_check.set_defaults(func=checkCmd)	
	#args=parser.parse_args(['rewrite', '../meta_info/meta_info_exploded/meta_schema.meta_dictionary'])
	#args=parser.parse_args(['cascade','--delete-old-bk'])
	#args=parser.parse_args(['doc', '../../meta_info/meta_info_exploded/common.meta_dictionary', '--extra-path', '../../meta_info/meta_info/meta_dictionary', '--delete-old-bk'])
	#args=parser.parse_args(['check', '../../meta_info/meta_info_exploded/common.meta_dictionary', '--extra-path', '../../meta_info/meta_info/meta_dictionary'])
	args=parser.parse_args()
	if not args.verbose:
		console.setLevel(logging.WARN)
	if not hasattr(args, 'func'):
		parser.print_help()
	else:
		args.func(args)

