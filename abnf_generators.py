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

def fix_self(fn):
  def _proxy(*self):
    return fn()
  return _proxy

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
  """  Return function generating valid binary string.
  Input := fmt : %XAA-BB.CC.DD ... ; dot-separated values
  X = { d, b, x }
  """
  base = {'b':2,'d':10,'x':16}.get(arg[1])
  conv = lambda x: int(x, base)
  if "-" in arg or "." in arg:
    def _tmp(token):
      if '-' in token:
        args = list(map(conv,token.split('-')))
        func = lambda : random.randint(*args)
        #print("Single args:",args, func())
      else:
        val = conv(token)
        func = lambda : val
      return func
    parts = list(map(_tmp, arg[2:].split(".")))
    #def _gen():
    #  v = list(x() for x in parts)
    #  print("Generate", parts, v)
    #  return bytes(v)
    #return _gen
    return lambda : bytes(list(x() for x in parts) )
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
    #print(f"RESOLVING {self.name}")
    val = self.ctx.get_rule(self.name, soft_fail=True)
    assert val is not None, f"FAIL TO RESOLVE lazy reference to : {self.name}"
    return val.generate()




class ABNF_Generator:
  """ Parent class for all sub-classes
  """
  format_str = '<???>'
  def __init__(self, ctx, arg):
    self.ctx = ctx
    self.arg = arg
    self.setup()
    self.max_attempts = 10

  def can_go_deeper(self):
    if self.ctx.depth > MAX_DEPTH:
      return False
    return True

  def setup(self):
    """ ? """
    pass

  def generate(self):
    """ Generate bytes value """
    #print(">> DEEPER >> " , self.ctx._depth , str(self) ) 
    if not self.can_go_deeper():
      return b''
    for _i in range(self.max_attempts):
      self.ctx.depth += 1
      chunk = self._gen()
      self.ctx.depth -= 1
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
  format_str = "<REPEAT range='{self.fmt}'>{self.subject}</REPEAT>"
  size_generator = fix_self(lambda :1) # callable, should return number of repetitions
  fmt = ''
  subject = None

  def setup(self):
    raise Exception("This is abstract class")

  def _gen(self):
    size = self.size_generator()
    return b''.join( self.subject.generate() for _ in range(size) )


class ABNF_Repeatrule(ABNF_AbstractRepeat):  
  def setup(self):
    self.fmt, self.varname = extract_repeat_fmt(self.arg)
    self.size_generator = fix_self(parse_repeate_string(self.fmt))
    self.subject = MyLazyResolver(self.ctx, self.varname)


class ABNF_Group(ABNF_AbstractRepeat):
  def setup(self):
    bra, self.subject, _ket = self.arg
  #  ^-----------^----- Tokens !
    if len(bra.value) > 1:
      self.fmt = bra.value[:-1]
      self.size_generator = fix_self(parse_repeate_string(self.fmt))
    else:
      self.fmt = "1"
      #self.size_generator is already 1


class ABNF_Primitive(ABNF_Generator):
  name = '<??>'
  format_str = "<{self.name} arg='{self.arg}' />"


class ABNF_EscString(ABNF_Primitive):
  name = "STRING"
  def setup(self):
    self.arg = self.arg[1:-1] # STRIP QUOTES ("" or <>)

  def _gen(self):
    return self.arg.encode()


class ABNF_NumString(ABNF_Primitive):
  name = "STRING-CODE"
  gen_fn = None

  def setup(self):
    self.gen_fn = numeric_string_generator(self.arg)

  def _gen(self):
    return self.gen_fn()

class ABNF_Reference(ABNF_Primitive):
  name = "REF"
  resolve_repr = True

  def __repr__(self):
    return f"<{self.name} to='{self.arg}'/>"

  def _gen(self):
    return MyLazyResolver(self.ctx, self.arg).generate()


class ABNF_List(ABNF_Generator):
  def __repr__(self):
    inner = '  '.join(map(str,self.arg))
    return f"<ITEMS> {inner} </ITEMS>"

  def _gen(self):
    return b''.join(x.generate() for x in self.arg)


class ANBF_Optional(ABNF_Generator):
  format_str = "<OPTIONAL> {self.arg} </OPTIONAL>"
  def setup(self):
    # arg = BRA ... VALUE ... KET
    #       ---------^
    self.arg = self.arg[1]

  def _gen(self):
    if _flip_the_coin() and self.can_go_deeper():
      return self.arg.generate()
    #else:
    return b''

class ABNF_Alternative(ABNF_Generator):
  format_str = "<ALT><OPT id=1>  {self.arg[0]} </OPT><!--OR {self.arg[1]} --><OPT id=2> {self.arg[2]} </OPT></ALT>"

  def setup(self):
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
    self.ctx.depth = 0
    return f"<DEF name='{self.name}'>{self.arg}</DEF>"

