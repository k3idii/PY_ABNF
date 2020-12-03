import lark
import abnf_parser



if __name__ == '__main__':

  abnf_data = open('syslog.abnf','r').read()
  rules = abnf_parser.process_rules(abnf_data)
  
  test = rules['SYSLOG-MSG']
  
  for i in range(20):
    print(test.generate())


#print(o)


