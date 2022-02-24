import sys
import json
import re

m2s=None #标记markdown -> symbol,
s2t=None #    symbol   -> latex 的映射关系的两个字典，初始化为空

def load_config():
	global m2s, s2t
	with open('md2sym_template.json','r') as f:
		m2s=json.load(f)
	with open('sym2tex_template.json','r') as f:
		s2t=json.load(f)

	for key in m2s:
		if type(m2s[key])==list:
			m2s[key]='\n'.join(m2s[key])
	for key in s2t:
		if type(s2t[key])==list:
			s2t[key]='\n'.join(s2t[key])

def md2sym(md_src): #-> intermediate format
	global m2s
	global_var=dict()

	global_var['PKG_REQUIRED']=[]
	global_var['NEWCOMMANDS']=[]

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
	md_src=md_src.split('\n')
	in_code_env,in_fml_env=False,False#标记当前行是否在数学或代码环境中
	in_enum_env,in_emph_env=False,False#标记枚举结构/粗斜体环境的开始和结尾
	#第一遍：处理粗斜体。为了避开单独成行的分割线和公式环境，就需要识别公式环境。
	#因此又必须要维护公式环境。所以要走两遍。
	i=0
	while i<len(md_src):
		print(i,len(md_src))
		line=md_src[i]
		
		#进出多行数学和代码环境
		if line==r'$$':
			in_fml_env=not in_fml_env#进出行间公式
			i+=1;continue#(跳过开头结尾的行)
		if line==r'```':
			in_code_env=not in_code_env#进出多行代码
			i+=1;continue

		if line=='' and in_fml_env:
			#由于"$$"围起来的行间公式当中不能有空行，因此要将其去掉
			md_src.pop(i)
			continue

		#多行公式和多行代码环境不接受下面的格式控制，因此跳过(当中的行)
		if in_code_env or in_fml_env:
			i+=1;continue

		#处理粗体和斜体。难的地方是，要避开单行的分割横线，和行内公式中的星号。
		if re.match(r'\s*\*{3}\s*',line):#避开单独成行的分割线
			i+=1;continue
		#由于已经处理过了多行公式，因此可以保证此时的行开始时在公式外
		def sub_func(matched):#替换函数
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

		entry=line.split('$')
		#Corner Case: 如果最后有一个未配对的$
		#if len(entry)%2==0:
		#	entry[-2]=entry[-2]+r'\$'+entry[-1]
		#	entry.pop(-1)
		#我现在选择不处理
		for j in range(len(entry)):
			part=entry[j]
			if j!=0: in_fml_env=not in_fml_env
			if in_fml_env: continue#这样就可以跳过行内公式环境了
			entry[j]=re.sub(r'\*{1,3}',sub_func,part)
			#Corner Case: md中一行内连着两个$$，但这两个$$不是单独成行的情形。试试就知道了。
			#这不是完美处理。不过相信应该不会有人写这种内容吧。。
			#if entry[j]=='': entry[j]=' ' #处理了bug比不处理还多，不处理了，开摆！
		md_src[i]='$'.join(entry)
			
		#其余情形：i++
		i+=1


	
	#第二遍 处理标题，图片，枚举和引用环境，以及公式的逻辑
	#处理第一行的标题，如果有的话
	ans=re.match(r'#{1,5} (.*)',md_src[0])
	if ans:
		global_var['TITLE']=ans.group(1)
		md_src.pop(0)

	#由于markdown很多语法元素是按行分的，因此可以逐行处理
	in_code_env,in_fml_env=False,False#标记当前行是否在数学或代码环境中
	in_enum_env,in_emph_env=False,False#标记枚举结构/粗斜体环境的开始和结尾
	i=0#重新从头开始
	while i<len(md_src):
		print(i,len(md_src))
		line=md_src[i]

		#标题与段落
		if line.startswith('### '):#我的习惯使用###作一级标题。可调。
			md_src[i]=r'\section{'+line[4:]+r'}'
			i+=1;continue
		if line.startswith('#### '):
			md_src[i]=r'\subsection{'+line[5:]+r'}'
			i+=1;continue
		if line.startswith('##### '):
			md_src[i]=r'\subsubsection{'+line[6:]+r'}'
			i+=1;continue
		
		ans = re.match(r'(>\s*)+(.*)',line)#处理引用环境。现在的做法是直接忽略，把所有引用去掉。
		if ans: 
			md_src[i]=ans.group(2)

		#处理枚举
		ans = re.match(r'\s*[\+-] (.*)',line)
		if ans:
			md_src[i]='\t\\item '+ans.group(1)#注意line不是引用，要修改源码的话必须用md_src[i]
			if not in_enum_env:
				in_enum_env=True
				md_src.insert(i,r'\begin{itemize}')
				i+=1		
			if (i+1<len(md_src) and not re.match(r'\s*[\+-] (.*)',md_src[i+1])) or i+1==len(md_src):
				md_src.insert(i+1,r'\end{itemize}')
				i+=1
				in_enum_env=False
			i+=1;continue
		
		


		#提取\newcommand
		if line.startswith(r'\newcommand'):
			global_var['NEWCOMMANDS'].append(line)
			md_src.pop(i)
			continue
		
		#进出多行数学和代码环境
		if line==r'$$':
			in_fml_env=not in_fml_env#进出行间公式
			i+=1;continue
		if line==r'```':
			in_code_env=not in_code_env#进出多行代码
			i+=1;continue

		if line=='' and in_fml_env:
			#由于latex中"$$"围起来的行间公式当中不能有空行，因此要将其去掉
			md_src.pop(i)
			continue

		#多行公式和多行代码环境不接受下面的格式控制，因此跳过
		if in_code_env or in_fml_env:
			i+=1;continue


		#处理图片
		#目前只能处理单行的图片
		ans = re.match(r'!\[(.*)\]\((.*)\)',line)
		if ans: 
			param={'path':ans.group(2),'caption':ans.group(1)}
			md_src[i]=r'^^^^'+'FIGURE'+'?'+repr(param)+'$$$$'
			global_var['PKG_REQUIRED'].append('graphicx')
			global_var['PKG_REQUIRED'].append('float')
			i+=1;continue

		

		#其余情形：plain text，i++
		i+=1
	global_var['PKG_REQUIRED']=list(set(global_var['PKG_REQUIRED']))#用set进行去重
	global_var['PKG_REQUIRED'].sort()
	return md_src,global_var


def sym2tex(mid_repr,global_var): #-> tex src str
	global s2t
	def is_symbol(entry):
		return re.match(r"\^{4}.*\${4}",entry)
	for i,entry in enumerate(mid_repr):
		if not is_symbol(entry): continue
		tmp=entry[4:-4].split('?')
		if len(tmp)==2:
			token,param=tmp[0],eval(tmp[1])
		else:
			token,param=tmp[0],dict()
		mid_repr[i]=s2t[token]
		for var in param:#local params
			mid_repr[i]=mid_repr[i].replace('#'+var+'#',param[var])
	mid_repr='\n'.join(mid_repr)
	for var in global_var:
		if var=='PKG_REQUIRED':
			global_var[var]=[r'\usepackage{'+pkg+'}' for pkg in global_var[var]]
		if type(global_var[var])==list:
			global_var[var]='\n'.join(global_var[var])
		mid_repr=mid_repr.replace('#'+var+'#',global_var[var])
	return mid_repr


def main(argv):
	load_config()

	with open(argv[1],'r',encoding='utf8') as f:
		md_src=f.read()

	mid_repr,global_var=md2sym(md_src)

	tmp=['PREAMABLE','DOC_BEGIN','DOC_END']
	tmp=['^^^^'+entry+'$$$$' for entry in tmp]
	mid_repr=[tmp[0],tmp[1]]+mid_repr+[tmp[2]]
	global_var['AUTHOR_INFO']=r"IcyChlorine\footnote{icy\_chlorine@pku.edu.cn}"
	global_var['PKG_REQUIRED']+=['amsmath','amssymb']

	with open('tex_src.tex','w',encoding='utf8') as f:
		f.write(sym2tex(mid_repr,global_var))

if __name__ == "__main__":
	main(sys.argv)