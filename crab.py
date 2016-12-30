#TODO: finish all commands, let if do cond (maybe), more loops (while, for in, etc.)
#TODO: attempt/instead statement, throw command, switch (maybe), read/write to a file 
#TODO: stats, 

import copy
import os
import pprint
import sys
import time

os.system('cls')
time.sleep(0.05)

class Inst:

    def __init__(self, inst='', contents=[], lineno=0, line='', do=True, parent=False, embedded_in='', **kwargs):
        self.inst = inst
        self.contents = contents
        self.lineno = lineno
        self.line = line
        self.args = kwargs
        self.do = do
        self.parent = parent
        self.embedded_in = embedded_in

    def __repr__(self):
        return '<Inst object \'%s\' at line %s that %scontains %s line(s): %s %s>' % (self.line, self.lineno, ('is child of %s and ' % self.parent) if self.parent else '', len(self.contents), self.contents, self.args)


class Crab:


    def __init__(self):

        #Constants
        self.FILE_NAME = ''
        self.FILE_DIR = ''
        self.FILE_PATH = ''
        self.INDENTATION = 4
        self.BOOLS = ['TRUE', 'FALSE']
        self.DONT_DO = ['else']
        self.COMMANDS = {
            'exit': self.do_exit, 
            'cal': self.do_cal, 
            'cout': self.do_cout,
            'help': self.do_help,
            'py_exec': self.do_py_exec, 
            'create': self.do_create, 
            'set': self.do_set, 
            'get': self.do_get, 
            'open': self.do_open,
            'func': self.do_func,
            'wait': self.do_wait,
            'round': self.do_round,
            'ask': self.do_ask,
            'repeat': self.do_repeat,
            'return': self.do_return,
            'use': self.do_use,
            'cond': self.do_cond,
            'if': self.do_if,
            'else': self.do_else,
            'len': self.do_len,
            'pass': self.do_pass,
            'endl': self.do_endl,
            'spc': self.do_spc,
            'while': self.do_while
            }
        
        #Variables
        self.vars = dict()
        self.funcs = dict()
        self.do_get_var = str()


    def error(self, errortype, msg, line, lineno):
        #Returns an error message in a tuple
        return ('ERROR', '\n\n%s\n%s\nLine %s\n\'%s\'\n%s\n\n' % (self.FILE_PATH, errortype, lineno, line.rstrip('\n'), msg))


    def handle_file(self, file_path):
        self.FILE_NAME = os.path.basename(file_path)
        self.FILE_DIR = file_path.rstrip(self.FILE_NAME)
        self.FILE_PATH = file_path
        
        with open(file_path, 'r', encoding='UTF-8') as f:
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
            if type(result) == tuple:
                if result[0] == 'ERROR':
                    return result[1]
                elif result[0] == 'RETURN':
                    return result

            else:
                print(result, end='')
        return ''


    def handle_inst(self, instobj, lines, index):
        ninstobj = copy.deepcopy(instobj)
        if self.validate_cmd(ninstobj.inst) and ninstobj.do:
            for key, arg in list(ninstobj.args.items()):
                if '{' in arg:
                    embed = self.find_embed(arg, '{', '}')

                    for tup in reversed(embed):
                        new_inst = tup[0][1:len(tup[0])-1] if tup[0].startswith('{') and tup[0].endswith('}') else tup[0][1:] if tup[0].startswith('{') else tup[0][:len(tup[0])-1]
                        parsed_line_ninstobj = self.parse_lines([new_inst], lineno=ninstobj.lineno, embedded_in=ninstobj.line, parent=ninstobj)[0]
                        selfcall_outcome = self.handle_inst(parsed_line_ninstobj, False, False)

                        if type(selfcall_outcome) == tuple:
                            if selfcall_outcome[0] == 'ERROR':
                                return selfcall_outcome#[1] <<< IDK about this, I'm pretty certian it's useless (the '[1]' part)
                            elif selfcall_outcome[0] == 'RETURN':
                                ninstobj.args[key] = list(ninstobj.args[key])
                                ninstobj.args[key][tup[1]: tup[2]] = list(str(selfcall_outcome))
                                ninstobj.args[key] = ''.join(ninstobj.args[key])
                                if ninstobj.parent:
                                    if ninstobj.parent.inst == 'func':
                                        return ('RETURN', self.COMMANDS[ninstobj.inst](ninstobj, lines, index), selfcall_outcome[2])
                                    else:
                                        return self.error('SyntaxError', '\'return\' outside function', ninstobj.line, ninstobj.lineno)
                        else:
                            ninstobj.args[key] = list(ninstobj.args[key])
                            ninstobj.args[key][tup[1]: tup[2]] = list(str(selfcall_outcome))
                            ninstobj.args[key] = ''.join(ninstobj.args[key])

            return self.COMMANDS[ninstobj.inst](ninstobj, lines, index)
        else:
            if ninstobj.do:
                return self.error('SyntaxError', 'Unknown command \'%s\'' % ninstobj.inst, ninstobj.line, ninstobj.lineno)
            return ''

    
    def find_embed(self, inst, start_embed, end_embed):
        # start_embed and end_embed are the characters it looks for (usually '{' and '}') 
        inst += ' '
        token = ''
        result = []
        start = 0
        embeds = found = started = 0
        for i in range(len(inst)):
            if inst[i] == start_embed:
                if started != 1:
                    start = i
                embeds += 1
                found = 1
                started = 1
            elif inst[i] == end_embed: embeds -= 1

            if found == 1 and embeds == 1:
                token = ''
            
            found = 0
            token += inst[i]
            if embeds == 0 and started > 0:
                result.append((token, start, i+1))
                started = 0
        return result   


    def parse_lines(self, lines, lineno=False, indentline=0, parent=False, embedded_in=''):
        result = []
        embeds = quotes = lists = 0
        token = ''
        last_unindented_line = 0  
        for i, line in enumerate(lines):

            if line.lstrip(' ').rstrip(' ') == '\n' and line.strip(' ') != '':
                result.append(False)
                continue
            elif len(line.lstrip(' ')) > 0:
                if line.lstrip(' ')[0] == '#':
                    result.append(False)
                    continue

            nline = line
            while nline[:self.INDENTATION] == ' ' * self.INDENTATION:
                nline = nline[self.INDENTATION:]
            else:
                try:
                    if nline[0] == ' ': return self.error('IndentationError', 'Invalid indentation', lines[i], i+1)
                except IndexError:
                    continue # Quick bugfix, might cause trouble later ;)

            inst = Inst(lineno = (i+1+indentline) if not lineno else int(lineno)+indentline, parent=parent, embedded_in=embedded_in)
            
            if self.check_if_indented(line):
                try:
                    line = line[self.INDENTATION:]
                    result[last_unindented_line].contents.append(line)
                    result.append(False)
                    continue
                except AttributeError:
                    return self.error('IndentationError', 'Invalid indentation', lines[i], i+1)
            else:
                last_unindented_line = i

            inst.line = line.rstrip('\n').rstrip(' ')

            cur_arg = 1
            for index, tok in enumerate(line + ' '):
                token += tok
                if sum([embeds, quotes, lists]) == 0 and tok == ' ' or tok == '\n':
                    if inst.inst == '':
                        inst.inst = token[:-1]
                        if inst.inst in self.DONT_DO:
                            inst.do = False
                    else:
                        if token[:-1] != '':
                            inst.args['arg%s' % cur_arg] = token[:-1]
                            cur_arg += 1
                    token = ''
                elif tok == '{': embeds += 1
                elif tok == '}': embeds -= 1
                elif tok == '"' and quotes == 0: quotes = 1
                elif tok == '"' and quotes == 1: quotes = 0
                elif tok == '[': lists += 1
                elif tok == ']': lists -= 1
                elif tok == '#':
                    if token.strip(' ') == '#':
                        token = ''
                        break
                    return self.error('SyntaxError', 'Invalid comment, comments can only occur on seperat lines or after a space', lines[i], inst.lineno+1)

                if embeds < 0: return self.error('SyntaxError', 'Invalid embed. Missing \'{\'', lines[i], inst.lineno+1)
                elif lists < 0: return self.error('SyntaxError', 'Invalid list. Missing \'[\'', lines[i], inst.lineno+1)

            if inst.inst != '':
                result.append(copy.deepcopy(inst))

            if embeds > 0: return self.error('SyntaxError', 'Invalid embed. Missing \'}\'', lines[i], inst.lineno+1)
            elif lists > 0: return self.error('SyntaxError', 'Invalid list. Missing \']\'', lines[i], inst.lineno+1)

        return result


    def check_if_indented(self, line):
        if line[:self.INDENTATION] == ' ' * self.INDENTATION:
            return True
        else: return False

    def find_indentation_value(self, lines):

        for index, line in enumerate(lines):
            if line.startswith(' ') and line.strip(' ') != '\n' and line.strip(' ') != '' :
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

    
    def str2list(self, s):
        if not (s.startswith('[') and s.endswith(']')):
            return False       
        elif s == '[]':
            return []

        s = s[1:]
        l = []
        b = 0
        t = ''

        for tok in s:
            if b:
                if tok == '[': b += 1
                elif tok == ']': b -= 1
                t += tok

                if not b:
                    l.append(self.str2list('[' + t))
                    t = ''
                    
            else:
                if (tok == ' ' and t == '') or (tok in ["'", '"']):
                    continue
                elif tok == ',' or tok == ']':
                    if t != '':
                        l.append(t)
                        t = ''
                elif tok == '[':
                    b += 1
                    t = ''
                else:
                    t += tok

        if len(s) > 0 and len(l) == 0:
            return False 
        return l



    def do_exit(self, instobj, lines, index):
        exit()
        return ''
    def do_cal(self, instobj, lines, index):
        try:
            result = eval(instobj.args['arg1'])
            return float(result)
        except NameError as e:
            return self.error('SyntaxError', 'Invalid \'cal\' syntax', instobj.line, instobj.lineno)
        except ZeroDivisionError as e:
            return self.error('ZeroDivisionError', e, instobj.line, instobj.lineno)
        except SyntaxError:
            return self.error('SyntaxError', 'Invalid \'cal\' syntax', instobj.line, instobj.lineno)
        except KeyError:
            return self.error('TypeError', 'Not enough \'cal\' input', instobj.line, instobj.lineno)
        except TypeError as e:
            return self.error('SyntaxError', 'Invalid \'cal\' syntax: %s' % e.__str__().capitalize(), instobj.line, instobj.lineno)


    def do_cout(self, instobj, lines, index): 
        print('\n', ' '.join([instobj.args['arg%s' % (x+1)] for x in range(len(instobj.args))]), end='', sep='')
        return ''
    def do_help(self, instobj, lines, index): return '\nhelp is not implemented'
    def do_py_exec(self, instobj, lines, index):
        try:
            result = exec('\n'.join(instobj.contents))
            return ''
        except Exception as e:
            return self.error('py_execError', e, 'Below exception was thrown by Python', instobj.lineno)


    def do_create(self, instobj, lines, index): return '\ncreate is not implemented'
    def do_set(self, instobj, lines, index): 
        try:
            if len(instobj.args) == 2:
                if instobj.args['arg2'].startswith('[') and instobj.args['arg2'].endswith(']'):
                    self.vars.update({instobj.args['arg1']: ['LIST', self.str2list(instobj.args['arg2'])]})
                elif instobj.args['arg2'] in self.BOOLS:
                    self.vars.update({instobj.args['arg1']: ['BOOL', instobj.args['arg2']]})
                else:
                    self.vars.update({instobj.args['arg1']: ['STR', instobj.args['arg2']]})

            elif len(instobj.args) >= 3:
                if instobj.args['arg3'].startswith('[') and instobj.args['arg3'].endswith(']'):

                    indices = ''
                    for i in range(len(instobj.args) - 2):
                        arg = instobj.args['arg%s' % (i+2)]
                        indices += '[%s]' % arg

                    cmd = 'self.vars[instobj.args[\'arg1\']][1]%s = self.str2list(instobj.args[\'arg%s\'])' % (indices, len(instobj.args))
                    exec(cmd)  

                else:
                    if self.vars[instobj.args['arg1']][0] == 'STR':
                        tmp = list(self.vars[instobj.args['arg1']][1])
                        tmp[int(instobj.args['arg2'])] = instobj.args['arg3']
                        tmp = ''.join(tmp)
                        self.vars[instobj.args['arg1']] = ['STR', tmp]
                    elif self.vars[instobj.args['arg1']][0] == 'LIST':
                        indices = ''
                        for i in range(len(instobj.args) - 2):
                            arg = instobj.args['arg%s' % (i+2)]
                            indices += '[%s]' % arg

                        cmd = 'self.vars[instobj.args[\'arg1\']][1]%s = instobj.args[\'arg%s\']' % (indices, len(instobj.args))
                        exec(cmd)
                    else:
                        return self.error('TypeError', '\'%s\' type is not subscriptable' % self.vars[instobj.args['arg1']][0], instobj.line, instobj.lineno)
            else:
                return self.error('SyntaxError', 'Too few many arguments to \'set\'', instobj.line, instobj.lineno)
        except IndexError:
            return self.error('IndexError', 'Assignment index out of range', instobj.line, instobj.lineno)
        except KeyError:
            return self.error('NameError', '\'%s\' is not defined' % instobj.args['arg1'], instobj.line, instobj.lineno)
        except NameError:
            return self.error('SyntaxError', 'Indices must be integers' % instobj.args['arg1'], instobj.line, instobj.lineno)
        except SyntaxError:
            return self.error('SyntaxError', 'Indices must be integers', instobj.line, instobj.lineno)
        return ''


    def do_get(self, instobj, lines, index):
        if len(instobj.args) == 1:
            try:
                return self.vars[instobj.args['arg1']][1]
            except KeyError as e:
                return self.error('NameError', '%s is not defined' % e, instobj.line, instobj.lineno)
        elif len(instobj.args) >= 2:
            try:
                indices = ''
                for i in range(len(instobj.args) - 1):
                    arg = instobj.args['arg%s' % (i+2)]
                    indices += '[%s]' % int(arg)

                exec('self.do_get_var = self.vars[instobj.args[\'arg1\']][1]%s' % indices)
                return self.do_get_var
            except ValueError:
                return self.error('ValueError', 'Can\'t get index \'%s\'' % instobj.args['arg2'], instobj.line, instobj.lineno)
            except KeyError as e:
                return self.error('NameError', '%s is not defined' % e, instobj.line, instobj.lineno)
            except SyntaxError:
                return self.error('SyntaxError', 'Indices must be integers', instobj.line, instobj.lineno)
            except NameError:
                return self.error('SyntaxError', 'Indices must be integers', instobj.line, instobj.lineno)
            except IndexError as e:
                return self.error('SyntaxError', e.__str__().capitalize(), instobj.line, instobj.lineno)
        else:
            return self.error('SyntaxError', 'Too few arguments to \'get\'', instobj.line, instobj.lineno)


    def do_open(self, instobj, lines, index): return '\nopen is not implemented'
    def do_func(self, instobj, lines, index):
        if len(instobj.args) < 1:
            return self.error('SyntaxError', 'Too few arguments to \'func\'', instobj.line, instobj.lineno)

        func_keywords = ['def']

        if len(instobj.args) == 2 and instobj.args['arg1'] in func_keywords:
            if instobj.args['arg1'] == 'def':
                parsed_lines = self.parse_lines(instobj.contents, indentline=instobj.lineno, parent=instobj)
                if type(parsed_lines) == tuple:
                    return parsed_lines
                else:
                    parsed_lines = [item for item in parsed_lines if item]
                self.funcs[instobj.args['arg2']] = parsed_lines
                self.vars.update({'_%s_args' % instobj.args['arg2']: ['LIST', []]})

            else:
                return self.error('SyntaxError', 'Can\'t do func \'%s\'' % instobj.args['arg1'], instobj.line, instobj.lineno)
        
        else:
            try:
                args = []
                for i in range(len(instobj.args)):
                    if i == 0:
                        continue
                    if instobj.args['arg%s' % (i+1)].startswith('[') and instobj.args['arg%s' % (i+1)].endswith(']'):
                        args.append(self.str2list(instobj.args['arg%s' % (i+1)]))
                    else:
                        args.append(instobj.args['arg%s' % (i+1)])
                self.vars.update({'_%s_args' % instobj.args['arg1']: ['LIST', args]})

                result = self.handle_lines(self.funcs[instobj.args['arg1']])
                if type(result) == tuple:
                    if result[0] == 'ERROR':
                        return result
                    elif result[0] == 'RETURN':
                        return result[1]
                return result
            except KeyError:
                return self.error('NameError', '\'%s\' is not defined' % instobj.args['arg1'], instobj.line, instobj.lineno)

        return ''


    def do_wait(self, instobj, lines, index):
        if len(instobj.args) > 1:
            return self.error('SyntaxError', 'Too many arguments to \'wait\'', instobj.line, instobj.lineno)
        try:
            wait_time = time.time() + int(instobj.args['arg1'])
            while time.time() < wait_time:
                time.sleep(0.01)
        except ValueError:
            return self.error('SyntaxError', 'Can\'t wait \'%s\' seconds' % instobj.args['arg1'], instobj.line, instobj.lineno)
        except OverflowError:
            return self.error('SyntaxError', 'Can\'t wait \'%s\' seconds' % instobj.args['arg1'], instobj.line, instobj.lineno)
        return ''
    def do_round(self, instobj, lines, index):
        try:
            if len(instobj.args) == 1:
                rounded = int(round(float(instobj.args['arg1'])))
            elif len(instobj.args) == 2:
                rounded = round(float(instobj.args['arg1']), int(instobj.args['arg2']))
        except ValueError:
            return self.error('SyntaxError', 'All arguments to \'round\' must be numbers', instobj.line, instobj.lineno)
        return rounded

    def do_ask(self, instobj, lines, index): 
        return input((' '.join([instobj.args['arg%s' % (x+1)] for x in range(len(instobj.args))])))

    def do_repeat(self, instobj, lines, index):
        if len(instobj.args) > 1:
            return self.error('SyntaxError', 'Too many arguments to \'repeat\'', instobj.line, instobj.lineno)
        
        try:
            parsed_lines = self.parse_lines(instobj.contents, indentline=instobj.lineno, parent=instobj)
            if type(parsed_lines) == tuple:
                return parsed_lines
            else:
                parsed_lines = [item for item in parsed_lines if item]
            
            for i in range(int(float(instobj.args['arg1']))):
                outcome = self.handle_lines(parsed_lines)
                if type(outcome) == tuple:
                    return outcome
                outcome = ''

            return outcome
        except ValueError:
            return self.error('ValueError', '\'repeat\' only takes whole numbers as an argument', instobj.line, instobj.lineno)
        

    def do_return(self, instobj, lines, index):
        in_func = False
        next_parent = instobj.parent
        while next_parent:
            if next_parent.inst == 'func':
                in_func = True
                break
            next_parent = next_parent.parent
        else:
            return self.error('SyntaxError', '\'return\' outside function', instobj.line, instobj.lineno)

        return ('RETURN', ' '.join([instobj.args['arg%s' % (x+1)] for x in range(len(instobj.args))]), instobj)


    def do_use(self, instobj, lines, index):
        if len(instobj.args) != 1:
            return self.error('SyntaxError', 'Too many or too few arguments to \'use\'', instobj.line, instobj.lineno)
        elif instobj.args['arg1'] + '.crb' in [self.FILE_NAME, self.FILE_PATH]:
            return self.error('UseError', 'Can\'t \'use\' self', instobj.line, instobj.lineno)

        try:
            return self.handle_file(self.FILE_DIR + instobj.args['arg1'] + '.crb')
        except PermissionError:
            try:
                return self.handle_file(instobj.args['arg1'])
            except PermissionError:
                return self.error('UseError', 'Couldn\'t find module \'%s\'' % instobj.args['arg1'], instobj.line, instobj.lineno)
        return ''

    def do_cond(self, instobj, lines, index):
        if len(instobj.args) == 2:
            if instobj.args['arg1'] == 'not':
                if not (instobj.args['arg2'] == 'TRUE'): return 'TRUE'
                else: return 'FALSE'
            else:
                return self.error('SyntaxError', 'There is no such logic gate: \'%s\'' % instobj.args['arg1'], instobj.line, instobj.lineno)

        elif len(instobj.args) != 3:
            return self.error('SyntaxError', '\'cond\' takes exactly 3 arguments', instobj.line, instobj.lineno)


        if instobj.args['arg2'] == '==':
            if instobj.args['arg1'] == instobj.args['arg3']: return 'TRUE'
            else: return 'FALSE'

        elif instobj.args['arg2'] == '<=':
            if instobj.args['arg1'] <= instobj.args['arg3']: return 'TRUE'
            else: return 'FALSE'

        elif instobj.args['arg2'] == '>=':
            if instobj.args['arg1'] >= instobj.args['arg3']: return 'TRUE'
            else: return 'FALSE'

        elif instobj.args['arg2'] == '!=':
            if instobj.args['arg1'] != instobj.args['arg3']: return 'TRUE'
            else: return 'FALSE'

        elif instobj.args['arg2'] == '<':
            if instobj.args['arg1'] < instobj.args['arg3']: return 'TRUE'
            else: return 'FALSE'

        elif instobj.args['arg2'] == '>':
            if instobj.args['arg1'] > instobj.args['arg3']: return 'TRUE'
            else: return 'FALSE'

        elif instobj.args['arg2'] == 'and':
            if instobj.args['arg1'] == 'TRUE' and instobj.args['arg3'] == 'TRUE': return 'TRUE'
            else: return 'FALSE'

        elif instobj.args['arg2'] == 'or':
            if instobj.args['arg1'] == 'TRUE' or instobj.args['arg3'] == 'TRUE': return 'TRUE'
            else: return 'FALSE'

        elif instobj.args['arg2'] == 'xor':
            if (instobj.args['arg1'] == 'TRUE' and instobj.args['arg3'] == 'FALSE') or (instobj.args['arg1'] == 'FALSE' and instobj.args['arg3'] == 'TRUE'): return 'TRUE'
            else: return 'FALSE'

        elif instobj.args['arg2'] == 'nand':
            if not (instobj.args['arg1'] == 'TRUE' and instobj.args['arg3'] == 'TRUE'): return 'TRUE'
            else: return 'FALSE'

        elif instobj.args['arg2'] == 'nor':
            if instobj.args['arg1'] == 'FALSE' and instobj.args['arg3'] == 'FALSE': return 'TRUE'
            else: return 'FALSE'

        elif instobj.args['arg2'] == 'xnor':
            if (instobj.args['arg1'] == 'TRUE' and instobj.args['arg3'] == 'TRUE') or (instobj.args['arg1'] == 'FALSE' and instobj.args['arg3'] == 'FALSE'): return 'TRUE'
            else: return 'FALSE'

        elif instobj.args['arg2'] == 'in':
            arg1 = self.str2list(instobj.args['arg1'])
            arg3 = self.str2list(instobj.args['arg3'])
            if not arg1:
                arg1 = instobj.args['arg1']
            if not arg3:
                arg3 = instobj.args['arg3']
            try:
                if arg1 in arg3: return 'TRUE'
                else: return 'FALSE'
            except TypeError:
                return 'FALSE'

        else:
            return self.error('SyntaxError', 'There is no such logic gate/comparison operator: \'%s\'' % instobj.args['arg1'], instobj.line, instobj.lineno)

    def do_if(self, instobj, lines, index):
        if len(instobj.args) != 1:
            return self.error('SyntaxError', '\'if\' takes 1 argument, but got %s' % len(instobj.args), instobj.line, instobj.lineno)

        if instobj.args['arg1'] == 'TRUE':
            parsed_lines = self.parse_lines(instobj.contents, indentline=instobj.lineno, parent=instobj)
            if type(parsed_lines) == tuple:
                return parsed_lines
            else:
                parsed_lines = [item for item in parsed_lines if item]

            result = self.handle_lines(parsed_lines)
            if type(result) == tuple:
                if result[0] == 'ERROR':
                    return result[1]
                elif result[0] == 'RETURN':
                    return result
            return result


        elif instobj.args['arg1'] == 'FALSE' and len(lines) > index+1:
            if lines[index+1].inst == 'else':
                lines[index+1].do = True
        else:
            if instobj.args['arg1'] != 'FALSE':
                return self.error('TypeError', '\'if\' only take type BOOL as argument', instobj.line, instobj.lineno)
        return ''


    def do_else(self, instobj, lines, index):
        if len(instobj.args) > 0:
            return self.error('SyntaxError', '\'else\' doesn\'t take any arguments', instobj.line, instobj.lineno)

        parsed_lines = self.parse_lines(instobj.contents, indentline=instobj.lineno, parent=instobj)
        if type(parsed_lines) == tuple:
            return parsed_lines[1]
        else:
            parsed_lines = [item for item in parsed_lines if item]
        
        result = self.handle_lines(parsed_lines)
        if type(result) == tuple:
            if result[0] == 'ERROR':
                return result[1]
            elif result[0] == 'RETURN':
                return result
        return result


    def do_len(self, instobj, lines, index):
        if len(instobj.args) == 1:
            if instobj.args['arg1'].startswith('[') and instobj.args['arg1'].endswith(']'):
                return len(self.str2list(instobj.args['arg1']))
            elif instobj.args['arg1'] in self.BOOLS:
                return '1'
            else:
                return len(instobj.args['arg1'])
        else:
            return self.error('SyntaxError', 'Too many arguments to \'len\'', instobj.line, instobj.lineno)
        
        return instobj.args
    def do_pass(self, instobj, lines, index):
        return ''
    def do_spc(self, instobj, lines, index):
        try:
            return ' ' * (int(instobj.args['arg1']) if len(instobj.args) >= 1 else 1)
        except ValueError:
            return self.error('ValueError', '\'spc\' only takes whole numbers as the second argument', instobj.line, instobj.lineno)

    def do_endl(self, instobj, lines, index):
        try:
            return '\n' * (int(instobj.args['arg1']) if len(instobj.args) >= 1 else 1)
        except ValueError:
            return self.error('ValueError', '\'endl\' only takes whole numbers as the second argument', instobj.line, instobj.lineno)

    def do_while(self, instobj, lines, index):
        if len(instobj.args) > 1:
            return self.error('SyntaxError', 'Too many arguments to \'while\'', instobj.line, instobj.lineno)
        
        #try:
        parsed_lines = self.parse_lines(instobj.contents, indentline=instobj.lineno, parent=instobj)
        if type(parsed_lines) == tuple:
            return parsed_lines[1]
        else:
            parsed_lines = [item for item in parsed_lines if item]    

        if self.find_embed(lines[index].args['arg1'], '{', '}'):
            ninstobj = self.parse_lines([lines[index].args['arg1'][1:-1]])[0]
            instobj.args['arg1'] = self.handle_inst(ninstobj, lines, index)
            if type(instobj.args['arg1']) == tuple:
                return instobj.args['arg1']

        
        print(instobj.args['arg1'], ' <<< what it returned')
        if instobj.args['arg1'] not in self.BOOLS:
            return self.error('TypeError', '\'while\' only takes \'TRUE\' or \'FALSE\' as an argument', instobj.line, instobj.lineno)
        
        while instobj.args['arg1'] == 'TRUE':
            pass

        '''
        for i in range(int(float(instobj.args['arg1']))):
            outcome = self.handle_lines(parsed_lines)
            if type(outcome) == tuple:
                return outcome
            outcome = ''

        return outcome
        '''
        #except ValueError:
        #    return self.error('TypeError', '\'while\' only takes \'TRUE\' or \'FALSE\' as an argument', instobj.line, instobj.lineno)

sys.argv.append(r'C:\Users\jonas\OneDrive\Dokumenter\GitHub\crab\f.crb')

if __name__ == '__main__':
    crabber = Crab()
    print(crabber.handle_file(sys.argv[1]), end='')
    input('\n\nEnter to close ')
