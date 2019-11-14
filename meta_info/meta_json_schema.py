from ..meta_schema import MetaSchema
from ..meta_info import MetaDataType

class JsonSchemaDumper (object):
	def __init__(self,schema,basePath, baseUri=None, suspendable=True):
		self.schema=schema
		self.basePath=basePath
		self.baseUri=baseUri
		self.suspendable=suspendable
	
	def arraySchema(self, baseType, dim=1, suspendable=None):
		if suspendable is None:
			suspendable=self.suspendable
		if dim==1:
			dictType={
				'type':'object',
				'properties':{
					'array_data': baseType,
					'array_indexes': { 'type': 'array', 'items': {'type':'integer'} },
					'array_stored_length': { 'type': 'integer' },
					'array_range': { 'type': 'array', 'items': {'type':'integer'}}
				}
			}
		else:
			dictType={
				'type':'object',
				'properties':{
					f'array_{dim}d_flat_data': {'type': 'array', 'items':baseType},
					f'array_{dim}d_indexes': {'type': 'array', 'items':{ 'type': 'array', 'items': dim * [{'type':'integer'}] }},
					f'array_{dim}d_stored_length': {'type':'array', 'items':{ 'type': 'integer' }},
					f'array_{dim}d_range': { 'type': 'array', 'items':{ 'type': 'array', 'items': {'type':'integer'},  "minItems": 2,"maxItems": 3},"minItems": dim,"maxItems": dim}
				}
			}
		arrType= { 'type': 'array', 'items': baseType }
		for idim in range(1,dim):
			arrType={'type': 'array', 'items': arrType }
		if suspendable:
			return {'oneOf': [arrType, dictType]}
		else:
			return arrType

	def valueSchema(self, metaValue):
		'null','array','object','integer', 'string', 'boolean', 'number'
		baseTypeMap={
			MetaDataType.Int: {'type':'integer'},
			MetaDataType.Int32: {'type':'integer'},
			MetaDataType.Int64: {'type':['integer', 'string']},
			MetaDataType.Boolean: {'type':'boolean'},
			MetaDataType.Reference: {'type':'integer'}
			MetaDataType.Float32: {'type':'number'}, 
			MetaDataType.Float: {'type':'number'},
			MetaDataType.Float64: {'type':'number'},
			MetaDataType.String: {'type':'string'},
			MetaDataType.Binary: { 'type': 'object', 'properties': {'binary_data_stored_size': { 'description': 'total length in bytes of the data stored', 'type':'integer' }, 'binary_data_range': { 'type': 'array', 'items': [{'type':'integer', 'description': '0-based offset giving the start byte index of the data returned'},{'type':'integer', 'description':'0-based upper bound (not included) of the byte index of data returned'}], 'additionalItems':false}, 'base64_data':{ 'type': 'oneOf': ['string',{'type': 'array', 'additionalItems': {'type': 'string'}}], 'Base 64 encoded binary data either a single string or as an array of strings'}}, 'description': 'Object storing binary data (or part of it) encoded using base 64 string'} ,
			MetaDataType.Json: {'type':'object'}
		}
		baseType=baseTypeMap[metaValue.meta_data_type]
		if metaValue.meta_shape:
			dim=len(metaValue.meta_shape)
			val=self.arraySchema(baseType, dim)
		else:
			val=baseType
		if metaValue.meta_repeats:
			val=self.arraySchema(val)
		val['title']=f'Value {metaValue.meta_parent_section}.{metaValue.meta_name}'
		val['description']=maybeJoinStr(metaValue.meta_description)
		if metaValue.meta_examples:
			examples = []
			for e in metaValue.meta_examples:
				if not e startswith('!'):
					try:
						examples.append(json.loads(e))
					except:
						logging.error(f'Invalid json in example {repr(e)} in {metaValue}')
			if examples:
				val['examples']=examples
		return val
