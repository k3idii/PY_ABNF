import abnf_parser



if __name__ == '__main__':

  abnf_data = open('syslog.abnf','r').read()
  rules = abnf_parser.process_rules(abnf_data)

  # get the definition
  test = rules['SYSLOG-MSG']

  #for name,value in rules.items():
  #  print(name)

  # print the XML-like definition 
  print(test)

  # example how to override generated value
  rules['UTF-8-STRING'].validate = lambda x: b'hack!'

  # generate few payloads 
  for i in range(1):
    print(test.generate())


#print(o)

