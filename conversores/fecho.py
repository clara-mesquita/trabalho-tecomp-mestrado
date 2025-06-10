from collections import defaultdict

def remover_caracteres_extra(s):
    elementos = []
    it = 0
    atual = []
    for ch in s:
        if ch == '{':
            it += 1
            atual.append(ch)
        elif ch == '}':
            it -= 1
            atual.append(ch)
        elif ch == ',' and it == 0:
            elementos.append("".join(atual).strip())
            atual = []
        else:
            atual.append(ch)
    if atual:
        elementos.append("".join(atual).strip())
    return elementos

def extrair_afn_arquivo(caminho_arquivo):
    """
    Lê um AFD  de arquivo, garantindo totalidade das transições.
    """
    estados = set()
    alfabeto = set()
    transicoes = defaultdict(lambda: defaultdict(set))
    inicial = ""
    finais = set()

    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        linhas = [linha.strip() for linha in f if linha.strip() and not linha.startswith("#")]

    lendo_trans = False
    for linha in linhas:
        if linha.startswith("Q:"):
            rhs = linha.split(":", 1)[1].strip()
            for item in remover_caracteres_extra(rhs):
                estados.add(item)
            continue

        if linha.startswith("Σ") or linha.startswith('∑:'):
            linha_trans = linha.split(":", 1)[1].strip()
            for simb in [tok.strip() for tok in linha_trans.split(",")]:
                alfabeto.add(simb)
            continue

        if linha.startswith("Δ:") or linha.startswith("δ:"):
            lendo_trans = True
            continue
        
         # transição p, a -> q
        if lendo_trans and "->" in linha:
            esquerda, direita = linha.split("->", 1)
            esquerda = esquerda.strip()
            direita = direita.strip()
            estado, simbolo = remover_caracteres_extra(esquerda)
            transicoes[estado][simbolo].add(direita)
            continue
        
        if "inicial" in linha:
            state_str = linha.split(":", 1)[0].strip()
            inicial_raw = state_str
            if state_str in estados:
                inicial = state_str
            else:
                parts = [part.strip() for part in state_str.split(',')]
                candidate_with_spaces = '{' + ', '.join(parts) + '}'
                candidate_no_spaces = '{' + ','.join(parts) + '}'
                if candidate_with_spaces in estados:
                    inicial = candidate_with_spaces
                elif candidate_no_spaces in estados:
                    inicial = candidate_no_spaces
                else:
                    normalized_estados = {s.replace(' ', '') for s in estados}
                    normalized_candidate = candidate_with_spaces.replace(' ', '')
                    if normalized_candidate in normalized_estados:
                        for s in estados:
                            if s.replace(' ', '') == normalized_candidate:
                                inicial = s
                                break
                    else:
                        inicial = candidate_with_spaces
            continue
        if linha.startswith("F:"):
            rhs = linha.split(":", 1)[1].strip()
            for item in remover_caracteres_extra(rhs):
                finais.add(item)
    
    all_states_in_transitions = set()
    for state in list(transicoes.keys()):
        all_states_in_transitions.add(state)
        for symbol, next_states in transicoes[state].items():
            for ns in next_states:
                all_states_in_transitions.add(ns)
    estados |= all_states_in_transitions

    dead_state = '{}'
    estados.add(dead_state)
    
    # Ensure transitions are complete
    for state in estados:
        for symbol in alfabeto:
            if state == dead_state:
                transicoes[state][symbol] = {dead_state}
            else:
                if symbol not in transicoes[state] or not transicoes[state][symbol]:
                    transicoes[state][symbol] = {dead_state}

    return estados, alfabeto, transicoes, inicial, finais

def reverter_afd_para_afn(estados, alfabeto, transicoes, inicial, finais):
    novos_estados = set(estados)
    novas_transicoes = defaultdict(lambda: defaultdict(set))

    for p, mapa in transicoes.items():
        for a, dests in mapa.items():
            for q in dests:
                novas_transicoes[q][a].add(p)

    I_rev = "I_rev"
    novos_estados.add(I_rev)
    for f in finais:
        novas_transicoes[I_rev]["ε"].add(f)

    novos_finais = {inicial}

    return novos_estados, alfabeto, novas_transicoes, I_rev, novos_finais

def simular_afd(transicoes, inicial, finais, w):
    atual = inicial
    for simb in w:
        destinos = transicoes.get(atual, {}).get(simb)
        if not destinos:
            return False
        atual = next(iter(destinos))
    return atual in finais

def fechamento_afn(transicoes_afn, estados):
    fecho = set(estados)
    stack = list(estados)
    while stack:
        q = stack.pop()
        for r in transicoes_afn[q].get("ε", set()):
            if r not in fecho:
                fecho.add(r)
                stack.append(r)
    return fecho

def simular_afn(transicoes_afn, inicial, finais, w):
    estados_atuais = fechamento_afn(transicoes_afn, {inicial})
    for c in w:
        prox_cadeia = set()
        for p in estados_atuais:
            if c in transicoes_afn[p]:
                prox_cadeia |= transicoes_afn[p][c]
        estados_atuais = fechamento_afn(transicoes_afn, prox_cadeia)
    return bool(estados_atuais & finais)

def aplicar_reverso_complemento_afd(caminho_afd, cadeia):
    estados, alfabeto, transicoes, inicial, finais = extrair_afn_arquivo(caminho_afd)
    novos_finais = estados - finais
    estados_rev, rev_alpha, transicoes_rev, inicial_rev, finais_rev = reverter_afd_para_afn(estados, alfabeto, transicoes, inicial, finais)
    
    aceita_comp = simular_afd(transicoes, inicial, novos_finais, cadeia)
    aceita_rev = simular_afn(transicoes_rev, inicial_rev, finais_rev, cadeia)
    print(aceita_comp, aceita_rev)
    return aceita_comp, aceita_rev