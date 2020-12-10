import abnf_parser



if __name__ == '__main__':

  import alter

  abnf_data = open('syslog.abnf','r').read()
  context = abnf_parser.process_rules(abnf_data)

  # get the definition
  test = context.get_rule('SYSLOG-MSG')

  #for name,value in rules.items():
  #  print(name)

  # print the XML-like definition
  print(test)

  # example how to override generated value
  context.get_rule('UTF-8-STRING').validate = lambda x: b'hack!'
  context.get_rule('TIME-HOUR').generate = lambda : b'12'
  context.get_rule('MSG-ANY').generate = lambda : b'message-ascii'
  context.get_rule('MSG-UTF8').generate = lambda : 'message-ółżkę-UTF8'.encode()
  
  #test = context.get_rule('MSG-UTF8')

  # generate few payloads
  for i in range(1):
    print(test.generate())


#print(o)

