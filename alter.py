"""
  Alternative implelemtation of ABNF generators.
  Lambda madness ;)
"""
import random
from abnf_generators import parse_repeate_string, extract_repeat_fmt, numeric_string_generator

import functools

cache = functools.lru_cache

def rand_range(a,b):
  print(a,'..',b)
  return random.randint(a,b)

def ABNF_None(ctx, arg):
  return cache()(lambda env : b'')

def ABNF_Reference(ctx, arg):
  return lambda env : ctx.get_rule(arg)(env)

def ABNF_List(_, arg):
  #print(arg)
  return lambda env : b''.join(_x(env) for _x in arg)

def ANBF_Optional(ctx, arg):
  return lambda env : env.optional(arg[1])(env)

def ABNF_EscString(_, arg):
  return cache()(lambda env : arg[1:-1].encode())

def ABNF_Repeatrule(ctx, arg):
  #print(arg)
  fmt, varname = extract_repeat_fmt(arg)
  rng_gen = parse_repeate_string(fmt)
  #print(_a, _b, varname)
  return lambda env : b''.join( ctx.get_rule(varname)(env) for _ in range(rng_gen()))

def ABNF_Alternative(ctx, arg):
  return lambda env : env.select(arg[0], arg[2])(env)

def ABNF_Group(ctx, arg):
  sval = arg[0].value # 'xxxx(' <- format
  if len(sval) == 1: 
    return lambda env : arg[1](env)
  rnd_func = lambda a,b, env : env.rnd(a,b)
  rng_gen = parse_repeate_string(sval[:-1], rnd_func )
  return lambda env : b''.join( arg[1](env) for _ in range(rng_gen(env)))

def ABNF_NumString(ctx, arg):
  _tmp = numeric_string_generator(arg)
  return lambda env : _tmp()


class MicroEnv: # all possible decisions go here.
  depth = 0
  limit = 1000

  def optional(self, callme):
    #print(f"Decision {self.depth}" )
    if 1 or self.depth < self.limit and random.randint(0,1):
      return callme
    else:
      return lambda env : b''

  def select(self, *a):
    return random.choice(a)
  
  def rnd(self, a, b):
    #print(f"Range @ {self.depth}, {a} ... {b} ") 
    if self.depth > self.limit:
      if a == 0:
        return random.randint(0,1)
      b = a + int( (b-a)*0.1 )
    return random.randint(a,b)

  def __add__(self, x): 
    """ Super dirty hack to track depth :) """
    self.depth += 1
    return self



class ABNF_Definition:

  def __init__(self, ctx, arg, name):
    self.name = name
    self.child = arg

  def __call__(self, env):
    return self.child(env+1)

  def generate(self):
    env = MicroEnv()
    return self.child(env)


