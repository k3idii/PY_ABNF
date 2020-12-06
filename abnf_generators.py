"""
  Classes to generate ABNF defined content
"""
import random
import re


ALMOST_INFINITY = 42 # ROTFL

def _flip_the_coin():
  return random.randint(0,1)

class MyLazyResolver:
  """ Proxy class, used when the resolve of sumbol/rule fail (not yet parsed ^_^)
  """
  lazy = True # to be able to check if this is lazy reference

  def __init__(self, src, name):
    self.src = src
    self.name = name

  def __repr__(self):
    val = self.src.get(self.name, None)
    if val is not None:
      return repr(val)
    return f"<LAZY-REF to={self.name} />"

  def generate(self):
    """ Try to resolve symbol -> generate bytes  """
    val = self.src.get(self.name, None)
    assert val is not None, "FAIL TO RESOLVE lazy reference to : {self.name}"
    return val.generate()




class ABNF_Generator:
  """ Parent class for all sub-classes
  """
  format_str = '<???>'
  def __init__(self, ctx, arg, *other):
    self.ctx = ctx
    self.arg = arg
    self.setup(*other)
    self.max_attempts = 10

  def setup(self, *_):
    pass

  def _resolve(self, varname, lazy=True):
    val = self.ctx.RULES.get(varname, None)
    if val == None:
      if lazy:
        return MyLazyResolver(self.ctx.RULES, varname)
      else:
        return None
    else:
      return val

  def generate(self):
    """ Generate bytes value """
    for _i in range(self.max_attempts):
      chunk = self._gen()
      chunk = self.validate(chunk)
      if chunk is not None:
        return chunk
    raise Exception("I was not able to generate valid data @ " + str(self.__class__))

  def validate(self, data):
    """ perform data (bytes) validation ... just in case """
    return data

  def _gen(self):
    raise Exception("Implement Me" + str(self.__class__))

  def __repr__(self):
    return self.format_str.format(self=self)


class ABNF_None(ABNF_Generator):
  format_str = "<NONE/>"

  def _gen(self):
    return b""


class ABNF_AbstractRepeat(ABNF_Generator):
  format_str = "<REPEAT range='{self.repeat_a} ... {self.repeat_b}'>{self.subject}</REPEAT>"
  repeat_a = 0
  repeat_b = 0
  fmt = ''
  subject = None

  def setup(self, *_):
    self.fmt, self.subject = self._extract()
    self._parse_repeate()

  def _extract(self):
    raise Exception("Implement extractor !")

  def _parse_repeate(self):
    expr = re.compile('(?P<a>[0-9]*)(?P<star>[*]?)(?P<b>[0-9]*)')
    mobj = expr.match(self.fmt)
    _a, star, _b = mobj.groups()
    #print(f" [{a}] .{star:2}. [{b}] ")
    if star == '': #  3XX
      self.repeat_a = int(_a)
      self.repeat_b = int(_a)
    else:
      if _a == '': #  *3XX
        self.repeat_a = 0
      else:       
        self.repeat_a = int(_a)
      if _b == '': # 3*XX
        self.repeat_b = ALMOST_INFINITY
      else: 
        self.repeat_b = int(_b)
    assert self.repeat_a <= self.repeat_b, "Invalid repeat statement !"
    
  def _gen(self):
    #print("GENERATE", self.__class__, self.arg )
    size = 1
    if self.repeat_a == self.repeat_b:
      size = self.repeat_b
    else:
      size = random.randint(self.repeat_a, self.repeat_b)
    return b''.join( self.subject.generate() for _ in range(size) )



class ABNF_Repeat(ABNF_AbstractRepeat):  
  def _extract(self):
    expr = re.compile('(?P<fmt>[0-9*]+)(?P<varname>[A-Z][A-Z0-9-]*)')
    mobj = expr.match(self.arg)
    #print(mobj, mobj.groups())
    fmt, varname = mobj.groups()
    return fmt, self._resolve(varname)


class ABNF_Group(ABNF_AbstractRepeat):
  def _extract(self):
    bra, child, _ket = self.arg
    fmt = '1' # default - repeat ONCE
    if len(bra) > 1:
      fmt = bra[:-1]
    return fmt, child


class ABNF_Primitive(ABNF_Generator):
  name = '<??>'
  format_str = "<{self.name} arg='{self.arg}' />"


class ABNF_FixString(ABNF_Primitive):
  name = "STRING"
  def setup(self, *_):
    self.arg = self.arg[1:-1] # STRIP QUOTES
    # ? self.arg = self.arg.strip('"')

  def _gen(self):
    return self.arg.encode()


class ABNF_NumString(ABNF_Primitive):
  name = "STRING-CODE"
  encoding_map = {
    'd' : 10,
    'x' : 16,
    'b' : 2,
  }

  #def setup(self, base):
  #  self.base = base
  def setup(self, *_):
    encoding = self.arg[1].lower()
    self.fmt = self.arg[2:] # skip %X prefix
    self.base = self.encoding_map.get(encoding, None)
    assert self.base is not None, "Unknown base !"

  def _gen(self):
    retval = []
    # worst case: xx-xx.xx.xx-xx.xx 
    for part in self.fmt.split('.'):
      if '-' in part:
        a,b = part.split('-')
        val = random.randint(int(a,self.base), int(b,self.base))
      else:
        val = int(part, self.base)
      retval.append(val)  
    return bytes(retval)
    
class ABNF_Reference(ABNF_Primitive):
  name = "REF"
  #format_str = "<{self.name} to='{self.arg}'/>"
  resolve_repr = True

  def __repr__(self):
    if self.resolve_repr:
      val = self._resolve(self.arg, lazy=False)
      if val is not None:
        return repr(val)
    return f"<{self.name} to='{self.arg}'/>"

  def _gen(self):
    return self._resolve(self.arg).generate()
    #return f"REF TO {self.arg}".encode()


class ABNF_List(ABNF_Generator):
  def __repr__(self):
    inner = '  '.join(map(str,self.arg))
    return f"<ITEMS> {inner} </ITEMS>"

  def _gen(self):
    return b''.join(x.generate() for x in self.arg)


class ANBF_Optional(ABNF_Generator):
  format_str = "<OPTIONAL> {self.arg} </OPTIONAL>"
  def setup(self, *_):
    # arg = BRA ... VALUE ... KET 
    #       ---------^
    self.arg = self.arg[1]

  def _gen(self):
    if _flip_the_coin():
      return self.arg.generate()
    else:
      return b''

class ABNF_Alternative(ABNF_Generator):
  format_str = "<ALT><OPT id=1>  {self.arg[0]} </OPT><!--OR {self.arg[1]} --><OPT id=2> {self.arg[2]} </OPT></ALT>"

  def setup(self, *_):
    # arg = OPT1 <alt-operator> OPT2
    self.options = [ self.arg[0] , self.arg[2] ]

  def _gen(self):
    if _flip_the_coin():
      return self.options[0].generate()
    else:
      return self.options[1].generate()


class ABNF_Definition(ABNF_Generator):
  """ To be ale to control top-level validator/etc
  """
  format_str = "<DEF name='{self.name}'>{self.arg}</DEF>"

  def setup(self, name, *_):
    self.name = name

  def _gen(self):
    return self.arg.generate()

