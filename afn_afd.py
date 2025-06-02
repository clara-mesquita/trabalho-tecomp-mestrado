from collections import defaultdict, deque
import re

# ---------- Etapa 1: Leitura do arquivo AFN ----------
def parse_afn_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    states = []
    alphabet = []
    transitions = defaultdict(lambda: defaultdict(list))
    start_state = ''
    final_states = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("Q:"):
            states = [s.strip() for s in line[2:].strip().split(",")]
        elif line.startswith("∑") or line.startswith("Σ") or line.startswith("S:"):
            alphabet = [s.strip() for s in line.split(":")[1].split(",")]
        elif line.startswith("δ:") or line.startswith("d:"):
            continue  # header of transitions
        elif "->" in line:
            # Ex: q0, a -> q1
            match = re.match(r"(.+?),\s*(.+?)\s*->\s*(.+)", line)
            if match:
                from_state, symbol, to_state = match.groups()
                transitions[from_state.strip()][symbol.strip()].append(to_state.strip())
        elif ": inicial" in line:
            start_state = line.split(":")[0].strip()
        elif line.startswith("F:"):
            final_states = [s.strip() for s in line[2:].strip().split(",")]

    return states, alphabet, transitions, start_state, final_states

# ---------- Etapa 2: Conversão AFN → AFD ----------
def epsilon_closure(nfa_transitions, state_set):
    stack = list(state_set)
    closure = set(state_set)

    while stack:
        state = stack.pop()
        for next_state in nfa_transitions[state].get('ε', []):
            if next_state not in closure:
                closure.add(next_state)
                stack.append(next_state)
    return closure

def convert_nfa_to_dfa(nfa_states, alphabet, nfa_transitions, nfa_start_state, nfa_final_states):
    alphabet = [sym for sym in alphabet if sym != 'ε']
    dfa_states = []
    dfa_transitions = {}
    dfa_final_states = set()

    state_name_map = {}
    name_counter = 0

    start_closure = frozenset(epsilon_closure(nfa_transitions, {nfa_start_state}))
    queue = deque([start_closure])
    state_name_map[start_closure] = f'q{name_counter}'
    name_counter += 1
    dfa_states.append(start_closure)

    while queue:
        current = queue.popleft()
        current_name = state_name_map[current]
        dfa_transitions[current_name] = {}

        for symbol in alphabet:
            next_states = set()
            for state in current:
                targets = nfa_transitions[state].get(symbol, [])
                for t in targets:
                    next_states.update(epsilon_closure(nfa_transitions, {t}))
            next_states = frozenset(next_states)

            if not next_states:
                continue
            if next_states not in state_name_map:
                state_name_map[next_states] = f'q{name_counter}'
                name_counter += 1
                queue.append(next_states)
                dfa_states.append(next_states)

            dfa_transitions[current_name][symbol] = state_name_map[next_states]

    for state_set, name in state_name_map.items():
        if any(s in nfa_final_states for s in state_set):
            dfa_final_states.add(name)

    dfa_start_state = state_name_map[start_closure]

    return {
        "states": list(state_name_map.values()),
        "alphabet": alphabet,
        "transitions": dfa_transitions,
        "start_state": dfa_start_state,
        "final_states": list(dfa_final_states)
    }

# ---------- Etapa 3: Uso ----------
if __name__ == "__main__":
    path = "afn.txt"
    nfa_states, alphabet, nfa_transitions, start, finals = parse_afn_file(path)
    dfa = convert_nfa_to_dfa(nfa_states, alphabet, nfa_transitions, start, finals)

    # Exibição do DFA
    print("\nAFD Gerado:")
    print("Estados:", dfa["states"])
    print("Alfabeto:", dfa["alphabet"])
    print("Estado Inicial:", dfa["start_state"])
    print("Estados Finais:", dfa["final_states"])
    print("Transições:")
    for state, trans in dfa["transitions"].items():
        for symbol, dest in trans.items():
            print(f"  δ({state}, {symbol}) -> {dest}")
