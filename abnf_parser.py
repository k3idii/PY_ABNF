import lark

import abnf_generators


class ABNFTransformer(lark.Transformer):
  RULES = dict()
  _mod = None

  def set_module(self, mod):
    self._mod = mod

  def primitive(self, node):
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

  def group(self, arg):
    return self._mod.ABNF_Group(self, arg)

  def optional(self, arg):
    return self._mod.ANBF_Optional(self, arg)

  def list_of_primitives(self, arg):
    return self._mod.ABNF_List(self, arg)

  def concat_statement(self, arg):
    return self._mod.ABNF_List(self, arg)

  def multiline_spec(self, arg):
    return self._mod.ABNF_List(self, arg)

  def alternative(self, arg):
    return self._mod.ABNF_Alternative(self, arg)

  def comment_or_newline(self, arg):
    return self._mod.ABNF_None(self, arg)

  def definition(self, arg):
    def_name, def_oper, def_val = arg
    # TODO : handle =/ operator ^_^
    if def_oper != '=':
      raise Exception("Operator not implemented")
    obj = self._mod.ABNF_Definition(self, def_val, def_name)
    self.RULES[def_name.value] = obj
    return obj


def print_tree(tree):

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


def tokenize_abnf(abnf_data):
  parser = lark.Lark(grammar=open("abnf_gramar.lark").read())
  tree = parser.parse(abnf_data)
  return tree

def process_rules(abnf_data, module=None):
  if module is None:
    module = abnf_generators
  tree = tokenize_abnf(abnf_data)
  trans = ABNFTransformer()
  trans.set_module(module)
  trans.transform(tree)
  return trans.RULES

  