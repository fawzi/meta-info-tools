import os
from meta_info import MetaInfo, MetaDictionary

m=MetaInfo(dictionaries={})
loader=MetaDictionary.fileLoader(['../meta_info/meta_info/meta_dictionary'])
n=[f[:-len('.meta_dictionary.json')] for f in os.listdir('../meta_info/meta_info/meta_dictionary')]
for nn in n:
	m.addMetaDict(loader(nn))
m.complete(loader)

