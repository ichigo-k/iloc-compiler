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

            if char.isdigit() or (char == '-' and i + 1 < length and line[i + 1].isdigit()):
                lexeme = ''
                if char == '-':
                    lexeme += '-'
                    i += 1
                    char = line[i]
                while i < length and line[i].isdigit():
                    lexeme += line[i]
                    i += 1
                tokens.append((line_num, 'CONSTANT', lexeme))
                continue

            if char.isalpha():
                lexeme = ''
                while i < length and line[i].isalnum():
                    lexeme += line[i]
                    i += 1
                if lexeme in VALID_OPCODES:
                    tokens.append((line_num, 'OPCODE', lexeme))
                else:
                    tokens.append((line_num, 'IDENTIFIER', lexeme))
                continue

            if char == ',':
                tokens.append((line_num, 'COMMA', ','))
                i += 1
                continue

            if char == '=' and i + 1 < length and line[i + 1] == '>':
                tokens.append((line_num, 'ASSIGN_ARROW', '=>'))
                i += 2
                continue

            tokens.append((line_num, 'UNKNOWN', char))
            i += 1

    return tokens


def print_tokens(tokens):
    for line_num, token_type, lexeme in tokens:
        print(f"{line_num} {token_type} {lexeme}")


def parse(tokens):
    errors = []
    line_tokens = {}

    for t in tokens:
        line_num, typ, lexeme = t
        if line_num not in line_tokens:
            line_tokens[line_num] = []
        if typ != 'COMMENT':
            line_tokens[line_num].append(t)

    for line_num, lt in line_tokens.items():
        if not lt:
            continue

        types = [t[1] for t in lt]
        lexemes = [t[2] for t in lt]
        opcode = lexemes[0] if lt else ''

        if opcode not in VALID_OPCODES:
            errors.append(f"Error on line {line_num}: Unknown opcode '{opcode}'")
            continue

        def check_operand(pos, allowed_types, name):
            if types[pos] not in allowed_types:
                allowed = " or ".join(allowed_types)
                errors.append(f"Error on line {line_num}: {name} of '{opcode}' should be {allowed}, got '{types[pos]}'")

        if opcode in ['add', 'sub', 'mult', 'lshift', 'rshift']:
            if len(types) != 6:
                errors.append(f"Error on line {line_num}: '{opcode}' expects 6 tokens (opcode, operand1, ',', operand2, '=>', destination register)")
                continue

            check_operand(1, ['REGISTER', 'CONSTANT'], 'First operand')
            if types[2] != 'COMMA':
                errors.append(f"Error on line {line_num}: Missing comma between operands")
            check_operand(3, ['REGISTER', 'CONSTANT'], 'Second operand')
            if types[4] != 'ASSIGN_ARROW':
                errors.append(f"Error on line {line_num}: Invalid assignment arrow")
            check_operand(5, ['REGISTER'], 'Destination operand')

            if types[1] == 'CONSTANT' and types[3] == 'CONSTANT' and opcode in ['add', 'sub', 'mult']:
                errors.append(f"Error on line {line_num}: Cannot perform '{opcode}' on two constants; at least one operand must be a register")

        elif opcode == 'loadI':
            if len(types) != 4:
                errors.append(f"Error on line {line_num}: 'loadI' expects a constant and a destination register")
                continue
            check_operand(1, ['CONSTANT'], 'LoadI value')
            if types[2] != 'ASSIGN_ARROW':
                errors.append(f"Error on line {line_num}: Invalid assignment arrow")
            check_operand(3, ['REGISTER'], 'Destination register')

        elif opcode in ['load', 'store']:
            if len(types) != 4:
                errors.append(f"Error on line {line_num}: '{opcode}' expects a source and destination register")
                continue
            check_operand(1, ['REGISTER'], 'Operand')
            if types[2] != 'ASSIGN_ARROW':
                errors.append(f"Error on line {line_num}: Invalid assignment arrow")
            check_operand(3, ['REGISTER'], 'Destination register')

        elif opcode == 'output':
            if len(types) != 2:
                errors.append(f"Error on line {line_num}: Missing operand after 'output'")
                continue
            check_operand(1, ['REGISTER', 'CONSTANT'], 'Output operand')

        elif opcode == 'nop':
            if len(types) != 1:
                errors.append(f"Error on line {line_num}: Invalid operand for 'nop'")

        # Additional checks
        for i, typ in enumerate(types):
            lex = lexemes[i]
            if typ == 'CONSTANT':
                try:
                    val = int(lex)
                    if not -(2**31) <= val <= 2**31 - 1:
                        errors.append(f"Error on line {line_num}: Constant '{lex}' out of 32-bit integer range")
                except ValueError:
                    errors.append(f"Error on line {line_num}: Invalid constant '{lex}'")
            if typ == 'REGISTER' and not lex[1:].isdigit():
                errors.append(f"Error on line {line_num}: Invalid register name '{lex}'")
            if typ == 'ASSIGN_ARROW' and lex != '=>':
                errors.append(f"Error on line {line_num}: Invalid assignment arrow")
            if typ == 'UNKNOWN':
                errors.append(f"Error on line {line_num}: Unknown character or token '{lex}' detected")

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

        if opcode in ['add', 'sub', 'mult', 'lshift', 'rshift']:
            op1 = lt[1][1] if len(lt) > 1 else None
            op2 = lt[3][1] if len(lt) > 3 else None
            op3 = lt[5][1] if len(lt) > 5 else None
        elif opcode == 'loadI':
            op1 = lt[1][1] if len(lt) > 1 else None
            op2 = lt[3][1] if len(lt) > 3 else None
        elif opcode in ['load', 'store']:
            op1 = lt[1][1] if len(lt) > 1 else None
            op2 = lt[3][1] if len(lt) > 3 else None
        elif opcode == 'output':
            op1 = lt[1][1] if len(lt) > 1 else None
        elif opcode == 'nop':
            pass

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
        opcode = instr['opcode']
        line_num = instr['line']
        op1 = instr['op1']
        op2 = instr['op2']
        op3 = instr['op3']

        if opcode in ['add', 'sub', 'mult', 'lshift', 'rshift']:
            line = f"Line {line_num}: {opcode} — {op1}, {op2} => {op3}"
        elif opcode == 'loadI':
            line = f"Line {line_num}: {opcode} — op1: {op1} — dest: {op2}"
        elif opcode == 'load':
            line = f"Line {line_num}: {opcode} — src: {op1} — dest: {op2}"
        elif opcode == 'store':
            line = f"Line {line_num}: {opcode} — {op1} => {op2}"
        elif opcode == 'output':
            line = f"Line {line_num}: {opcode} — {op1}"
        elif opcode == 'nop':
            line = f"Line {line_num}: {opcode}"
        else:
            line = f"Line {line_num}: {opcode}"

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
        print("Compilation Successful!")
        print("VALID ILOC PROGRAM")
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
