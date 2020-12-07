"""
  Classes to generate ABNF defined content


  TODO 1: try to re-write this to a form of dict-of-lambdas to decreas overhead
  TODO 2: try to re-write this to a linear (not recursive) form

"""
import random
import re


ALMOST_INFINITY = 42 # ROTFL
MAX_DEPTH = 100

MADNESS_FACTOR = 20

def _flip_the_coin():
  return random.randint(0,1)

def _random_range(a,b):
  return a + int((b-a)/MADNESS_FACTOR)

def extract_repeat_fmt(entry):
  """ exctact format and varname from repeat-var statement """
  expr = re.compile('(?P<fmt>[0-9*]+)(?P<varname>[A-Za-z][A-Za-z0-9-]*)')
  mobj = expr.match(entry)
  assert mobj is not None, "Invalid repeat format !?"
  return mobj.groups()

def parse_repeate_string(fmt, rnd_func=None):
  """ extract range (a,b) from range/repeat format.
      Optionally takes custom random range generator.
      Returns callable, that will return number matching rule .
      Infinity -> see ALMOST_INFINITY variable
  """
  expr = re.compile('(?P<a>[0-9]*)(?P<star>[*]?)(?P<b>[0-9]*)')
  mobj = expr.match(fmt)
  _a, star, _b = mobj.groups()
  #print(f" [{a}] .{star:2}. [{b}] ")
  repeat_a = 0
  repeat_b = 0
  if rnd_func is None:
    rnd_func = lambda a,b,*arg: random.randint(a, b)
  if star == '': #  3XX , exac repeat
    return lambda *arg: int(_a)
  else:
    if _a == '': #  *3XX
      repeat_a = 0
    else:       
      repeat_a = int(_a)
    if _b == '': # 3*XX
      repeat_b = ALMOST_INFINITY if ALMOST_INFINITY > repeat_a else repeat_a + 1
    else: 
      repeat_b = int(_b)
  assert repeat_a <= repeat_b, "Invalid repeat statement !"
  return lambda *arg: rnd_func(repeat_a, repeat_b, *arg)

def numeric_string_generator(arg):
  """  Return function generating valid value.
  Input := fmt : %XAA-BB.CC.DD ... ; dot-separated values   
  """
  base = {'b':2,'d':10,'x':16}.get(arg[1])
  conv = lambda x: int(x, base)
  if "-" in arg or "." in arg:
    def _tmp(token):
      if '-' in token:
        args = list(map(conv,token.split('-')))
        return lambda : random.randint(*args)
      else:
        val = conv(token)
        return lambda : val
    parts = map(_tmp, arg[2:].split("."))
    return lambda : bytes(x() for x in parts)
  else:
    val = bytes([conv(arg[2:])])
    return lambda : val


class MyLazyResolver:
  """ Proxy class, used when the resolve of sumbol/rule fail (not yet parsed ^_^)
  """
  lazy = True # to be able to check if this is lazy reference

  def __init__(self, ctx, name):
    self.ctx = ctx
    self.name = name

  def __repr__(self):
    #val = self.src.get(self.name, None)
    #if val is not None:
    #  return repr(val)
    return f"<LAZY-REF to={self.name} />"

  def generate(self):
    """ Try to resolve symbol -> generate bytes  """
    val = self.ctx.get_rule(self.name, soft_fail=True)
    assert val is not None, f"FAIL TO RESOLVE lazy reference to : {self.name}"
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

  def can_go_deeper(self):
    #print("DEPTH ?? : ",self.ctx._depth )
    if self.ctx._depth > MAX_DEPTH:
      return False
    return True

  def setup(self, *_):
    pass

  def _resolve(self, varname, lazy=True):
    val = self.ctx.get_rule(varname, soft_fail=True)
    if val is None:
      if lazy:
        return MyLazyResolver(self.ctx, varname)
      else:
        return None
    else:
      return val

  def generate(self):
    """ Generate bytes value """
    #print(">> DEEPER >> " , self.ctx._depth , str(self) ) 
    if not self.can_go_deeper():
      return b''
    for _i in range(self.max_attempts):
      self.ctx._depth += 1
      chunk = self._gen()
      self.ctx._depth -= 1
      chunk = self.validate(chunk)
      if chunk is not None:
        #print("<<")
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
  repeat_gen = None
  fmt = ''
  subject = None

  def setup(self, *_):
    self.fmt, self.subject = self._extract()
    self.repeat_gen = parse_repeate_string(self.fmt)
    #      ^--- callable that will return int

  def _extract(self):
    raise Exception("Implement extractor !")

  def _gen(self):
    #print("GENERATE", self.__class__, self.arg )
    size = self.repeat_gen()
    return b''.join( self.subject.generate() for _ in range(size) )


class ABNF_Repeatrule(ABNF_AbstractRepeat):  
  def _extract(self):
    fmt, varname = extract_repeat_fmt(self.arg)
    return fmt, self._resolve(varname)


class ABNF_Group(ABNF_AbstractRepeat):
  def _extract(self):
    bra, child, _ket = self.arg
  #  ^-----------^----- Tokens !
    fmt = '1' # default - repeat ONCE
    if len(bra.value) > 1:
      fmt = bra.value[:-1]
    return fmt, child


class ABNF_Primitive(ABNF_Generator):
  name = '<??>'
  format_str = "<{self.name} arg='{self.arg}' />"


class ABNF_EscString(ABNF_Primitive):
  name = "STRING"
  def setup(self, *_):
    self.arg = self.arg[1:-1] # STRIP QUOTES ("" or <>)
    # ? self.arg = self.arg.strip('"')

  def _gen(self):
    return self.arg.encode()


class ABNF_NumString(ABNF_Primitive):
  name = "STRING-CODE"
  gen_fn = None

  def setup(self, *_):
    self.gen_fn = numeric_string_generator(self.arg)

  def _gen(self):
    return self.gen_fn()

class ABNF_Reference(ABNF_Primitive):
  name = "REF"
  #format_str = "<{self.name} to='{self.arg}'/>"
  resolve_repr = True

  def __repr__(self):
    #if self.resolve_repr:
    #  val = self._resolve(self.arg, lazy=False)
    #  if val is not None:
    #    return repr(val)
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
    if _flip_the_coin() and self.can_go_deeper():
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


class ABNF_Definition:
  """ To be ale to control top-level validator/etc
  """

  def __init__(self, ctx, arg, name):
    self.ctx = ctx
    self.name = name
    self.arg = arg
    
  def generate(self):
    return self.arg.generate()

  def __repr__(self):
    self.ctx._depth = 0
    return f"<DEF name='{self.name}'>{self.arg}</DEF>"

