import sys
import argparse

import abnf_parser
from timeit import default_timer as timer

def main(args):
  """ main function """
  abnf_data = open(args.filename,'r').read()

  extra_mod = None
  if args.mod:
    extra_mod = __import__(args.mod)
    print(f"Warning: Using alternative generators from : {args.mod} / {extra_mod}")
  context = abnf_parser.process_rules(abnf_data, module=extra_mod)

  sys.setrecursionlimit(0x1FFF)

  if args.list_rules:
    print('Parsed rules: ',', '.join(context.get_rules().keys()))

  if args.rule is None:
    return ":-("
  rulename = args.rule
  obj = context.get_rule(rulename)
  if obj is None:
    raise Exception(f"Rule [{rulename}] not found !")
  if args.string:
    print(" --- RULE --->")
    print(obj)
    print(" <--- RULE ---")
  
  start = timer()
  for cnt in range(args.generate):
    binary = obj.generate() 
    if args.out:
      out_fn = args.out.format(n=cnt)
      print(f" > Saved to {out_fn}")
      open(out_fn, "ab").write(binary)
    else:
      print(binary)
  end = timer()
  time_diff = end - start
  if args.generate > 0:
    print(f"Generated {cnt} in {time_diff:.6f} seconds")


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description=""" ABNF Ruleset parser && generator """)
  parser.add_argument(
    "filename", 
    help="ABNF Definition file"
  )
  parser.add_argument(
    '-r', '--rule',
    help = "Rule name to operate on",
    #action = 'append',
    #default = [],
  )
  parser.add_argument(
    '-l', '--list',
    help = "List parsed rules",
    default = False,
    action = "store_true",
    dest = 'list_rules'
  )
  parser.add_argument(
    '-s', '--string',
    help = "Output string-representation of rule",
    default = False,
    action = "store_true",
  )
  parser.add_argument(
    '-g','--generate',
    metavar='N',
    type = int,
    help = "Generate N binary data (based on rule definition). Use 1 to get .. one :)",
    default = 0,
  )
  parser.add_argument(
    '-o', '--out',
    metavar = "outfile",
    help = """
    Optional output file name (if not provided, binary goes to stdout :P).
    You can use {n} placeholder to put each sample to different file.
    """,
    default = None
  )
  parser.add_argument(
    '--mod',
    metavar = 'module-name.py',
    help = "Use non-standard module for gerators (see alter.py example)",
    default = None,
  )

  main( parser.parse_args())


