import os
from meta_info import MetaInfo, FileLoader

m=MetaInfo(dictionaries={})
loader=FileLoader(['../meta_info/meta_info/meta_dictionary'])
n=[f[:-len('.meta_dictionary.json')] for f in os.listdir('../meta_info/meta_info/meta_dictionary')]
for nn in n:
	m.addMetaDict(nn,loader(nn))
m.complete(loader)

