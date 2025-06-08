from collections import defaultdict, deque
import sys

# ——————————————————————————————————————————————————————————————
# PARSERS / IMPRESSÃO DE AUTÔMATOS
# ——————————————————————————————————————————————————————————————

def split_top_level_commas(s: str) -> list[str]:
    """
    Dado algo como '{A}, {B}, ∅' ou '{{X}, {Y}}, {Z}', retorna:
      ['{A}', '{B}', '∅'] ou ['{{X}, {Y}}', '{Z}']
    Operação “split” por vírgulas que estejam no nível zero de chaves.
    """
    items = []
    depth = 0
    current = []
    for ch in s:
        if ch == '{':
            depth += 1
            current.append(ch)
        elif ch == '}':
            depth -= 1
            current.append(ch)
        elif ch == ',' and depth == 0:
            # ponto de separação
            items.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    # resto
    if current:
        items.append("".join(current).strip())
    return items

def parse_dfa_from_txt(file_path: str):
    """
    Lê um AFD (completo e determinístico) de um arquivo de texto no formato:

    Q: {A}, {QF_S}, ∅
    Σ: a, b
    Δ:
    {A}, a -> ∅
    {A}, b -> {QF_S}
    {QF_S}, a -> {A}
    {QF_S}, b -> ∅
    ∅, a -> ∅
    ∅, b -> ∅
    q0: {QF_S}
    F: {{QF_S}}

    Retorna uma tupla (states, alphabet, transitions, initial, finals), onde:
      - states: set[str]   (cada estado é dado como, por ex., "{A}" ou "∅")
      - alphabet: set[str] (ex.: {'a', 'b'})
      - transitions: dict[(state, symbol)] -> next_state
      - initial: str       (ex.: "{QF_S}")
      - finals: set[str]   (ex.: {"{QF_S}"})

    NOTAS:
      • Usamos o nome de cada estado exatamente como aparece entre chaves
        (inclusive “{}” para o estado vazio, se houver).
      • Em “F: {{QF_S}}” há uma camada extra de chaves para indicar
        que os estados finais são os itens dentro daquele conjunto.
    """
    states: set[str] = set()
    alphabet: set[str] = set()
    transitions: dict[tuple[str, str], str] = {}
    initial: str = ""
    finals: set[str] = set()

    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    reading_delta = False
    for line in lines:
        # Q: {A}, {QF_S}, ∅
        if line.startswith("Q:"):
            rhs = line.split(":", 1)[1].strip()
            # remove o 'Q:' e pega a parte à direita
            for item in split_top_level_commas(rhs):
                states.add(item)
            continue

        # Σ: a, b
        if line.startswith("Σ") or line.startswith("S"):
            rhs = line.split(":", 1)[1].strip()
            for sym in [tok.strip() for tok in rhs.split(",")]:
                alphabet.add(sym)
            continue

        # Δ:
        if line.startswith("Δ:") or line.startswith("D"):
            reading_delta = True
            continue

        # Linhas de transição: "{A}, a -> ∅"
        if reading_delta and "->" in line:
            left, right = line.split("->")
            left = left.strip()
            right = right.strip()

            state_part, sym_part = (s.strip() for s in left.split(",", 1))
            state = state_part
            symbol = sym_part

            next_state = right
            transitions[(state, symbol)] = next_state
            continue

        # q0: {QF_S}
        if ": " in line and "inicial" not in line and "F:" not in line:
            # Detecta a linha que especifica estado inicial,
            # pode vir como "q0: {QF_S}" ou "{algum}: {BLA}"
            # mas no nosso caso, esperamos algo na forma “q0: {ESTADO}”.
            rhs = line.split(":", 1)[1].strip()
            initial = rhs
            continue

        # F: {{QF_S}}
        if line.startswith("F:"):
            rhs = line.split(":", 1)[1].strip()
            # ex: rhs = "{{QF_S}}" ou "{{A}, {B}}"
            # removemos as chaves exteriores para pegar os estados finais:
            if rhs.startswith("{") and rhs.endswith("}"):
                inner = rhs[1:-1].strip()
                for item in split_top_level_commas(inner):
                    finals.add(item)
            continue

    return states, alphabet, transitions, initial, finals

def print_dfa(states: set[str],
              alphabet: set[str],
              transitions: dict[tuple[str, str], str],
              initial: str,
              finals: set[str]):
    """
    Imprime um DFA no mesmo formato do arquivo de entrada:
      Q: {...}
      Σ: ...
      Δ:
      ...
      q0: {ESTADO_INICIAL}
      F: {...}
    """
    # 1) imprime Q:
    print("Q: " + ", ".join(sorted(states, key=lambda x: x)))
    # 2) imprime Σ:
    print("Σ: " + ", ".join(sorted(alphabet)))
    # 3) imprime Δ:
    print("Δ:")
    for (state, sym), nxt in sorted(transitions.items(), key=lambda x: (x[0][0], x[0][1])):
        print(f"{state}, {sym} -> {nxt}")
    # 4) imprime inicial:
    print(f"q0: {initial}")
    # 5) imprime F:
    print("F: {" + ", ".join(sorted(finals)) + "}")

def print_nfa_lambda(states: set[str],
                     alphabet: set[str],
                     transitions: dict[tuple[str, str], set[str]],
                     initial: str,
                     finals: set[str]):
    """
    Imprime um NFA-λ (com transições ε) num formato similar, mas aceitando ε:
      Q: {A}, {B}, ...
      Σ: a, b        (SEM ε aqui)
      Δ:
      A, a -> {X, Y}
      A, ε -> {F}
      ...
      q0: A
      F: {B}
    """
    print("Q: " + ", ".join(sorted(states)))
    print("Σ: " + ", ".join(sorted(alphabet)))
    print("Δ:")
    for (st, sym), dests in sorted(transitions.items(), key=lambda x: (x[0][0], x[0][1])):
        ds = ", ".join(sorted(dests))
        print(f"{st}, {sym} -> { {ds} }")
    print(f"q0: {initial}")
    print("F: {" + ", ".join(sorted(finals)) + "}")

# ——————————————————————————————————————————————————————————————
# OPERAÇÕES: COMPLEMENTO E REVERSO
# ——————————————————————————————————————————————————————————————

def complement_dfa(states: set[str],
                   alphabet: set[str],
                   transitions: dict[tuple[str, str], str],
                   initial: str,
                   finals: set[str]):
    """
    Dado um DFA completo e determinístico, retorna seu complemento:
      • states, alphabet e transitions permanecem os mesmos
      • initial idem
      • finals_complement = states \ finals
    """
    new_finals = states - finals
    return states, alphabet, transitions, initial, new_finals

def reverse_dfa_to_nfa(states: set[str],
                       alphabet: set[str],
                       transitions: dict[tuple[str, str], str],
                       initial: str,
                       finals: set[str]) -> tuple[
                           set[str],
                           set[str],
                           dict[tuple[str, str], set[str]],
                           str,
                           set[str]
                       ]:
    """
    Dado um DFA (full, deterministic), constrói um NFA-λ que reconhece a linguagem inversa:
      • Novo alfabeto = mesmo alfabeto original.
      • Transições invertidas: se no DFA havia p --a--> q, no NFA teremos q --a--> p.
      • Criamos um novo estado inicial "I_rev" (string fixa) que faz ε-> sobre cada
        antigo estado final. (I_rev é só string, não pertencia a states ainda.)
      • O(s) novo(s) estado(s) final(is) do NFA-reverso é(ão) { initial_original }.
      • Retornamos (new_states, alphabet, new_transitions, new_initial, new_finals).
    """
    new_states = set(states)  # vamos adicionar "I_rev" em seguida
    new_transitions: dict[tuple[str, str], set[str]] = defaultdict(set)

    # 1) inverte todas as transições originais:
    for (p, a), q in transitions.items():
        # p --a--> q  vira  q --a--> p
        new_transitions[(q, a)].add(p)

    # 2) cria um novo estado inicial “I_rev” que faz ε -> cada final original
    I_rev = "I_rev"
    new_states.add(I_rev)
    for f in finals:
        new_transitions[(I_rev, "ε")].add(f)

    # 3) nó(s) final(is) do NFA reverso é(ão) { initial_original }
    new_finals = {initial}

    return new_states, alphabet, new_transitions, I_rev, new_finals

# ——————————————————————————————————————————————————————————————
# SIMULAÇÃO: DETERMINÍSTICO E NÃO‐DETERMINÍSTICO
# ——————————————————————————————————————————————————————————————

def simulate_dfa(transitions: dict[tuple[str, str], str],
                 initial: str,
                 finals: set[str],
                 w: str) -> bool:
    """
    Simula uma cadeia w num DFA determinístico completo:
      • começa em 'initial'
      • a cada símbolo c em w, faz current = transitions[(current, c)]
      • ao final, retorna True se current ∈ finals, ou False caso contrário.
    """
    current = initial
    for c in w:
        current = transitions.get((current, c), None)
        if current is None:
            return False
    return (current in finals)

def epsilon_closure_nfa(nfa_trans: dict[tuple[str, str], set[str]],
                        states: set[str]) -> set[str]:
    """
    Dado um NFA-λ, retorne o ε‐fecho de todo o conjunto `states`.
    (expande lembretes: de cada s ∈ states, segue todas as transições ε recursivamente)
    """
    closure = set(states)
    stack = list(states)
    while stack:
        p = stack.pop()
        for r in nfa_trans.get((p, "ε"), []):
            if r not in closure:
                closure.add(r)
                stack.append(r)
    return closure

def simulate_nfa(nfa_trans: dict[tuple[str, str], set[str]],
                 initial: str,
                 finals: set[str],
                 w: str) -> bool:
    """
    Simula cadeia w num NFA-λ:
      • current_states = ε-closure({initial})
      • para cada símbolo c em w:
          next_states = ∪_{p ∈ current_states} (nfa_trans[(p, c)] se existir)
          current_states = ε‐closure(next_states)
      • ao final, retorna True se current_states ∩ finals ≠ ∅
    """
    current_states = epsilon_closure_nfa(nfa_trans, {initial})

    for c in w:
        next_set = set()
        for p in current_states:
            next_set |= nfa_trans.get((p, c), set())
        current_states = epsilon_closure_nfa(nfa_trans, next_set)

    return bool(current_states & finals)

# ——————————————————————————————————————————————————————————————
# PROGRAMA PRINCIPAL
# ——————————————————————————————————————————————————————————————

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python afd_operacoes.py <arquivo_dfa.txt> <cadeia_w>")
        sys.exit(1)

    file_path = sys.argv[1]
    w = sys.argv[2]

    # 1) Parse do AFD de entrada:
    states, alphabet, transitions, initial, finals = parse_dfa_from_txt(file_path)

    print("\n— AFD de Entrada —")
    print_dfa(states, alphabet, transitions, initial, finals)

    # 2) Gera o complemento do AFD:
    comp_states, comp_alpha, comp_trans, comp_init, comp_finals = complement_dfa(
        states, alphabet, transitions, initial, finals
    )
    print("\n— AFD Complemento —")
    print_dfa(comp_states, comp_alpha, comp_trans, comp_init, comp_finals)

    # 3) Gera o reverso do AFD (como um NFA-λ):
    rev_states, rev_alpha, rev_trans, rev_init, rev_finals = reverse_dfa_to_nfa(
        states, alphabet, transitions, initial, finals
    )
    print("\n— AFN-λ Reverso —")
    # Para impressão, transformamos rev_trans[(st, sym)] num set[str]
    print_nfa_lambda(rev_states, rev_alpha, rev_trans, rev_init, rev_finals)

    # 4) Simula w:
    print(f"\nSimulação da cadeia w = '{w}':")
    aceita_comp = simulate_dfa(comp_trans, comp_init, comp_finals, w)
    print(f"  • Em AFD Complemento: {'ACEITA' if aceita_comp else 'REJEITA'}")

    aceita_rev = simulate_nfa(rev_trans, rev_init, rev_finals, w)
    print(f"  • Em AFN-λ Reverso: {'ACEITA' if aceita_rev else 'REJEITA'}")

    # 5) Exibe, ao final, o autômato resultante de cada operação:
    #    (já foi exibido nos passos 2 e 3)
