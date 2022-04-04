from email import message
from multiprocessing.connection import wait
import threading
import rpyc
from rpyc.utils.server import ThreadedServer
import datetime
from functools import wraps
from multiprocessing import synchronize
from platform import processor
import _thread
from types import coroutine
import time
import random

from sympy import false, true

# -------------------------------- my code
system_start = datetime.datetime.now()
date_time = datetime.datetime.now()

processes = []
running = False
gb_time = 0

class Process:
    def __init__(self, id, name, data):
        self.id = id
        self.name = name
        self.data = data
        self.change_time = 0
        self.start_wanting_times = [random.randint(5, 20)]
        self.held_time = 10
        self.tick = 0
        self.pending_requests = []
        self.premisions = []
        self.debug = False

    def update_data(self):
        if len(self.start_wanting_times) > 0: 
            if((self.data == 'DO-NOT-WANT') and (self.tick - self.change_time >= self.start_wanting_times[0])):
                self.data = 'WANTED'
                self.start_wanting_times.pop(0)
                self.send_request()

                if self.debug:
                    changes_for_debuging(processes)
                
        if(self.data == 'WANTED'):
            h = [p[1] for p in self.premisions]
            st = True
            for i in h:
                if i == False:
                    st = False
            if st:
                self.data = 'HELD'
                self.change_time = self.tick

                if self.debug:
                    changes_for_debuging(processes)
                
        if(self.data == 'HELD' and (self.tick - self.change_time >= self.held_time)):
            self.data = 'DO-NOT-WANT'
            for pr in self.premisions:
                pr[1] = False
            if len(self.start_wanting_times) > 0:
                self.change_time = self.tick
            else:
                self.change_time = None
                
            if self.debug:    
                changes_for_debuging(processes)
    
    def clock(self):
        # program ticks evey second
        while True:
            time.sleep(1)
            self.tick += 1
            self.check_premisions()
            self.update_data()
              
    def kill(self):
        _thread.kill()
        
    def run(self):
        _thread.start_new_thread(self.clock,())
        
    def check_premisions(self):
        if self.data == "DO-NOT-WANT":
            for req in range(len(self.pending_requests)):
                pre = self.pending_requests.pop(0)
                self.send_premision(pre[0])
            
    def send_request(self):
        for p in processes:
            if p.id != self.id:
                p.pending_requests.append([self.id,self.tick])
    
    def send_premision(self, id):
        for p in processes:
            if p.id == id:
                for pp in p.premisions:
                    if pp[0] == self.id:
                        pp[1] = True
                break
            
def main(n):
    # main program function
    for p in range(int(n)):     
        processes.append(Process(p, f'p_{p}', 'DO-NOT-WANT'))
        for b in range(int(n)):
            if p != b:
                processes[-1].premisions.append([b,False])
    # start threads of all processes
    print(f"{n} processes where created ")
    for p in processes:
        print(f"{p.name}, will start to want CS in {p.start_wanting_times} s, hold for {p.held_time} s")
        p.run()
    return processes

# commands ------------------------------------------------------------------------------

def update_p_t(tm):
    print(f"Added additional request to hold the CS. Time interval (10,{tm})")
    for p in processes:
        if p.change_time == None:
            p.change_time = p.tick
        p.start_wanting_times.append(random.randint(10, tm))
        print(f"{p.name}, will start to want CS in {p.start_wanting_times} s, hold for {p.held_time} s")

def update_cs_t(tm):
    print("Updated CS held time randomly. time interval (5,{tm})")
    for p in processes:
        p.held_time = random.randint(5, tm)
        print(f"{p.name}, will start to want CS in {p.start_wanting_times} s, hold for {p.held_time} s")

def status(processes):
    # utility method to list proceeses
    for p in processes:
        str = f"{p.name}, {p.data}" 
        print(str, end="\n")
        
def show_queue(processes):
    for p in processes:
        print(f"{p.id}, pending requests {p.pending_requests}")
        print(f"pending premisions:")
        for bb in p.premisions:
            print(bb)
            
def changes_for_debuging(processes):
    
    for p in processes:
        if p.change_time == None:
            print(f"{p.id}, {p.data}, {p.premisions}, did nothing for {None}, next event in none")
        else:
            did_nothing_for = p.tick - p.change_time
            if p.data == "DO-NOT-WANT":
                if p.start_wanting_times == None:
                    print(f"{p.id}, {p.data}, {p.premisions}, did nothing for {did_nothing_for}, next event in none")
                else:
                    next = p.start_wanting_times[0] - did_nothing_for
                    print(f"{p.id}, {p.data}, {p.premisions}, did nothing for {did_nothing_for}, next event in {next}")
            elif p.data == "WANTED":
                print(f"{p.id}, {p.data}, {p.premisions}, did nothing for {did_nothing_for}, next event in")
            else:
                next = p.held_time - did_nothing_for
                print(f"{p.id}, {p.data}, {p.premisions}, did nothing for {did_nothing_for}, next event in {next}")
    print("-------------------------------")

def set_debug(pro):
    for p in pro:
        if p.debug == False:
            p.debug = True
        else:
            p.debug = False

def run_commands(inp, procs, stat):
    running = stat
    processes = procs
    cmd = inp.split(" ")

    command = cmd[0]

    if len(cmd) > 3:
        print("Too many arguments")
    # handle exit
    elif command == "exit":
        running = False
        for p in processes:
            p.kill()
        print("Program exited")
    # handle list
    
    elif command == "debug":
        try:
            set_debug(processes)
        except:
            print("Error")
            
    elif command == "status":
        try:
            status(processes)
        except: 
            print("Error")
    elif command == "time-p":
        try:
            update_p_t(int(cmd[1]))
        except:
            print("Error")
    elif command == "time-cs":
        try:
            update_cs_t(int(cmd[1]))
        except:
            print("Error")
    # handle unsupported command        
    else:
        print("Unsupported command:", inp)
            

class MonitorService(rpyc.Service):
    
    stat = False
    Processes = []

    def exposed_start_processes(self, params):
        MonitorService.Processes = main(params)
        MonitorService.stat = True
        return True
    
    def exposed_execute_command(self, params):
        print('received command from client', params)
        return run_commands(params, MonitorService.Processes, MonitorService.stat)    
            
    def on_disconnect(self, conn):
        print("\ndisconneced on {}".format(date_time))

    def on_connect(self, conn):
        print("\nconnected on {}".format(date_time))
        

    def exposed_isrunning(self):
        #print(clock_sync.isRunning())
        return MonitorService.stat


if __name__ == '__main__':
    t = ThreadedServer(MonitorService, port=18813)
    t.start()
