import sys

VALID_OPCODES = {'load', 'loadI', 'store', 'add', 'sub', 'mult', 'lshift', 'rshift', 'output', 'nop'}


def scan(lines):
    tokens = []

    for line_num, line in enumerate(lines, start=1):
        i = 0
        length = len(line)

        while i < length:
            char = line[i]

            if char.isspace():
                i += 1
                continue

            if char == '/' and i + 1 < length and line[i + 1] == '/':
                lexeme = line[i:].strip()
                tokens.append((line_num, 'COMMENT', lexeme))
                break

            if char == 'r' and i + 1 < length and line[i + 1].isdigit():
                lexeme = 'r'
                i += 1
                while i < length and line[i].isdigit():
                    lexeme += line[i]
                    i += 1
                tokens.append((line_num, 'REGISTER', lexeme))
                continue

            if char.isalpha():
                lexeme = ''
                while i < length and line[i].isalnum():
                    lexeme += line[i]
                    i += 1
                tokens.append((line_num, 'OPCODE', lexeme))
                continue

            if char.isdigit():
                lexeme = ''
                while i < length and line[i].isdigit():
                    lexeme += line[i]
                    i += 1
                tokens.append((line_num, 'CONSTANT', lexeme))
                continue

            if char == ',':
                tokens.append((line_num, 'COMMA', ','))
                i += 1
                continue

            if char == '=' and i + 1 < length and line[i + 1] == '>':
                tokens.append((line_num, 'ASSIGN_ARROW', '=>'))
                i += 2
                continue

            i += 1

    return tokens


def print_tokens(tokens):
    for line_num, token_type, lexeme in tokens:
        print(f"{line_num} {token_type} {lexeme}")


def parse(tokens):
    errors = []
    line_tokens = {}

    for t in tokens:
        line_num, _, _ = t
        if line_num not in line_tokens:
            line_tokens[line_num] = []
        if t[1] != 'COMMENT':
            line_tokens[line_num].append(t)

    for line_num, lt in line_tokens.items():
        if not lt:
            continue

        types = [t[1] for t in lt]
        lexemes = [t[2] for t in lt]
        opcode = lexemes[0] if lt else ''

        if opcode not in VALID_OPCODES:
            errors.append(f"Error on line {line_num}: Invalid opcode '{opcode}'")
            continue

        if opcode in ['add', 'sub', 'mult', 'lshift', 'rshift']:
            expected = ['OPCODE', 'REGISTER', 'COMMA', 'REGISTER', 'ASSIGN_ARROW', 'REGISTER']
            if types != expected:
                errors.append(f"Error on line {line_num}: Invalid format for '{opcode}'")

        elif opcode == 'loadI':
            expected = ['OPCODE', 'CONSTANT', 'ASSIGN_ARROW', 'REGISTER']
            if types != expected:
                errors.append(f"Error on line {line_num}: Invalid format for 'loadI'")

        elif opcode in ['load', 'store']:
            expected = ['OPCODE', 'REGISTER', 'ASSIGN_ARROW', 'REGISTER']
            if types != expected:
                errors.append(f"Error on line {line_num}: Invalid format for '{opcode}'")

        elif opcode == 'output':
            expected = ['OPCODE', 'REGISTER']
            if types != expected:
                errors.append(f"Error on line {line_num}: Invalid format for 'output'")

        elif opcode == 'nop':
            expected = ['OPCODE']
            if types != expected:
                errors.append(f"Error on line {line_num}: Invalid format for 'nop'")

        for i, typ in enumerate(types):
            if typ == 'CONSTANT' and int(lexemes[i]) > 2**31 - 1:
                errors.append(f"Error on line {line_num}: Constant out of range")
            if typ == 'ASSIGN_ARROW' and lexemes[i] != '=>':
                errors.append(f"Error on line {line_num}: Invalid assignment arrow")

    return errors


def build_ir(tokens):
    ir = []
    line_tokens = {}

    for t in tokens:
        line_num, typ, lex = t
        if line_num not in line_tokens:
            line_tokens[line_num] = []
        if typ != 'COMMENT':
            line_tokens[line_num].append((typ, lex))

    for line_num, lt in line_tokens.items():
        if not lt:
            continue

        opcode = lt[0][1]
        op1 = op2 = op3 = None

        if len(lt) > 1:
            op1 = lt[1][1]
        if len(lt) > 3:
            op2 = lt[3][1]
        if len(lt) > 5:
            op3 = lt[5][1]

        ir.append({
            'line': line_num,
            'opcode': opcode,
            'op1': op1,
            'op2': op2,
            'op3': op3
        })

    return ir


def print_ir(ir):
    for instr in ir:
        opcode = instr["opcode"]
        line_num = instr["line"]

        op1_label = "op1"
        op2_label = "op2"
        op3_label = "op3"

        if opcode == "load":
            op1_label = "src"
            op2_label = "dest"
            op3_label = None
        elif opcode == "store":
            op1_label = "src"
            op2_label = "dest"
            op3_label = None

        line = f"Line {line_num}: {opcode}"

        if instr["op1"] and op1_label:
            line += f" — {op1_label}: {instr['op1']}"
        if instr["op2"] and op2_label:
            line += f" — {op2_label}: {instr['op2']}"
        if instr["op3"] and op3_label:
            line += f" — {op3_label}: {instr['op3']}"

        print(line)


def show_help():
    print("Usage: 411fe [flag] <file>")
    print("-h: Show this help message")
    print("-s <file>: Scan the file and print tokens")
    print("-p <file>: Scan and parse the file, report errors or 'VALID ILOC PROGRAM'")
    print("-r <file>: Scan, parse, build IR, and print IR")
    sys.exit(0)


args = sys.argv[1:]
flag = '-p'
filename = None

if not args:
    show_help()

for i, arg in enumerate(args):
    if arg == '-h':
        show_help()
    elif arg in ['-r', '-p', '-s'] and i + 1 < len(args):
        flag = arg
        filename = args[i + 1]
        break

if not filename and flag != '-h':
    print("Error: Missing file name")
    show_help()

if flag in ['-p', '-r', '-s']:
    if not filename.endswith('.iloc'):
        print(f"Error: Cannot compile '{filename}'. Expected a '.iloc' file extension.")
        sys.exit(1)

try:
    with open(filename, 'r') as f:
        lines = f.readlines()
except FileNotFoundError:
    print(f"Error: File {filename} not found")
    sys.exit(1)

tokens = []
errors = []
ir = []

if flag == '-s':
    tokens = scan(lines)
    print_tokens(tokens)

elif flag == '-p':
    tokens = scan(lines)
    errors = parse(tokens)
    if not errors:
        print("VALID ILOC PROGRAM")
        print("Compilation Successful!")
    else:
        for err in errors:
            print(err)

elif flag == '-r':
    tokens = scan(lines)
    errors = parse(tokens)
    if not errors:
        ir = build_ir(tokens)
        print_ir(ir)
    else:
        for err in errors:
            print(err)
