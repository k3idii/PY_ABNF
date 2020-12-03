import lark
import random
import re


ALMOST_INFINITY = 42 # ROTFL

def flip_the_coin():
  return random.randint(0,1)


class ABNF_LazyResolver:
  def __init__(self, src, name):
    self.src = src
    self.name = name
  
  def __repr__(self):
    return f"<LAZY-REF> {self.name} </LAZY-REF>"

  def generate(self):
    #print(f"Yo man, here is your lazy resolver ... to {self.name}")
    val = self.src.get(self.name, None)
    assert val is not None, "FAIL TO RESOLVE lazy reference to : {self.name}"
    #print(val)
    return val.generate()


class ABNF_Generator:
  def __init__(self, ctx, arg, *other):
    self.ctx = ctx
    self.arg = arg
    self.setup(*other)

  def setup(self):
    pass

  def _resolve(self, varname):
    #print("RESOLVE:", varname, self.ctx.RULES.keys())
    val = self.ctx.RULES.get(varname, None)
    if val == None:
      #print("LAZY RESOLVER !!!!", varname)
      return ABNF_LazyResolver(self.ctx.RULES, varname)
    else:
      #print("INLINE RESOLVE !", varname)
      return val

  def generate(self):
    raise Exception("Implement Me" + str(self.__class__))

class ABNF_None(ABNF_Generator):
  def __repr__(self):
    return f"<NONE>"

  def generate(self):
    return b""

class ABNF_AbstractRepeat(ABNF_Generator):
  def setup(self):
    self.fmt, self.subject = self._extract()
    self._parse_repeate()

  def _extract(self):
    raise Exception("Implement extractor !")

  def _parse_repeate(self):
    expr = re.compile('(?P<a>[0-9]*)(?P<star>[*]?)(?P<b>[0-9]*)')
    mobj = expr.match(self.fmt)
    a,star,b = mobj.groups()
    #print(f" [{a}] .{star:2}. [{b}] ")
    if star == '': #  3XX
      self.repeat_a = int(a)
      self.repeat_b = int(a)
    else:
      if a == '': #  *3XX
        self.repeat_a = 0
      else:       
        self.repeat_a = int(a)
      if b == '': # 3*XX
        self.repeat_b = ALMOST_INFINITY
      else: 
        self.repeat_b = int(b)
    assert self.repeat_a <= self.repeat_b, "Invalid repeat statement !"
    
  def generate(self):
    #print("GENERATE", self.__class__, self.arg )
    size = 1
    if self.repeat_a == self.repeat_b:
      size = self.repeat_b
    else:
      size = random.randint(self.repeat_a, self.repeat_b)
    return b''.join( self.subject.generate() for _ in range(size) )

  def __repr__(self):
    return f"<REPEAT range='{self.repeat_a} ... {self.repeat_b}'>{self.subject}</REPEAT>"


class ABNF_Repeat(ABNF_AbstractRepeat):  
  def _extract(self):
    expr = re.compile('(?P<fmt>[0-9*]+)(?P<varname>[A-Z][A-Z0-9-]*)')
    mobj = expr.match(self.arg)
    #print(mobj, mobj.groups())
    fmt, varname = mobj.groups()
    return fmt, self._resolve(varname)

class ABNF_Group(ABNF_AbstractRepeat):
  def _extract(self):
    bra, child, ket = self.arg
    fmt = '1'
    if len(bra) > 1:
      fmt = bra[:-1]
    return fmt, child

class ABNF_Primitive(ABNF_Generator):
  name = '<Interface>'

  def __repr__(self):
    return f"<{self.name} arg='{self.arg}'>"

class ABNF_FixString(ABNF_Primitive):
  name = "String"
  def setup(self):
    self.arg = self.arg[1:-1]
  def generate(self):
    return self.arg.encode()

class ABNF_NumString(ABNF_Primitive):
  name = "DecString"
  def setup(self, base):
    self.base = base

  def generate(self):
    fmt = self.arg[2:]
    retval = []
    base = self.base
    # worst case: xx-xx.xx.xx-xx.xx 
    for part in fmt.split('.'):
      if '-' in part:
        a,b = part.split('-')
        val = random.randint(int(a,base), int(b,base))
      else:
        val = int(part, base)
      retval.append(val)  
    #print(retval)
    return bytes(retval)
    
class ABNF_Reference(ABNF_Primitive):
  name = "Ref"
  def generate(self):
    return self._resolve(self.arg).generate()
    #return f"REF TO {self.arg}".encode()


class ABNF_List(ABNF_Generator):
  def __repr__(self):
    inner = '  '.join(map(str,self.arg))
    return f"<ITEMS> {inner} </ITEMS>"
  
  def generate(self):
    #print(self)
    return b''.join(x.generate() for x in self.arg)

  
class ANBF_Optional(ABNF_Generator):
  def setup(self):
    self.arg = self.arg[1]

  def __repr__(self):
    return "<OPTIONAL>" + str(self.arg) + "</OPTIONAL>"

  def generate(self):
    if flip_the_coin():
      return self.arg.generate()
    else:
      return b''

class ABNF_Alternative(ABNF_Generator):
  def setup(self):
    self.opt = [ self.arg[0] , self.arg[2] ]

  def __repr__(self):
    return f"<ALT>  {self.arg[0]} <--OR {self.arg[1]} --> {self.arg[2]} </ALT>"

  def generate(self):
    return self.opt[flip_the_coin()].generate()  


class ABNFTransformer(lark.Transformer):
  RULES = dict()

  def primitive(self, node):
    node = node[0]
    if node.type == 'RULENAME':
      return ABNF_Reference(self, node.value)
    elif node.type == 'HEX_STRN':
      return ABNF_NumString(self, node.value, 16)
    elif node.type == 'DEC_STRN':
      return ABNF_NumString(self, node.value, 10)
    elif node.type == 'BIN_STRN':
      return ABNF_NumString(self, node.value, 2)
    elif node.type == 'ESCAPED_STRING':
      return ABNF_FixString(self, node.value) 
    elif node.type == 'REP_RULE':
      return ABNF_Repeat(self, node.value)
    s = f"{node.type}({node.value})"
    raise Exception(s)
    return s

  def group(self, arg):
    #print('GROUP', arg)
    return ABNF_Group(self, arg)

  def optional(self, arg):
    return ANBF_Optional(self, arg)

  def list_of_primitives(self, arg):
    return ABNF_List(self, arg)

  def concat_statement(self, arg):
    return ABNF_List(self, arg)

  def multiline_spec(self, arg):
    return ABNF_List(self, arg)
  
  def alternative(self, arg):
    return ABNF_Alternative(self, arg)

  def comment_or_newline(self, arg):
    return ABNF_None(self, arg)

  def definition(self, arg):
    def_name, def_oper, def_val = arg
    #print(f"DEF {def_name.value} => {def_val} ")
    # TODO : handle =/ operator ;D
    self.RULES[def_name.value] = def_val
    return f"DEF {def_name.value}"

def _tree_str_(t):
  s=f'[{t.data}]\n'
  for ch in t.children:
    s+= " " + str(ch)
  return s

def _token_str_(t):
  return f"{t.type:10} => {t.value}"

def abnf_to_tree(abnf_data):
  parser = lark.Lark(grammar=open("abnf_gramar.lark").read())
  tree = parser.parse(abnf_data)
  #lark.Tree.__str__ = _tree_str_
  #lark.Token.__str__ = _token_str_
  #print(tree.pretty())
  return tree

def process_rules(abnf_data):
  tree = abnf_to_tree(abnf_data)
  trans = ABNFTransformer()
  obj = trans.transform(tree)
  return trans.RULES