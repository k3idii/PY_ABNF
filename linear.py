"""
  Classes to generate ABNF defined content
  Attempt to do this non-recursive way

"""
import random
import re
from abnf_generators import parse_repeate_string, extract_repeat_fmt, numeric_string_generator
import itertools



def _flip_the_coin():
  return random.randint(0,1)


class SingleEntity:
  terminal = False
  format_str = "<UNK/>"

  def __init__(self, ctx, arg):
    self.ctx = ctx
    self.arg = arg
    self.setup()

  def setup(self):
    pass

  def __repr__(self):
    return self.format_str.format(self=self)


class TerminalEntity(SingleEntity):
  terminal = True
  name = '<??>'
  format_str = "<{self.name} arg='{self.arg}' />"

  value = b''

class DummyTerminal(TerminalEntity):
  format_str = "<DUMMY {self.arg} />"

  @property
  def value(self):
    return b'[' + self.arg + b']'


class ComplexEntity(SingleEntity):
  terminal = False

  def generate(self):
    """ generate children elements """
    raise Exception(f"Implement me {self.__class__}")


class RuleRef(ComplexEntity):
  """ Reference to rule """
  format_str = '<REF to="{self.arg}" />'

  def generate(self):
    """ Try to resolve symbol """
    #yield DummyTerminal(None,self.arg.encode())
    # skip Rule Def. Generator
    yield self.ctx.get_rule(self.arg).arg


class ABNF_Generator(ComplexEntity):
  pass

class ABNF_None(TerminalEntity):
  format_str = "<NONE/>"



class ABNF_AbstractRepeat(ABNF_Generator):
  format_str = '<REPEAT what="{self.what}" range="{self.fmt}">{self.subject}</REPEAT>'
  repeat_gen = None
  fmt = ''
  what = "??"
  subject = None

  def setup(self):
    self.fmt, self.subject = self._extract()
    self.calc_size = parse_repeate_string(self.fmt)

  def _extract(self):
    raise Exception("Implement extractor !")

  def generate(self):
    #print("GENERATE", self.__class__, self.arg )
    size = self.calc_size()
    #print(f"Will return {size} elements")
    #size = 1
    for _ in range(size):
      yield self.subject
    

class ABNF_Repeatrule(ABNF_AbstractRepeat):  
  what = "RULE"
  def _extract(self):
    fmt, varname = extract_repeat_fmt(self.arg)
    return fmt, RuleRef(self.ctx, varname)


class ABNF_Group(ABNF_AbstractRepeat):
  what="GROUP"
  def _extract(self):
    bra, child, _ket = self.arg
  #  ^-----------^----- Tokens !
    fmt = '1' # default - repeat ONCE
    if len(bra.value) > 1:
      fmt = bra.value[:-1]
    return fmt, child


class ABNF_Reference(RuleRef):
  pass


class ABNF_List(ABNF_Generator):
  format_str = "<LIST> {self.arg} </LIST>"

  def generate(self):
    for elem in self.arg:
      yield elem

class ANBF_Optional(ABNF_Generator):
  format_str = "<OPTIONAL> {self.arg} </OPTIONAL>"
  def setup(self, *_):
    # arg = BRA ... VALUE ... KET 
    #       ---------^
    self.arg = self.arg[1]

  def generate(self): 
    if 0 and _flip_the_coin() and self.ctx.is_this_too_much():
      yield self.arg

class ABNF_Alternative(ABNF_Generator):
  format_str = "<ALT><OPT id=1>  {self.arg[0]} </OPT><!--OR {self.arg[1]} --><OPT id=2> {self.arg[2]} </OPT></ALT>"

  def setup(self, *_):
    # arg = OPT1 <alt-operator> OPT2
    self.options = [ self.arg[0] , self.arg[2] ]

  def generate(self):
    if _flip_the_coin():
      yield self.options[0]
    else:
      yield self.options[1]




class ABNF_EscString(TerminalEntity):
  name = "STRING"
  def setup(self, *_):
    self.arg = self.arg[1:-1] # STRIP QUOTES ("" or <>)
    # ? self.arg = self.arg.strip('"')
    self.value = self.arg.encode()


class ABNF_NumString(TerminalEntity):
  name = "STRING-CODE"
  gen_fn = None

  def setup(self, *_):
    self.gen_fn = numeric_string_generator(self.arg)
    #print("VAL ", self.arg, "=>", self.gen_fn())

  @property
  def value(self):
    val = self.gen_fn()
    #print(f"Call to VALUE {self.arg} -> {val}")
    return val


class ABNF_Definition:
  """ To be ale to control top-level validator/etc
  """

  def __init__(self, ctx, arg, name):
    self.ctx = ctx
    self.name = name
    self.arg = arg
    self.evaluated = 0
    
  def _evaluate(self, element):
    #print(f" -> Check if evaluate {element}")
    if element.terminal:
      #print(f"  => NO :-) ")
      yield element
    else:
      self.evaluated += 1 
      #print(f"  => YES ... ")
      for new_elem in element.generate():
        #print(f"    -> VALUE: {new_elem}")
        yield new_elem

  def generate(self):
    #import yaml
    children = [self.arg]
    self.evaluated = 1

    TOO_MUCH_LEVEL = 100

    while self.evaluated > 0:
      self.evaluated = 0
      #print("\nLOOP ==============> ")
      #print('BEFORE:')
      #print(yaml.dump(list(map(lambda x:str(x.__class__), children) )))
      new_arr = []
      for child in children:
        for new_elem in self._evaluate(child):
          new_arr.append(new_elem)
      #print(f" Count : old:{len(children)} + eval:{self.evaluated} = new:{len(new_arr)} ")
      children = new_arr
      self.ctx.is_this_too_much = lambda :  0 and len(new_arr) > TOO_MUCH_LEVEL
      #print("<==============LOOP\n")

    return b''.join(child.value for child in children)


  def __repr__(self):
    return f"<DEF name='{self.name}'>{self.arg}</DEF>"

