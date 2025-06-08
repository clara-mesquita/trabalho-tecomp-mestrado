def parse_grammar(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    productions = []
    non_terminals = set()
    terminals = set()

    for line in lines:
        left, right = line.split('->')
        left = left.strip()
        right = right.strip()
        non_terminals.add(left)

        if right == 'ε':
            productions.append((left, 'ε', None))
        elif len(right) == 1:
            terminals.add(right)
            productions.append((left, right, None))
        elif len(right) == 2:
            terminals.add(right[0])
            productions.append((left, right[0], right[1]))
        else:
            raise ValueError("Formato de produção inválido: " + line)

    return productions, non_terminals, terminals

def build_afn(productions, non_terminals, terminals):
    states = non_terminals.union({'Z'})
    initial_state = 'S'
    final_state = 'Z'
    transitions = []

    for left, symbol, right in productions:
        if symbol == 'ε':
            transitions.append((left, 'ε', final_state))
        elif right is None:
            transitions.append((left, symbol, final_state))
        else:
            transitions.append((left, symbol, right))

    return states, terminals, transitions, initial_state, final_state

def save_afn_to_file(states, terminals, transitions, initial_state, final_state, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# AFN Original\n")
        f.write(f"Q: {', '.join(states)}\n")
        f.write(f"∑: {', '.join(terminals)}\n")
        f.write("δ:\n")
        for from_state, symbol, to_state in transitions:
            f.write(f"{from_state}, {symbol} -> {to_state}\n")
        f.write(f"{initial_state}: inicial\n")
        f.write(f"F: {final_state}\n")

# Uso
input_path = 'gramatica.txt'
output_path = 'afn_saida.txt'

productions, non_terminals, terminals = parse_grammar(input_path)
states, terminals, transitions, initial_state, final_state = build_afn(productions, non_terminals, terminals)
save_afn_to_file(states, terminals, transitions, initial_state, final_state, output_path)
print("AFN gerado com sucesso em", output_path)
