from collections import defaultdict, deque

def parse_afn_lambda(file_path):
    """
    Lê um arquivo de AFN-λ e retorna:
      - states: conjunto de estados
      - alphabet: conjunto de símbolos (sem ε)
      - transitions: dict[state][symbol] = set(dest_states)
      - initial_state: estado inicial (string)
      - final_states: conjunto de estados finais
    Não calcula fechamento; simplesmente monta a estrutura de transições com λ.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    states = set()
    alphabet = set()
    transitions = {}
    initial_state = None
    final_states = set()
    reading_transitions = False

    for line in lines:
        if line.startswith("Q:"):
            states = {s.strip() for s in line.split(":", 1)[1].split(",")}
        elif line.startswith("∑"):
            alphabet = {s.strip() for s in line.split(":", 1)[1].split(",")}
        elif line.startswith("δ:"):
            reading_transitions = True
        elif reading_transitions and "->" in line:
            left, right = line.split("->")
            left = left.strip()
            right = right.strip()
            state, symbol = (s.strip() for s in left.split(","))
            # Converte 'ε' para 'λ' internamente, se desejar:
            symbol = "λ" if symbol == "ε" else symbol

            if state not in transitions:
                transitions[state] = {}
            if symbol not in transitions[state]:
                transitions[state][symbol] = set()
            transitions[state][symbol].add(right)
        elif ": inicial" in line:
            initial_state = line.split(":", 1)[0].strip()
        elif line.startswith("F:"):
            final_states = {s.strip() for s in line.split(":", 1)[1].split(",")}

    return states, alphabet, transitions, initial_state, final_states


def epsilon_closure(nfa_table, state):
    """
    Recebe nfa_table[state]["ε"] → lista de destinos por ε
    e retorna o conjunto completo de ε-fecho de `state`.
    """
    stack = [state]
    closure = {state}

    while stack:
        current = stack.pop()
        for next_state in nfa_table[current].get("ε", []):
            if next_state not in closure:
                closure.add(next_state)
                stack.append(next_state)

    return closure


def parse_afn(file_path):
    """
    Lê um arquivo de descrição de AFN-λ e retorna:
      - nfa_table: defaultdict onde nfa_table[q][símbolo] é lista de destinos
      - states: conjunto de estados
      - alphabet: conjunto de símbolos (sem incluir ε)
      - initial_state: estado inicial (string)
      - final_states: conjunto de estados finais

    Também imprime:
      • ε-fecho de cada estado
      • Tabela completa de transições (incluindo 'ε' e 'closure')
    """
    nfa_table = defaultdict(lambda: defaultdict(list))
    states = set()
    alphabet = set()
    initial_state = None
    final_states = set()

    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    reading_transitions = False
    for line in lines:
        if line.startswith("Q:"):
            states = {s.strip() for s in line.split(":", 1)[1].split(",")}
            continue

        if line.startswith("∑"):
            alphabet = {s.strip() for s in line.split(":", 1)[1].split(",")}
            continue

        if line.startswith("δ:"):
            reading_transitions = True
            continue

        if reading_transitions and "->" in line:
            left, right = line.split("->")
            left = left.strip()
            right = right.strip()
            state, symbol = (s.strip() for s in left.split(","))
            # Aqui mantemos 'ε' como símbolo especial:
            dest_state = right
            nfa_table[state][symbol].append(dest_state)
            continue

        if ": inicial" in line:
            initial_state = line.split(":", 1)[0].strip()
            continue

        if line.startswith("F:"):
            final_states = {s.strip() for s in line.split(":", 1)[1].split(",")}
            continue

    # 1) Calcular e armazenar ε-fecho para cada estado
    print("\nFecho-ε:")
    for state in states:
        closure = epsilon_closure(nfa_table, state)
        nfa_table[state]["closure"] = sorted(closure)
        print(f"ε-fecho({state}) = {{{', '.join(sorted(closure))}}}")

    # 2) Imprimir tabela completa de transições
    print("\nTabela de transições:")
    for state in nfa_table:
        for symbol in nfa_table[state]:
            destinations = nfa_table[state][symbol]
            print(f"{state}, {symbol} -> {', '.join(destinations)}")

    return nfa_table, states, alphabet, initial_state, final_states


def remove_epslon(nfa_table):
    """
    Dado um nfa_table que inclui entradas "ε" e "closure", retorna um
    novo dicionário ε‐free (novo_nfa) onde:
      novo_nfa[p][a] = união dos closures de todos os destinos por 'a'
                       a partir de qualquer r em closure(p).

    Exemplo de uso:
      new_table = remove_epslon(nfa_table)
    """
    # 1) Reunir todos os estados presentes (chaves e valores)
    all_states = set(nfa_table.keys())
    for q in list(nfa_table.keys()):
        for dest_list in nfa_table[q].values():
            for dst in dest_list:
                all_states.add(dst)

    # 2) Capturar closures pré‐computadas (confiamos que nfa_table[q]["closure"] existe)
    closures = {q: set(nfa_table[q].get("closure", [q])) for q in all_states}

    # 3) Montar lista de símbolos reais (excluindo "ε" e "closure")
    alphabet = {
        sym
        for q in all_states
        for sym in nfa_table.get(q, {})
        if sym not in ("ε", "closure")
    }

    # 4) Construir novo_nfa sem ε‐moves
    novo_nfa = {q: {} for q in all_states}
    for p in all_states:
        for a in alphabet:
            union_dest = set()
            for r in closures[p]:
                for s in nfa_table.get(r, {}).get(a, []):
                    union_dest |= closures[s]
            if union_dest:
                novo_nfa[p][a] = union_dest

    return novo_nfa


def nfa_to_dfa(nfa_table, initial_state, final_states):
    """
    Converte um NFA ε-free (`nfa_table[p][a] = set(destinos)`) em um DFA por
    meio da construção de subconjuntos.

    Parâmetros:
      - nfa_table: dict[state][symbol] = set(dest_states) (sem 'ε' nem 'closure')
      - initial_state: estado inicial do NFA (string)
      - final_states: set de estados finais do NFA

    Retorna uma tupla:
      (dfa_states, dfa_start, dfa_finals, dfa_transitions) onde:
        • dfa_states: lista de frozenset de estados do NFA (cada frozenset é um estado do DFA)
        • dfa_start: frozenset que representa o estado inicial do DFA
        • dfa_finals: conjunto de frozenset que são finais no DFA
        • dfa_transitions: dict[dfa_state][symbol] = target_dfa_state
    """
    # 1) Coletar todos os estados do NFA (chaves e valores) — já contidos em nfa_table
    all_states = set(nfa_table.keys())
    for q in list(nfa_table.keys()):
        for dests in nfa_table[q].values():
            all_states |= dests

    # 2) Determinar alfabeto real a partir de nfa_table (já suposto sem 'ε')
    alphabet = {sym for q in nfa_table for sym in nfa_table[q]}

    # 3) Definir o estado inicial do DFA como {initial_state}
    dfa_start = frozenset([initial_state])
    queue = deque([dfa_start])
    seen = {dfa_start}

    dfa_transitions = {}
    dfa_finals = set()

    # 4) BFS sobre subconjuntos
    while queue:
        dstate = queue.popleft()
        dfa_transitions[dstate] = {}

        # Verifica se este subconjunto contém algum estado final do NFA
        if any(q in final_states for q in dstate):
            dfa_finals.add(dstate)

        # Para cada símbolo, faz união de destinos
        for a in alphabet:
            target_subset = set()
            for q in dstate:
                target_subset |= nfa_table.get(q, {}).get(a, set())

            target_frozenset = frozenset(target_subset)
            dfa_transitions[dstate][a] = target_frozenset

            if target_frozenset and target_frozenset not in seen:
                seen.add(target_frozenset)
                queue.append(target_frozenset)

    dfa_states = list(seen)
    return dfa_states, dfa_start, dfa_finals, dfa_transitions


# ─────────────── Exemplo de uso ───────────────

if __name__ == "__main__":
    file_path = "afn_rafael.txt"  # Caminho para o seu arquivo

    # 1) Parse do AFN-λ:
    nfa_table, states, alphabet, initial_state, final_states = parse_afn(file_path)

    # 2) Remover ε-moves:
    new_table = remove_epslon(nfa_table)

    # 3) Converter NFA sem ε em DFA:
    dfa_states, dfa_start, dfa_finals, dfa_transitions = nfa_to_dfa(
        new_table, initial_state, final_states
    )

    # 4) Imprimir resultados do DFA:
    print("\nDFA States (subconjuntos de estados do NFA):")
    for s in dfa_states:
        print(f"  {s}")

    print(f"\nDFA Start State: {dfa_start}")

    print("\nDFA Final States:")
    for s in dfa_finals:
        print(f"  {s}")

    print("\nDFA Transitions:")
    for s in dfa_states:
        for a in sorted({sym for sym in dfa_transitions[s]}):
            t = dfa_transitions[s][a]
            print(f"  {s} --{a}--> {t}")
