import os
os.system('cls')

import sys
import pprint
import copy
import time
time.sleep(0.05)


class Inst:

    def __init__(self, inst='', contents=[], lineno=0, **kwargs):
        self.inst = inst
        self.contents = contents
        self.lineno = lineno
        self.args = kwargs

    def __repr__(self):
        return '<Inst object \'%s\' at line %s that contains %s lines: %s>' % (self.line, self.lineno, len(self.contents), self.contents)


class Crab:


    def __init__(self):
        self.FILE_NAME = ''
        self.FILE_DIR = ''
        self.INDENTATION = 4


    def error(self, errortype, msg, line, lineno):
        return ('ERROR', '%s\nLine %s\n%s\n%s' % (errortype, lineno, line.rstrip('\n'), msg))


    def handle_file(self, file_path):
        self.FILE_NAME = os.path.basename(file_path)
        self.FILE_DIR = file_path.rstrip(self.FILE_NAME)
        
        with open(file_path, 'r') as f:
            lines = f.readlines()

        self.INDENTATION = self.find_indentation(lines)

        parsed_lines = self.parse_lines(lines)
        if type(parsed_lines) == tuple:
            return parsed_lines[1]
        else:
            parsed_lines = [item for item in parsed_lines if item]
            #pprint.pprint(parsed_lines)
        
        tmp = self.parse_lines(parsed_lines[2].contents, l=True)
        if type(tmp) == tuple:
            return tmp[1]
        else:
            pprint.pprint(tmp)


        return ''



    def parse_lines(self, lines, l=False):
        lines[len(lines)-1] += '\n'
        result = []
        embeds = quotes = 0
        token = ''
        last_unindented_line = 1      
        for i, line in enumerate(lines):
            if line.strip(' ') == '\n':
                continue
            line = line.rstrip('\n').rstrip(' ')
            cur_arg = 1
            inst = Inst(lineno=i+1)

            if line[0] == ' ':
                if line[:self.INDENTATION] == ' ' * self.INDENTATION:
                    if l:print(last_unindented_line)
                    line = line[self.INDENTATION:]
                    result[last_unindented_line].contents.append(line)
                    result.append(False)
                    continue
                else:
                    return self.error('IndentationError', 'Invalid indentation', lines[i], i+1)
            else:
                last_unindented_line = i-1

            inst.line = line
            
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

            ninst = copy.deepcopy(inst)
            result.append(ninst)

            if embeds > 0: return self.error('EmbedError', 'Invalid embed. Excess \'{\'', lines[i], i+1)


        return result




    def find_indentation(self, lines):
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




sys.argv.append(r'C:\Users\jonas\OneDrive\Dokumenter\GitHub\crab\f.crab')
    
if __name__ == '__main__':
    crabber = Crab()
    print(crabber.handle_file(sys.argv[1]))
    input('\n\nEnter to close ')