from collections import defaultdict


def parse_afn_lambda(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    states = set()
    alphabet = set()
    transitions = {}
    initial_state = ""
    final_states = set()

    reading_transitions = False

    for line in lines:
        if line.startswith("Q:"):
            states = set(s.strip() for s in line.split(":")[1].split(","))
        elif line.startswith("∑"):
            alphabet = set(s.strip() for s in line.split(":")[1].split(","))
        elif line.startswith("δ:"):
            reading_transitions = True
        elif reading_transitions and "->" in line:
            left, right = line.split("->")
            left = left.strip()
            right = right.strip()
            state, symbol = (s.strip() for s in left.split(","))
            symbol = "λ" if symbol == "ε" else symbol
            dest_state = right

            if state not in transitions:
                transitions[state] = {}
            if symbol not in transitions[state]:
                transitions[state][symbol] = set()
            transitions[state][symbol].add(dest_state)
        elif ": inicial" in line:
            initial_state = line.split(":")[0].strip()
        elif line.startswith("F:"):
            final_states = set(s.strip() for s in line.split(":")[1].split(","))

    return states, alphabet, transitions, initial_state, final_states


# # ✅ Exemplo de uso
# file_path = "afn2.txt"  # Caminho para o seu arquivo .txt

# states, alphabet, transitions, initial_state, final_states = parse_afn_lambda(file_path)

def epsilon_closure(nfa_table, state):
    stack = [state]
    closure = set([state])

    while stack:
        current = stack.pop()
        for next_state in nfa_table[current].get("ε", []):
            if next_state not in closure:
                closure.add(next_state)
                stack.append(next_state)

    return closure

def parse_afn(file_path):
    # Constrói uma estrutura para a tabela do AFND com a coluna de fecho(epslon)
    # Retorna uma tabela representativa do AFND com fecho
    nfa_table = defaultdict(lambda: defaultdict(list))

    with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

            reading_transitions = False
            for line in lines:
                if line.startswith("δ:"):
                    reading_transitions = True
                    continue

                if reading_transitions and "->" in line:
                    left, right = line.split("->")
                    left = left.strip()
                    right = right.strip()

                    state, symbol = (s.strip() for s in left.split(","))

                    # symbol = "λ" if symbol == "ε" else symbol
                    dest_state = right
                    nfa_table[state][symbol].append(dest_state)

            

            print("\nFecho-ε:")
            all_states = set(nfa_table.keys())
            for state in all_states:
                closure = epsilon_closure(nfa_table, state)
                nfa_table[state]['closure'] = sorted(closure)
                print(f"ε-fecho({state}) = {{{', '.join(sorted(closure))}}}")

            print("Tabela de transições:")
            for state in nfa_table:
                for symbol in nfa_table[state]:
                    destinations = nfa_table[state][symbol]
                    print(f"{state}, {symbol} -> {', '.join(destinations)}")

def remove_epslon(nfa_table):
    for state in nfa_table:
        for symbol in nfa_table[state]:
                destinations = nfa_table[state][symbol]
           
file_path = "afn2.txt"  # Caminho para o seu arquivo .txt

parse_afn(file_path)

