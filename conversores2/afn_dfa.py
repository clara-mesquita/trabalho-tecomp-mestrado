from collections import defaultdict, deque
from io_utils.parser import parse_afn


## metodo de construção de subconjuntos 2 

def calcular_fecho_epsilon(nfa_table, state):
    closure = {state}
    changed = True

    while changed:
        changed = False
        for q in list(closure):
            for r in nfa_table[q].get("ε", []):
                if r not in closure:
                    closure.add(r)
                    changed = True

    return closure

def fecho_epsilon(file_path):
    states, alphabet, initial_state, final_states, nfa_table = parse_afn(file_path)

    for state in states:
        closure = calcular_fecho_epsilon(nfa_table, state)
        nfa_table[state]["closure"] = closure

    return states, alphabet, initial_state, final_states, nfa_table

def remover_transicao_epslon(nfa_table): #adicionar alfabeto aqui pra nao precisar pegar da tabela
    """
    Dado um nfa_table que inclui entradas "ε" e "closure", retorna um
    novo dicionário ε‐free (novo_nfa) onde:
      novo_nfa[p][a] = união dos closures de todos os destinos por 'a'
                       a partir de qualquer r em closure(p).

    Exemplo de uso:
      new_table = remover_transicao_epslon(nfa_table)
    """
    # 1) Reunir todos os estados presentes (chaves e valores)
    all_states = set(nfa_table.keys())
    for q in list(nfa_table.keys()):
        for dest_list in nfa_table[q].values():
            for dst in dest_list:
                all_states.add(dst)

    # 2) Capturar closures pré‐computadas (confiamos que nfa_table[q]["closure"] existe)
    closures = {q: set(nfa_table[q].get("closure", [q])) for q in all_states}
    print(f'closures: {closures}')

    # 3) Montar lista de símbolos reais (excluindo "ε" e "closure")
    alphabet = {
        sym
        for q in all_states
        for sym in nfa_table.get(q, {})
        if sym not in ("ε", "closure")
    }
    print(f'alphabet: {alphabet}')

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

    print("novo nfa")
    print(novo_nfa)
    return novo_nfa


def nfa_to_dfa(nfa_table, initial_state, final_states):
    # 1) Coletar todos os estados do NFA (chaves e valores)
    all_states = set(nfa_table.keys())
    for q in nfa_table:
        for dests in nfa_table[q].values():
            all_states |= dests

    # 2) Determinar alfabeto real
    alphabet = {sym for q in nfa_table for sym in nfa_table[q]}

    # 3) Estado inicial do DFA (subconjunto com o estado inicial do NFA)
    dfa_start = frozenset([initial_state])
    dfa_states = [dfa_start]      # lista de todos os subconjuntos gerados
    dfa_transitions = {}
    dfa_finals = set()

    # 4) Iterar pelos índices da lista; à medida que novos subconjuntos
    #    são adicionados, eles também serão processados
    idx = 0
    while idx < len(dfa_states):
        dstate = dfa_states[idx]
        dfa_transitions[dstate] = {}

        # Marcar como final se qualquer q ∈ dstate for final no NFA
        if any(q in final_states for q in dstate):
            dfa_finals.add(dstate)

        # Para cada símbolo, calcular o subconjunto destino
        for a in alphabet:
            target = set()
            for q in dstate:
                target |= nfa_table.get(q, {}).get(a, set())
            target = frozenset(target)

            dfa_transitions[dstate][a] = target

            # Se for um subconjunto novo, adiciona à lista
            if target and target not in dfa_states:
                dfa_states.append(target)

        idx += 1  # passa para o próximo subconjunto na lista

    return dfa_states, dfa_start, dfa_finals, dfa_transitions


def converter_afn(file_path):

    # 1) Parse do AFN-λ:
    states, alphabet, initial_state, final_states, nfa_table = fecho_epsilon(file_path)

    # 2) Remover ε-moves:
    new_table = remover_transicao_epslon(nfa_table)

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
