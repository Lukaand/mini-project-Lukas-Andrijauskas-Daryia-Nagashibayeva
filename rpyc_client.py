import rpyc
import sys
 
if len(sys.argv) < 2:
   exit("Usage {} SERVER".format(sys.argv[0]))
 
server = sys.argv[1]
try:
   conn = rpyc.connect(server,18813)
   if(not conn.root.isrunning()):
      n = input('The number of processes: ')
      conn.root.start_processes(n)
      
   cmd = ''
   print("status, time-p, time-cs, debug")
   while(conn.root.isrunning() and cmd != 'exit'):
      cmd = input("Input the command: ")
      conn.root.execute_command(cmd)
   
except:
   raise Exception("Fail")



 
 