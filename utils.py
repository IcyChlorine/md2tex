import os
import sys
import json
from contextlib import contextmanager

from constants import *
from entry import Entry

def debug_print(mid_repr):
	if not DEBUG_PRINT: return
	print('[')
	for e in mid_repr:
		print(repr(e))
	print(']')
	print('');os.system('pause');print('')

@contextmanager
def wrapped_open(filename,*args,**kwargs):
	success=False
	try:
		f=open(filename,*args,**kwargs)
		success=True
	except FileNotFoundError:
		pass

	i=len(sys.path)-1
	while not success and i>=0:
		try:
			path=sys.path[i]
			if not path.endswith('\\'): path=path+'\\'
			f=open(path+filename,*args,**kwargs)
			success=True
		except FileNotFoundError:
			pass
		i=i-1
	if not success:
		raise FileNotFoundError

	yield f
	
	f.close()

def load_config(md2sym_cfg=DEFAULT_MD2SYM_CONFIG,sym2tex_cfg=DEFAULT_SYM2TEX_CONFIG):
	#global m2s, s2t
	with wrapped_open(md2sym_cfg,'r',encoding='utf8') as f:
		m2s=json.load(f)
	with wrapped_open(sym2tex_cfg,'r',encoding='utf8') as f:
		s2t=json.load(f)

	for key in m2s:
		if type(m2s[key])==list:
			m2s[key]='\n'.join(m2s[key])
	for key in s2t:
		if type(s2t[key])==list:
			s2t[key]='\n'.join(s2t[key])
	return m2s,s2t

def reset_env_dict(env):
	for key in env:
		env[key]=False

def is_line_delim(entry_or_str):
	return isinstance(entry_or_str,Entry) and entry_or_str.type==NEWLINE

def escape_special_ch(s):
	ch_to_esc="\\_#$%{}"
	ret=''
	#latex中\\是换行；因此反斜杠的转移是\backslash，要特殊处理
	for c in s:
		if c in ch_to_esc:
			ret+=('\\'+c) if c!='\\' else '$\\backslash$'
		else:
			ret+=c
	return ret