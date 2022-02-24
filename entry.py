from constants import *

# entry in middle representation
class Entry():
	def __init__(self,type,content=''):
		self.type=type
		self.content=content
		self.env={}

	def __repr__(self):
		ret_val=''
		ret_val+= f'<entry type={self.type}'+\
			(f' content={self.content}' if self.content else '')
		if self.type==IMAGE:
			ret_val+=f' path={self.path} caption={self.caption}'

		ret_val+='>'
		return ret_val