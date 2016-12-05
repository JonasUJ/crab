import os
os.system('cls')

import sys
import pprint
import copy
import time
time.sleep(0.05)

class Inst:

    def __init__(self, inst='', contents=[], lineno=0, line='', **kwargs):
        self.inst = inst
        self.contents = contents
        self.lineno = lineno
        self.line = line
        self.args = kwargs

    def __repr__(self):
        return '<Inst object \'%s\' at line %s that contains %s lines: %s>' % (self.line, self.lineno, len(self.contents), self.contents)


class Crab:


    def __init__(self):

        #Constants
        self.FILE_NAME = ''
        self.FILE_DIR = ''
        self.INDENTATION = 4
        self.COMMANDS = {
            'exit': self.do_exit, 
            'quit': self.do_exit, 
            'cal': self.do_cal, 
            'say': self.do_say,
            'help': self.do_help,
            'py': self.do_py, 
            'create': self.do_create, 
            'set': self.do_set, 
            'get': self.do_get, 
            'open': self.do_open,
            'func': self.do_func,
            'wait': self.do_wait,
            'int': self.do_int,
            'ask': self.do_ask,
            'repeat': self.do_repeat,
            'return': self.do_return,
            'use': self.do_use,
            'cond': self.do_cond,
            'if': self.do_if,
            'else': self.do_else,
            'len': self.do_len,
            'pass': self.do_pass
            }
        
        #Variables
        self.vars = dict()


    def error(self, errortype, msg, line, lineno):
        #Returns an error message in a tuple
        return ('ERROR', '\n%s\nLine %s\n%s\n%s' % (errortype, lineno, line.rstrip('\n'), msg))


    def handle_file(self, file_path):
        self.FILE_NAME = os.path.basename(file_path)
        self.FILE_DIR = file_path.rstrip(self.FILE_NAME)
        
        with open(file_path, 'r') as f:
            lines = f.readlines()

        self.INDENTATION = self.find_indentation_value(lines)

        parsed_lines = self.parse_lines(lines)
        if type(parsed_lines) == tuple:
            return parsed_lines[1]
        else:
            parsed_lines = [item for item in parsed_lines if item]
            #pprint.pprint(parsed_lines)
        
        return self.handle_lines(parsed_lines)

    
    def handle_lines(self, lines):
        for i, instobj in enumerate(lines):
            result = self.handle_inst(instobj, lines, i)
            if type(result) == tuple and result[0] == 'ERROR':
                return result[1]
            else:
                print(result, end='')
        return ''


    def handle_inst(self, instobj, lines, index):
        if self.validate_cmd(instobj.inst):
            for key, arg in list(instobj.args.items()):
                if '{' in arg:
                    embed = self.find_embed(arg)

                    for tup in reversed(embed):
                        new_inst = tup[0][1:len(tup[0])-1] if tup[0].startswith('{') and tup[0].endswith('}') else tup[0][1:] if tup[0].startswith('{') else tup[0][:len(tup[0])-1]

                        parsed_line_instobj = self.parse_lines([new_inst], lineno='%s, embedded in \'%s\'' % (instobj.lineno, instobj.line))[0]
                        selfcall_outcome = self.handle_inst(parsed_line_instobj, False, False)

                        if type(selfcall_outcome) == tuple:
                            return selfcall_outcome
                        else:
                            instobj.args[key] = list(instobj.args[key])
                            instobj.args[key][tup[1]: tup[2]] = list(str(selfcall_outcome))
                            instobj.args[key] = ''.join(instobj.args[key])

            return self.COMMANDS[instobj.inst](instobj, lines, index)
        else:
            return self.error('SyntaxError', 'Unknown command \'%s\'' % instobj.inst, instobj.line, instobj.lineno)

    
    def find_embed(self, inst):
        inst += ' '
        token = ''
        result = []
        start = 0
        embeds = found = started = 0
        for i in range(len(inst)):
            if inst[i] == '{':
                if started != 1:
                    start = i
                embeds += 1
                found = 1
                started = 1
            elif inst[i] == '}': embeds -= 1

            if found == 1 and embeds == 1:
                token = ''
            
            found = 0
            token += inst[i]
            if embeds == 0 and started > 0:
                result.append((token, start, i+1))
                started = 0
        return result   


    def parse_lines(self, lines, lineno=False):
        lines[len(lines)-1] += '\n'
        result = []
        embeds = quotes = 0
        token = ''
        last_unindented_line = 0  
        for i, line in enumerate(lines):

            if line.strip(' ') == '\n':
                result.append(False)
                continue

            nline = line
            while nline[:self.INDENTATION] == ' ' * self.INDENTATION:
                nline = nline[self.INDENTATION:]
            else:
                if nline[0] == ' ': return self.error('IndentationError', 'Invalid indentation', lines[i], i+1)

            inst = Inst(lineno = (i+1) if not lineno else lineno)
            
            if self.check_if_indented(line):
                line = line[self.INDENTATION:]
                result[last_unindented_line].contents.append(line)
                result.append(False)
                continue
            else:
                last_unindented_line = i

            inst.line = line.rstrip('\n').rstrip(' ')

            cur_arg = 1
            for index, tok in enumerate(line):
                token += tok
                if embeds == 0 and quotes == 0 and tok == ' ' or tok == '\n':
                    if inst.inst == '':
                        inst.inst = token[:-1]
                    else:
                        inst.args['arg%s' % cur_arg] = token[:-1]
                        cur_arg += 1
                    token = ''
                elif tok == '{': embeds += 1
                elif tok == '}': embeds -= 1
                elif tok == '"' and quotes == 0: quotes = 1
                elif tok == '"' and quotes == 1: quotes = 0

                if embeds < 0: return self.error('EmbedError', 'Invalid embed. Excess \'}\'', lines[i], i+1)

            result.append(copy.deepcopy(inst))

            if embeds > 0: return self.error('EmbedError', 'Invalid embed. Excess \'{\'', lines[i], i+1)


        return result


    def check_if_indented(self, line):
        if line[:self.INDENTATION] == ' ' * self.INDENTATION:
            return True
        else: return False

    def find_indentation_value(self, lines):

        for index, line in enumerate(lines):
            if line.startswith(' ') and line.rstrip(' ').lstrip(' ') != '\n':
                if not lines[index - 1].startswith(' '):
                    i = 0
                    tok = line[i]
                    while tok == ' ':
                        i += 1
                        tok = line[i]
                    return i
        return 4

    def validate_cmd(self, cmd):
        if cmd in self.COMMANDS: return True
        return False
    def do_exit(self, instobj, lines, index):
        exit()
        return ''
    def do_cal(self, instobj, lines, index): 
        try:
            result = eval(instobj.args['arg1'])
            return float(result)
        except NameError as e:
            return self.error('NameError', e, instobj.line, instobj.lineno)
        except ZeroDivisionError as e:
            return self.error('ZeroDivisionError', e, instobj.line, instobj.lineno)
        except SyntaxError:
            return self.error('SyntaxError', 'Invalid \'cal\' syntax', instobj.line, instobj.lineno)
        except TypeError:
            return kwargs['arg1']
        except KeyError:
            return self.error('TypeError', 'Not enough \'cal\' input', instobj.line, instobj.lineno)
    def do_say(self, instobj, lines, index): 
        print(*[instobj.args['arg%s' % (x+1)] for x in range(len(instobj.args))])
        return ''
    def do_help(self, instobj, lines, index): return '\nhelp is not implemented'
    def do_py(self, instobj, lines, index): return '\npy is not implemented'
    def do_create(self, instobj, lines, index): return '\ncreate is not implemented'
    def do_set(self, instobj, lines, index): 
        if len(instobj.args) == 2:
            if '[' in instobj.args['arg2']:
                pass
            else:
                self.vars.update({instobj.args['arg1']: ['STR', instobj.args['arg2']]})
        return ''


    def do_get(self, instobj, lines, index): 
        if len(instobj.args) == 1:
            return self.vars[instobj.args['arg1']][1]


    def do_open(self, instobj, lines, index): return '\nopen is not implemented'
    def do_func(self, instobj, lines, index): return '\nfunc is not implemented'
    def do_wait(self, instobj, lines, index): return '\nwait is not implemented'
    def do_int(self, instobj, lines, index): return '\nint is not implemented'
    def do_ask(self, instobj, lines, index): return '\nask is not implemented'
    def do_repeat(self, instobj, lines, index): return '\nrepeat is not implemented'
    def do_return(self, instobj, lines, index): return '\nreturn is not implemented'
    def do_use(self, instobj, lines, index): return '\nuse is not implemented'
    def do_cond(self, instobj, lines, index): return '\ncond is not implemented'
    def do_if(self, instobj, lines, index): return '\nif is not implemented'
    def do_else(self, instobj, lines, index): return '\nelse is not implemented'
    def do_len(self, instobj, lines, index): return '\nlen is not implemented'
    def do_pass(self, instobj, lines, index): return '\npass is not implemented'

sys.argv.append(r'C:\Users\jonas\OneDrive\Dokumenter\GitHub\crab\f.crab')
    
if __name__ == '__main__':
    crabber = Crab()
    print(crabber.handle_file(sys.argv[1]), end='')
    input('\n\nEnter to close ')