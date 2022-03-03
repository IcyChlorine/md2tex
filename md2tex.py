import os
import sys
import json
import re

from soupsieve import match

from constants import *
from entry import Entry

m2s=None #标记markdown -> symbol,
s2t=None #    symbol   -> latex 的映射关系的两个字典，初始化为空

def debug_print(mid_repr):
	if not DEBUG_PRINT: return
	print('[')
	for e in mid_repr:
		print(repr(e))
	print(']')
	print('');os.system('pause');print('')

def load_config():
	global m2s, s2t
	with open('md2sym_template.json','r',encoding='utf8') as f:
		m2s=json.load(f)
	with open('sym2tex_template.json','r',encoding='utf8') as f:
		s2t=json.load(f)

	for key in m2s:
		if type(m2s[key])==list:
			m2s[key]='\n'.join(m2s[key])
	for key in s2t:
		if type(s2t[key])==list:
			s2t[key]='\n'.join(s2t[key])

def reset_env_dict(env):
	for key in env:
		env[key]=False

def is_line_delim(entry_or_str):
	return isinstance(entry_or_str,Entry) and entry_or_str.type==NEWLINE

def get_line_from_mid_repr(mid_repr,here,return_start_and_end=False):
	#输入mid_repr和其中一个元素的位置（下标），
	#找到这个元素所在行的所有元素并以以列表（切片）的形式返回
	assert(here>=0 and here<len(mid_repr))
	if is_line_delim(mid_repr[here]):
		if not return_start_and_end:
			return None
		else:
			return -1,-1

	start,end_,end=here,here,here+1
	while start>=0 and not is_line_delim(mid_repr[start]):
		start-=1
	start+=1
	while end_<len(mid_repr) and not is_line_delim(mid_repr[end_]):
		end_+=1
	end_-=1
	end=end_+1
	#ls[begin,end)=ls[begin,end_]
	if not return_start_and_end:
		return mid_repr[start:end]
	else:
		return start,end
def get_first_line(mid_repr):
	for i in range(len(mid_repr)):
		start,end=get_line_from_mid_repr(mid_repr,i,return_start_and_end=True)
		if start!=-1 and end !=-1: return start,end
	return -1,-1
def get_next_line(mid_repr,start,end=-1):
	if end==-1:
		start,end=get_line_from_mid_repr(mid_repr,start,return_start_and_end=True)
	if end+1<len(mid_repr):
		return get_line_from_mid_repr(mid_repr,end+1,return_start_and_end=True)
	else:
		return -1,-1
def is_last_line(mid_repr,start,end=-1):
	if end==-1:
		start,end=get_line_from_mid_repr(mid_repr,start,return_start_and_end=True)
	if end+1<len(mid_repr):
		return False
	else:
		return True
def is_line_beginner(mid_repr,here):
	start,end=get_line_from_mid_repr(mid_repr,here,return_start_and_end=True)
	return here==start
	

def md2sym(md_src): #-> intermediate format
	global m2s
	global_var=dict()

	global_var['PKG_REQUIRED']=set()
	global_var['NEWCOMMANDS']=[]

	md_src=md_src.split('\n')
	mid_repr=[]

	#这一方案已被遗弃，因为无法处理公式中的星号
	#处理粗体、斜体。
	#因为它们可能跨行，因此不能分行后处理。直接在原字符串上处理。
	'''in_emph_env=False
	def sub_func(matched):
		nonlocal in_emph_env
		if not in_emph_env:
			in_emph_env=True
			if len(matched.group())>=2:
				return r'\textbf{'
			else:
				return r'\emph{'
		else:
			in_emph_env=False
			return '}'
	#这个正则表达式可以提取 非单行的 1-3个连续星号
	md_src=re.sub(r'((?<!\n|\*)\*{1,3})|(\*{1,3}(?!\n|\*))',sub_func,md_src)
	'''
	

	env={
		'code':False,	#标记是否在数学环境中
		'fml':False,	#标记是否在代码环境中
		'enum':False,	#标记枚举环境的开头和结尾
		'emph':False	#标记粗斜体环境的开头和结尾
	}
	#第一遍：处理粗斜体。为了避开单独成行的分割线和公式环境，就需要识别公式环境。
	#因此又必须要维护公式环境。所以要走两遍。
	#print('----第一遍扫描：按行识别特殊元素----')
	print('    (1/5) Parsing elements by lines...')
	for line in md_src:
		#单独成行的分割线
		match_obj=re.match(r'\s*\*{3}\s*',line)
		if match_obj and match_obj.group()==line:
			mid_repr.append(Entry(DELIM))
			mid_repr.append(Entry(NEWLINE))
			continue

		#进出多行数学和代码环境
		if line==r'$$':
			if not env['fml']: mid_repr.append(Entry(MULTILINE_FML_BEGIN))
			else:              mid_repr.append(Entry(MULTILINE_FML_END))
			mid_repr.append(Entry(NEWLINE))
			env['fml']=not env['fml']#进出行间公式
			global_var['PKG_REQUIRED'].add('amsmath')#只要有公式，默认加这两个包
			global_var['PKG_REQUIRED'].add('amssymb')
			continue
		if line.startswith('```'):
			if not env['code']: mid_repr.append(Entry(MULTILINE_CODE_BEGIN))
			else:              mid_repr.append(Entry(MULTILINE_CODE_END))
			mid_repr.append(Entry(NEWLINE))
			env['code']=not env['code']#进出多行代码
			global_var['PKG_REQUIRED'].add('listings')#为了显示代码，需要listing宏包
			continue

		if line=='' and env['fml']:
			#由于"$$"围起来的行间公式当中不能有空行，因此要将其去掉
			#即忽略(不往mid_repr中加)
			continue
		#将\newcommand抽取出来，从而最后可以统一放到导言区
		if line.startswith(r'\newcommand') or line.startswith(r'\renewcommand'):
			global_var['NEWCOMMANDS'].append(line)
			continue

		mid_repr.append(line)#其它的字符串先保留字符串形式，留待后面处理
		mid_repr.append(Entry(NEWLINE))
	mid_repr.pop(-1)#把最后额外加上的NEWLINE去掉

	debug_print(mid_repr)

	#print('----第二遍扫描：识别行内公式----')
	print('    (2/5) Handling inline formulas...')
	md_src = mid_repr
	mid_repr = []#流水线式处理，一步一步地
	reset_env_dict(env)
	#处理行内公式
	for entry in md_src:
		if isinstance(entry,Entry):
			if entry.type==MULTILINE_FML_BEGIN:  env['fml'] =True
			if entry.type==MULTILINE_FML_END:    env['fml'] =False
			if entry.type==MULTILINE_CODE_BEGIN: env['code']=True
			if entry.type==MULTILINE_CODE_END:   env['code']=False
			mid_repr.append(entry)
			continue
			
		line = entry
		assert(isinstance(line,str))

		if env['fml'] or env['code']:
			mid_repr.append(line)
			continue

		parts = line.split('$')
		for i,part in enumerate(parts):
			if i:
				if not env['fml']: mid_repr.append(Entry(FML_BEGIN))
				else:              mid_repr.append(Entry(FML_END))
				env['fml']=not env['fml']
			mid_repr.append(part)
			
	debug_print(mid_repr)

	#第三遍：处理粗体斜体格式问题
	#print('----第三遍扫描：处理粗斜体问题----')
	print('    (3/5) Handling bold and italic texts...')
	md_src = mid_repr
	mid_repr = []#流水线式处理，一步一步地
	reset_env_dict(env)
	env['bold']=False
	env['italic']=False
	env['bold_italic']=False#因为markdown中粗斜体是三个星号一块考虑的，

	for entry in md_src:
		if isinstance(entry,Entry):
			if entry.type==          FML_BEGIN:  env['fml'] =True
			if entry.type==          FML_END:    env['fml'] =False
			if entry.type==MULTILINE_FML_BEGIN:  env['fml'] =True
			if entry.type==MULTILINE_FML_END:    env['fml'] =False
			if entry.type==MULTILINE_CODE_BEGIN: env['code']=True
			if entry.type==MULTILINE_CODE_END:   env['code']=False
			mid_repr.append(entry)
			continue
			
		textpart = entry #此时的文字可能已经被分割开、不是一整行了。因此语义上不是line，改成textpart.
		assert(isinstance(textpart,str))

		if env['fml'] or env['code']:#跳过公式&代码环境
			mid_repr.append(textpart)
			continue

		while True:#从前往后处理textpart，处理其中的“*”。
			#print(env)
			#print(textpart)
			if not env['bold'] and not env['italic'] and not env['bold_italic']:
				#如果在粗斜体环境外：
				#顺次，找到最近的“*”。连在一起的*，尽量一起识别。
				bold_pos=textpart.find('**')
				italic_pos=textpart.find('*')
				bold_italic_pos=textpart.find('***')

				mark_pos=-1
				mark_len=-1
				mark_type=None
				if bold_pos==-1 and italic_pos==-1 and bold_italic_pos==-1:
					mark_pos=-1
					mark_len=0
				else:#找到最近的粗斜体开始位置
					mark_pos=max(italic_pos,bold_pos,bold_italic_pos)
					if italic_pos!=-1 and italic_pos<=mark_pos:
						mark_pos=italic_pos
						mark_len=1 #len('*')
						mark_type=ITALIC_BEGIN
					if bold_pos!=-1 and bold_pos<=mark_pos:
						mark_pos=bold_pos
						mark_len=2 #len('**')
						mark_type=BOLD_BEGIN
					if bold_italic_pos!=-1 and bold_italic_pos<=mark_pos:
						mark_pos=bold_italic_pos
						mark_len=3 #len('***')
						mark_type=BOLD_ITALIC_BEGIN
				if mark_pos!=-1:#如果找到了
					if mark_pos>0: mid_repr.append(textpart[:mark_pos])
					textpart=textpart[mark_pos:]
					mid_repr.append(Entry(mark_type))
					textpart=textpart[mark_len:]
					if mark_type==BOLD_BEGIN:          env['bold']=True
					elif mark_type==ITALIC_BEGIN:      env['italic']=True
					elif mark_type==BOLD_ITALIC_BEGIN: env['bold_italic']=True
				else:
					mid_repr.append(textpart)
					textpart=''
			else:#此时已经在粗斜体环境里
				if env['bold']:
					mark_pos=textpart.find('**')
					mark_len=2
					mark_type=BOLD_END
				elif env['italic']:
					mark_pos=textpart.find('*')
					mark_len=1
					mark_type=ITALIC_END
				elif env['bold_italic']:
					mark_pos=textpart.find('***')
					mark_len=3
					mark_type=BOLD_ITALIC_END
				if mark_pos!=-1:
					if mark_pos>0: mid_repr.append(textpart[:mark_pos])
					textpart=textpart[mark_pos:]
					mid_repr.append(Entry(mark_type))
					textpart=textpart[mark_len:]
					if mark_type==BOLD_END:          env['bold']=False
					elif mark_type==ITALIC_END:      env['italic']=False
					elif mark_type==BOLD_ITALIC_END: env['bold_italic']=False
				else:
					mid_repr.append(textpart)
					textpart=''
			#when textpart is fully consumed out, break.
			if not textpart: break
	
	debug_print(mid_repr)

	#第四遍 处理标题与段落
	#print('----第四遍扫描：处理标题与段落----')
	print('    (4/5) Handling title and sections marks...')
	md_src=mid_repr
	mid_repr=[]
	del env['bold'],env['italic'],env['bold_italic']
	reset_env_dict(env)

	start,end=get_first_line(md_src)
	if isinstance(md_src[start],str):
		match_obj=re.match(r'#{1,5} (.*)',md_src[start])
	if match_obj:
		title_entry=Entry(TITLE)
		title_entry.content=[*md_src[start:end]]
		title_entry.content[0]=match_obj.group(1)

		global_var['TITLE']=title_entry
		mid_repr=md_src[:start]+[title_entry]
		i=end
	else:
		title_entry=Entry(TITLE)
		title_entry.content=['<empty title>']
		global_var['TITLE']=title_entry
	
	
	while i<len(md_src):
		entry=md_src[i]
		if not isinstance(entry, str) or not is_line_beginner(md_src,i):
			mid_repr.append(entry)
			i+=1;continue
		#TODO 判断是否在多行公式/代码环境中，跳过这两者。
		#else
		i,j=get_line_from_mid_repr(md_src,i,return_start_and_end=True)
		if md_src[i].startswith('> '):
			md_src[i]=md_src[i][2:]#忽略引用环境

		if md_src[i].startswith('+ ') or md_src[i].startswith('- '):
			if not env['enum']:
				env['enum']=True
				mid_repr.append(Entry(ENUM_BEGIN))		
			mid_repr.append(Entry(ITEM))
			mid_repr.append(md_src[i][2:])
			i+=1;continue
		else:#出枚举环境
			if env['enum']:
				mid_repr.append(Entry(ENUM_END))
				env['enum']=False

		if md_src[i].startswith('### '):
			section_title=md_src[i:j]
			section_title[0]=section_title[0][4:]
			mid_repr.append(Entry(SECTION,section_title))
			i=j;continue
		elif md_src[i].startswith('#### '):
			section_title=md_src[i:j]
			section_title[0]=section_title[0][5:]
			mid_repr.append(Entry(SUBSECTION,section_title))
			i=j;continue
		elif md_src[i].startswith('##### '):
			section_title=md_src[i:j]
			section_title[0]=section_title[0][6:]
			mid_repr.append(Entry(SUBSUBSECTION,section_title))
			i=j;continue

		mid_repr.append(md_src[i])
		i+=1
		
	debug_print(mid_repr)
	
	#处理图片
	#目前只能处理单行的图片
	#print('----第五遍扫描：处理图片----')
	print('    (5/5) Processing inserted images...')
	for i,part in enumerate(mid_repr):
		if not isinstance(part,str): continue
		match_obj = re.match(r'!\[(.*)\]\((.*)\)',part)
		if match_obj: 
			img=Entry(IMAGE)
			img.path=match_obj.group(2)
			img.caption=match_obj.group(1)
			mid_repr[i]=img
			global_var['PKG_REQUIRED'].add('graphicx')
			global_var['PKG_REQUIRED'].add('float')

	debug_print(mid_repr)

	global_var['PKG_REQUIRED']=list(global_var['PKG_REQUIRED'])
	global_var['PKG_REQUIRED'].sort()

	return mid_repr,global_var
	
def assemble_latex_components(mid_repr):
	mid_repr_assembled=[
		Entry(PREAMBLE), 
		Entry(DOC_BEGIN), 
		*mid_repr, 
		Entry(DOC_END)
	]
	return mid_repr_assembled

def replace_global_var(s,global_var):
	gvar_string=dict()
	gvar_string['TITLE']=sym2tex(global_var['TITLE'].content,global_var)
	gvar_string['PKG_REQUIRED']='\n'.join([f"\\usepackage{{{pkg}}}" for pkg in global_var['PKG_REQUIRED']])
	gvar_string['NEWCOMMANDS']='\n'.join(global_var['NEWCOMMANDS'])
	gvar_string['AUTHOR_INFO']=global_var['AUTHOR_INFO']
	gvar_string['PKG_OPTIONS']=s2t['LISTINGS_OPTIONS'] if 'listings' in global_var['PKG_REQUIRED'] else ''

	for key in gvar_string:
		s=s.replace('#'+key+'#',gvar_string[key])
	s=s.replace('##','#')#handle escape characters, if there's any.
	return s

def sym2tex(mid_repr,global_var): #-> tex src str
	global s2t
	tex_src=[]
	for entry in mid_repr:
		if isinstance(entry,str): 
			ch_to_esc="\\_#$%{}"
			s=''
			#latex中\\是换行；因此反斜杠的转移是\backslash，要特殊处理
			for c in entry:
				if c in ch_to_esc:
					s+=('\\'+c) if c!='\\' else '$\\backslash$'
				else:
					s+=c
			tex_src.append(s)
			continue

		assert(isinstance(entry, Entry))
		if entry.type==NEWLINE:#特殊元素
			tex_src.append('\n')
		elif entry.type==DELIM:
			tex_src.append('\\begin{center}\n\t*\\quad*\\quad*\n\end{center}')
		elif entry.type==TITLE:#标题与段落
			pass
		elif entry.type==SECTION:
			tex_src.append(r'\section{'+sym2tex(entry.content,global_var)+'}')
		elif entry.type==SUBSECTION:
			tex_src.append(r'\subsection{'+sym2tex(entry.content,global_var)+'}')
		elif entry.type==SUBSUBSECTION:
			tex_src.append(r'\subsubsection{'+sym2tex(entry.content,global_var)+'}')
		elif entry.type==ENUM_BEGIN:#枚举环境
			tex_src.append(r'\begin{itemize}')
		elif entry.type==ITEM:
			tex_src.append('\t\\item ')
		elif entry.type==ENUM_END:
			tex_src.append(r'\end{itemize}')
		elif entry.type==FML_BEGIN or entry.type==FML_END:#公式与代码
			tex_src.append('$')
		elif entry.type==MULTILINE_FML_BEGIN or entry.type==MULTILINE_FML_END:
			tex_src.append('$$')
		elif entry.type==CODE_BEGIN:
			tex_src.append(r'\begin{lstlisting}')#TODO lstlisting的设置还没有考虑
		elif entry.type==CODE_END:
			tex_src.append(r'\end{lstlisting}')#注意，这里还不支持行内代码，应为没有latex功能可以很方便地实现
		elif entry.type==BOLD_BEGIN:
			tex_src.append(r'\textbf{')
		elif entry.type==ITALIC_BEGIN:
			tex_src.append(r'\emph{')
		elif entry.type==BOLD_ITALIC_BEGIN:
			tex_src.append(r'\textbf{\emph{')
		elif entry.type==BOLD_END or entry.type==ITALIC_END:
			tex_src.append('}')
		elif entry.type==BOLD_ITALIC_END:
			tex_src.append('}}')
		elif entry.type==IMAGE:#图像
			s=s2t['FIGURE']
			s=s.replace('#path#', entry.path)
			s=s.replace('#caption#', entry.caption)
			s=s.replace('##','#') #handle escape characters
			tex_src.append(s)
		elif entry.type==DOC_BEGIN:
			s=s2t['DOC_BEGIN']
			tex_src.append(replace_global_var(s,global_var))
		elif entry.type==DOC_END:
			s=s2t['DOC_END']
			tex_src.append(replace_global_var(s,global_var))
		elif entry.type==PREAMBLE:
			s=s2t['PREAMBLE']
			tex_src.append(replace_global_var(s,global_var))
		else:
			print("WTF?? Unknown entry type.")
			raise ValueError('Unknown entry type:'+entry.type)
	return ''.join(tex_src)


def main(argv):
	load_config()
	
	input_path=argv[1]
	if '-o' in argv:
		idx=argv.index('-o')
		output_path=argv[idx+1]
	else:
		output_path=input_path.replace('.md','.tex')

	print('(1/4) Reading configuration files...')
	with open(input_path,'r',encoding='utf8') as f:
		md_src=f.read()

	print('(2/4) Parsing markdown sources...')
	mid_repr,global_var=md2sym(md_src)

	print('(3/4) Adding latex components to intermediate representation...')
	mid_repr=assemble_latex_components(mid_repr)
	global_var['AUTHOR_INFO']=r"IcyChlorine\footnote{icy\_chlorine@pku.edu.cn}"

	print('(4/4) Generating latex source codes...')
	with open(output_path,'w',encoding='utf8') as f:
		f.write(sym2tex(mid_repr,global_var))
	print('Done! Latex source file has been written to `'+output_path+'`.')

if __name__ == "__main__":
	main(sys.argv)