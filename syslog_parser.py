import abnf_parser



if __name__ == '__main__':

  abnf_data = open('syslog.abnf','r').read()
  rules = abnf_parser.process_rules(abnf_data)

  test = rules['SYSLOG-MSG']

  #for name,value in rules.items():
  #  print(name)

  #print(test)

  rules['UTF-8-STRING'].validate = lambda x: b'hack!'

  for i in range(1):
    print(test.generate())


#print(o)

