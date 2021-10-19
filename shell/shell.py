#! /usr/bin/env python3

import os, sys, re

def setPS1():
    # If PS1 environment variable is defined, use that value
    if 'PS1' in os.environ:
        return os.environ["PS1"]
    # Otherwise, make PS1 variable the default dollar sign
    else:
        return '$ '
    
def runChildProcess(args):
    if "/" in args[0]:
        os.execve(args[0], args, os.environ)
    else:
        for dir in re.split(':', os.environ["PATH"]):
            try:
                program = "%s/%s" % (dir, args[0])
                os.execve(program, args, os.environ)
            except Exception:
                pass
        errorMessage = args[0] + ": command not found\n"
        os.write(2, errorMessage.encode())
    sys.exit(0)
    
def redirectOutput(args):
    if args[-1] == "&":
        wait = False
        args.pop(-1)
    else:
        wait = True
    rc = os.fork()
    if rc < 0:
        os.write(2, "FORK FAILED".encode())
        sys.exit(0)
    elif rc == 0:
        os.close(1) # Close standard output
        sys.stdout = open(args[-1], "w") # Set output to desired location
        os.set_inheritable(1, True)
        
        args = args[:args.index(">")]
        runChildProcess(args)
    else:
        if wait:
            os.wait()
        
def redirectInput(args):
    if args[-1] == "&":
        wait = False
        args.pop(-1)
    else:
        wait = True
    rc = os.fork()
    if rc < 0:
        os.write(2, "FORKFAILED".encode())
        sys.exit(0)
    elif rc == 0:
        os.close(0) # Close standart input
        sys.stdin = open(args[-1], "r") # Set input from desired location
        os.set_inheritable(0, True)
        
        args = args[:args.index("<")]
        runChildProcess(args)
    else:
        if wait:
            os.wait()
    
def handleChildProcess(args):
    if args[-1] == "&":
        wait = False
        args.pop(-1)
    else:
        wait = True
    rc = os.fork()
    if rc < 0: # Failed fork
        os.write(2, "FORK FAILED".encode())
        sys.exit(1)
    elif rc == 0: # This is the child process to run entered command
        runChildProcess(args)
    else: # This is the parent process waiting for child execution to complete
        if wait:
            os.wait()

def handlePiping(args):
    pr, pw = os.pipe()
    for fd in (pr, pw):
        os.set_inheritable(fd, True)
    rc = os.fork()
    if rc < 0:
        os.write(2, "FORK FAILED".encode())
        sys.exit(1)
    elif rc == 0: # Child process to run first part of pipe
        os.close(1)
        os.dup(pw)
        os.set_inheritable(1, True)
        for fd in (pr, pw):
            os.close(fd)
        args = args[:args.index("|")]
        runChildProcess(args)
        sys.exit(0)
    else: # Parent process waiting for input from pipe
        os.close(0)
        os.dup(pr)
        os.set_inheritable(0, True)
        for fd in (pw, pr):
            os.close(fd)
            
        args = args[args.index("|") + 1:]
        if "|" in args:
            sys.stdin = sys.__stdin__
            sys.stdout = sys.__stdout__
            pr, pw = os.pipe()
            for fd in (pr, pw):
                os.set_inheritable(fd, True)
            rc = os.fork()
            if rc == 0:
                os.close(1)
                os.dup(pw)
                os.set_inheritable(1, True)
                for fd in (pr, pw):
                    os.close(fd)
                args = args[:args.index("|")]
                runChildProcess(args)
                sys.exit(0)
            else:
                os.close(0)
                os.dup(pr)
                os.set_inheritable(0, True)
                for fd in (pw, pr):
                    os.close(fd)
                args = args[args.index("|")+1:]
                
                runChildProcess(args)
        else:
            runChildProcess(args)

while True: # Continuously ask for commands
    prompt = setPS1()
    
    try:
        command = input(prompt)
        args = command.split()
    except EOFError:
        sys.exit(1)
    
    if command == "": # If no input, ask again
        continue
    elif args[0] == "exit": # If user types exit, then exit
        sys.exit(0)
    elif args[0] == "cd": # Change to specified directory
        os.chdir(args[1])
    elif "|" in args: # Piping requested
        handlePiping(args)
    elif ">" in args: # Redirect output
        redirectOutput(args)
    elif "<" in args: # Redirect input
        redirectInput(args)
    else: # look for command in PATH
        handleChildProcess(args)
