from collections import defaultdict, deque
import re

def remover_caracteres_estado(state_str):
    if state_str.strip() == '{}':
        return frozenset()
    state_str = state_str.strip()[1:-1]
    return frozenset(s.strip() for s in state_str.split(',') if s.strip())

def formatar_estado(state_set):
    return '{' + ', '.join(sorted(state_set)) + '}' if state_set else '{}'

def reverso_afn(transicoes_dfa, estado_inicial_dfa, estados_finais_dfa):
    """
    Gera um AFN (sem ε) que reconhece L^R de um DFA completo.
      - transicoes_dfa: dict[state][symbol] = {next_state}
      - estado_inicial_dfa: frozenset
      - estados_finais_dfa: set of frozensets
    Retorna:
      - transicoes_rev: dict[state][symbol] = set(prev_states)
      - iniciais_rev: set of states
      - finais_rev: set of states
    """
    transicoes_rev = defaultdict(lambda: defaultdict(set))
    # inverter todas as transições
    for src, mapa in transicoes_dfa.items():
        for a, dests in mapa.items():
            for q in dests:
                transicoes_rev[q][a].add(src)
    # estados inicias do AFN-reverso são os finais do DFA original
    iniciais_rev = set(estados_finais_dfa)
    # estados finais do AFN-reverso é apenas o inicial do DFA original
    finais_rev = {estado_inicial_dfa}
    return transicoes_rev, iniciais_rev, finais_rev

def verificar_cadeia_afn(cadeia, alfabeto, transicoes_afn, estados_iniciais, estados_finais):
    """
    Simula um AFN (sem ε) sobre a cadeia.
      - Começamos no set estados_iniciais.
      - Para cada símbolo, movemos para o conjunto de todos os destinos possíveis.
      - Ao fim, aceitamos se houver interseção com estados_finais.
    """
    atual = set(estados_iniciais)
    for c in cadeia:
        if c not in alfabeto:
            print(f"Símbolo inválido: '{c}'")
            return False
        prox = set()
        for q in atual:
            prox |= transicoes_afn[q].get(c, set())
        atual = prox
        if not atual:
            return False
    return bool(atual & estados_finais)

def ler_afd(caminho_arquivo):
    """
    Lê AFD no seguinte formato:
    `# AFD Determinizado
    Q: {conjunto de estados}
    Σ: {conjunto com alfabeto}
    δ: {transições de estados depois de conversão de produções}
    {estado inicial}: inicial
    F: {estado final}`
    """
    estados = set()
    alfabeto = set()
    transicoes = defaultdict(lambda: defaultdict(set))
    estado_inicial = frozenset()
    estados_finais = set()

    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        linhas = [l.strip() for l in f if l.strip() and not l.startswith('#')]

    if not linhas[0].startswith("Q:") or not linhas[1].startswith("∑:") or "δ:" not in linhas[2]:
        raise ValueError("Formato inválido de cabeçalho")

    estados_raw = re.findall(r'\{[^{}]*\}', linhas[0])
    for s in estados_raw:
        estados.add(remover_caracteres_estado(s))

    alfabeto = frozenset(x.strip() for x in linhas[1][2:].strip().split(','))
    
    i = 3
    while i < len(linhas):
        linha = linhas[i]
        if ': inicial' in linha:
            estado_inicial = remover_caracteres_estado(linha.split(':')[0])
            break
        match = re.match(r'(\{[^{}]*\})\s*,\s*(\w)\s*->\s*(\{[^{}]*\})', linha)
        if match:
            origem, simbolo, destino = match.groups()
            transicoes[remover_caracteres_estado(origem)][simbolo].add(remover_caracteres_estado(destino))
        i += 1

    i += 1
    if i < len(linhas) and linhas[i].startswith("F:"):
        finais_raw = re.findall(r'\{[^{}]*\}', linhas[i])
        for s in finais_raw:
            estados_finais.add(remover_caracteres_estado(s))

    return estados, alfabeto, transicoes, estado_inicial, estados_finais

def complementar_dfa(estados, alfabeto, transicoes, estado_inicial, estados_finais):
    """
    Gera um AFD que reconhece ~L. Trocando estados iniciais por não finais e vice-versa
    """
    trap_state = frozenset({'TRAP'})

    # monta o novo conjunto de estados, incluindo o trap
    estados2 = set(estados) | {trap_state}

    # constroi as novas transicoes garantindo completude
    transicoes2 = defaultdict(lambda: defaultdict(set))
    for q in estados2:
        for a in alfabeto:
            if q in transicoes and a in transicoes[q]:
                # transição original (único destino)
                dest = next(iter(transicoes[q][a]))
            else:
                # transição indefinida → vai para trap_state
                dest = trap_state
            transicoes2[q][a].add(dest)

    # trap_state é auto‐alimentado em todas as letras
    for a in alfabeto:
        transicoes2[trap_state][a].add(trap_state)

    # inverte os estados finais (exceto trap_state, que fica não-final)
    novos_finais = (estados2 - estados_finais) - {trap_state}

    return estados2, alfabeto, transicoes2, estado_inicial, novos_finais

def verificar_cadeia_dfa(cadeia, alfabeto, transicoes, estado_inicial, estados_finais):
    """
    Verifica se uma cadeia é aceita por um DFA
    """
    estado_atual = estado_inicial

    for simbolo in cadeia:
        if simbolo not in alfabeto:
            print(f"Símbolo inválido: '{simbolo}'")
            return False

        if simbolo not in transicoes[estado_atual]:
            return False  # Transição indefinida → rejeita

        estado_atual = transicoes[estado_atual][simbolo]

    return estado_atual in estados_finais

def processar_cadeia(transicoes, inicial, finais, cadeia):
    """
    Simula uma cadeia w num DFA determinístico completo:
    """
    atual = inicial
    print("Passando pelo estado:", formatar_estado(atual))
    for c in cadeia:
        # símbolo fora do alfabeto ou sem transição definida: rejeita
        if c not in transicoes[atual]:
            print(f"sem δ({formatar_estado(atual)},'{c}')")
            return False
        destinos = transicoes[atual][c]
        # pega o único destino
        atual = next(iter(destinos))
        print("Passando pelo estado:", formatar_estado(atual))
    return atual in finais

def elimina_nao_alcancaveis(transicoes, start):
    """
    Retorna o conjunto de estados alcançáveis a partir de 'começo'em um AFN-ε 
    """
    alcancaveis = {start}
    while True:
        novo = set(alcancaveis)  
        for q in alcancaveis:
            for dests in transicoes[q].values():
                novo |= dests
        if novo == alcancaveis:
            break
        alcancaveis = novo
    return alcancaveis

# def reverso_afd(estados, alfabeto, transicoes, inicial, finais):
#     """
#     Gera um AFN-ε que reconhece L^R
#     """
#     # Inverte transições
#     afn_rev = defaultdict(lambda: defaultdict(set))
#     for q, mapa in transicoes.items():
#         for a, dests in mapa.items():
#             for d in dests:
#                 afn_rev[d][a].add(q)

#     # Cria novos estados especiais
#     inicial_rev = frozenset({'__INICIAL_REV__'})
#     rev_final = frozenset({'__REV_FINAL__'})
#     estados_rev = set(estados) | {inicial_rev, rev_final}

#     # liga ε do novo inicio aos finais originais
#     for f in finais:
#         afn_rev[inicial_rev]['ε'].add(f)
#     #    e liga ε do inicial original ao novo final
#     afn_rev[inicial]['ε'].add(rev_final)

#     # monta novo alfabeto (com ε)
#     alfabeto_rev = set(alfabeto) | {'ε'}

#     # elimina estados não alcançáveis (incluindo via ε)
#     alcancaveis = elimina_nao_alcancaveis(afn_rev, inicial_rev)

#     # 6) filtra transições e estados
#     transicoes_rev = defaultdict(lambda: defaultdict(set))
#     for q in alcancaveis:
#         for a, dests in afn_rev[q].items():
#             transicoes_rev[q][a] = {d for d in dests if d in alcancaveis}

#     estados_rev = alcancaveis
#     inicial_rev = inicial_rev
#     finais_rev = {rev_final}

#     estados_rev = alcancaveis
#     transicoes_rev = {
#         q: {a: dests & alcancaveis
#             for a, dests in mapa.items()}
#         for q, mapa in transicoes_rev.items()
#         if q in alcancaveis
#     }

#     return estados_rev, alfabeto_rev, transicoes_rev, inicial_rev, finais_rev

def aplicar_reverso_complemento_afd(caminho_afd, cadeia):
    estados, alfabeto, transicoes, inicial, finais = ler_afd(caminho_afd)

    estados_comp, alfabeto_comp, transicoes_comp, inicial_comp, finais_comp = complementar_dfa(estados, alfabeto, transicoes, inicial, finais)
    
    resultado = processar_cadeia(transicoes_comp, inicial_comp, finais_comp, cadeia)
    print("ACEITA" if resultado else "REJEITA")

    trans_rev, iniciais_rev, finais_rev = reverso_afn(transicoes, inicial, finais)

    aceito = verificar_cadeia_afn(cadeia, alfabeto, trans_rev, iniciais_rev, finais_rev)
    print("REVERSE ACEITA" if aceito else "REVERSE REJEITA")
