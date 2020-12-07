""" Parsing ABNF rules """
import lark
import abnf_generators


class ABNFContext:
  """ Hold context (rules) for parsing & generating """
  RULES = None

  def __init__(self):
    self.rules = dict()

  def add_rule(self, name, value):
    """ add new rule """
    self.rules[name] = value

  def alter_rule(self, name, value):
    """ Modify existing rule """
    raise Exception("Implement me")

  def get_rule(self, name, soft_fail=True):
    """ Get rule by name """
    val = self.rules.get(name, None)
    if soft_fail:
      return val
    if val is None:
      raise Exception(f"Rule [{name}] not found ")

  def get_rules(self):
    """ get all rules """
    return self.rules

class ABNFTransformer(lark.Transformer):
  """ Modified tree transformer """
  _ctx = None
  _mod = None

  def initialize(self, mod):
    """ initialize local vars """
    self._mod = mod
    self._ctx = ABNFContext()

  def get_rules(self):
    return self._ctx.get_rules()

  def get_context(self):
    return self._ctx

  def __unused__now_primitive(self, node):
    node = node[0]
    if node.type == 'RULENAME':
      return self._mod.ABNF_Reference(self, node.value)
    #elif node.type == 'HEX_STRN':
    #  return self._mod.ABNF_NumString(self, node.value, 16)
    #elif node.type == 'DEC_STRN':
    #  return self._mod.ABNF_NumString(self, node.value, 10)
    #elif node.type == 'BIN_STRN':
    #  return self._mod.ABNF_NumString(self, node.value, 2)
    elif node.type in ['BIN_STRN', 'DEC_STRN', 'HEX_STRN']:
      return self._mod.ABNF_NumString(self, node.value)
    elif node.type == 'ESCAPED_STRING':
      return self._mod.ABNF_FixString(self, node.value)
    elif node.type == 'REP_RULE':
      return self._mod.ABNF_Repeat(self, node.value)
    s = f"{node.type}({node.value})"
    raise Exception(s)

  def esc_string(self, arg):
    return self._mod.ABNF_EscString(self._ctx, arg[0].value)

  def num_string(self, arg):
    return self._mod.ABNF_NumString(self._ctx, arg[0].value)

  def ref_rule(self, arg):
    return self._mod.ABNF_Reference(self._ctx, arg[0].value)

  def rep_ref_rule(self, arg):
    return self._mod.ABNF_Repeatrule(self._ctx, arg[0].value)

  def group(self, arg):
    return self._mod.ABNF_Group(self._ctx, arg)

  def optional(self, arg):
    return self._mod.ANBF_Optional(self._ctx, arg)

  def list_of_primitives(self, arg):
    return self._mod.ABNF_List(self._ctx, arg)

  def concat_statement(self, arg):
    return self._mod.ABNF_List(self._ctx, arg)

  def multiline_spec(self, arg):
    return self._mod.ABNF_List(self._ctx, arg)

  def alternative(self, arg):
    return self._mod.ABNF_Alternative(self._ctx, arg)

  def comment_or_newline(self, arg):
    return self._mod.ABNF_None(self._ctx, arg)

  def definition(self, arg):
    def_name, def_oper, def_val = arg
    # TODO : handle =/ operator ^_^
    if def_oper != '=':
      raise Exception("Operator not implemented")
    # parse node
    obj = self._mod.ABNF_Definition(self._ctx, def_val, def_name)
    # add to list
    self._ctx.add_rule(def_name.value, obj)
    # return into tree
    return obj


def _print_tree(tree):

  def _tree_str_(tok):
    ret = f'[{tok.data}]\n'
    for chx in tok.children:
      ret += " " + str(chx)
    return ret

  def _token_str_(tok):
    return f"{tok.type:10} => {tok.value}"

  lark.Tree.__str__ = _tree_str_
  lark.Token.__str__ = _token_str_

  print(tree.pretty())


def _tokenize_abnf(abnf_data):
  parser = lark.Lark(grammar=open("abnf_gramar.lark").read())
  tree = parser.parse(abnf_data)
  return tree

def process_rules(abnf_data, module=None):
  if module is None:
    module = abnf_generators
  tree = _tokenize_abnf(abnf_data)
  trans = ABNFTransformer()
  trans.initialize(module)
  trans.transform(tree)
  return trans.get_context()

