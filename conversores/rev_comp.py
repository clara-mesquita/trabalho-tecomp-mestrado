from collections import defaultdict, deque
import re

# ★★★★★★★★★★★★★★★★#
#    LEITURA DE AFD       #
# ★★★★★★★★★★★★★★★★#

def remover_caracteres_estado(state_str):
    if state_str.strip() in ('∅', '{∅}', '{}'):
        return frozenset()
    state_str = state_str.strip()[1:-1]
    return frozenset(s.strip() for s in state_str.split(',') if s.strip())

def formatar_estado(state_set):
    return '{' + ', '.join(sorted(state_set)) + '}' if state_set else '{}'

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

    # ignora comentários e linhas vazias 
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        linhas = [l.strip() for l in f if l.strip() and not l.startswith('#')]

    # extrai conjunto de estados lendo todas as substrings do tipo {...}
    # usando frozenset pq é hashable
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

# ★★★★★★★★★★★★★★★★#
#       REVERSO           #
# ★★★★★★★★★★★★★★★★#

def reverso_afn(transicoes_dfa, estado_inicial_dfa, estados_finais_dfa):
    """
    Gera um AFN (sem ε) que reconhece L^R de um DFA completo.
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
    """
    # conjunto atual com todos os estados inciiais
    atual = set(estados_iniciais)
    for c in cadeia:
        # verifica se c pertence ao afabeto
        if c not in alfabeto:
            print(f"Símbolo inválido: '{c}'")
            return False
        prox = set()
        for q in atual:
            # conjunto de destinos via transição_afn e faz a uniao dos destinos em prox
            prox |= transicoes_afn[q].get(c, set())
        # Se não há nenhum estado possível (atual == ∅), significa que não há
        # por onde continuar a simulação
        atual = prox
        if not atual:
            return False
    return bool(atual & estados_finais)


# ★★★★★★★★★★★★★★★★#
#      COMPLEMENTO        #
# ★★★★★★★★★★★★★★★★#

def complemento_afd(estados, alfabeto, transicoes, estado_inicial, estados_finais):
    """
    Gera um AFD que reconhece ~L. Trocando estados iniciais por não finais e vice-versa
    """
    # estado morto para quando a transição de um estado com um símbolo não leva a lugar nenhum
    trap_state = frozenset({'TRAP'})

    # monta o novo conjunto de estados, incluindo o trap
    # estados2 = estados ∪ {TRAP}
    estados2 = set(estados) | {trap_state}

    # constroi as novas transicoes garantindo completude
    transicoes2 = defaultdict(lambda: defaultdict(set))
    for q in estados2:
        for a in alfabeto:
            if q in transicoes and a in transicoes[q]:
                # transição original (único destino)
                dest = next(iter(transicoes[q][a]))
            else:
                # transição indefinida vai para trap_state
                dest = trap_state
            transicoes2[q][a].add(dest)

    # trap_state é auto‐alimentado em todas as letras
    for a in alfabeto:
        transicoes2[trap_state][a].add(trap_state)

    # inverte os estados finais (exceto trap_state, que fica não-final)
    novos_finais = (estados2 - estados_finais) - {trap_state}

    return estados2, alfabeto, transicoes2, estado_inicial, novos_finais


def verificar_cadeia_afd(transicoes, inicial, finais, cadeia):
    """
    Simula uma cadeia w num DFA determinístico completo
    - Sempre há no máximo 1 estado corrente
    - Transições não definidas levam à rejeição imediata (trap state)
    """
    atual = inicial
    for c in cadeia:
        # símbolo fora do alfabeto ou sem transição definida: rejeita
        if c not in transicoes[atual]:
            print(f"Símbolo inválido: '{c}'")
            return False
        destinos = transicoes[atual][c]
        # pega o único destino
        atual = next(iter(destinos))
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

def salvar_automato_arquivo(estados, alfabeto, transicoes,
                           estado_ini, estados_fin, caminho):
    """
    Salva um AFD/AFN no arquivo. Se houver só um estado inicial
    (DFA), imprime "{q}: inicial". Se houver vários (AFN), imprime
    "Iniciais: {q}, {r}, ...".
    """
    trap = frozenset({'TRAP'})
    with open(caminho, 'w', encoding='utf-8') as f:
        # — Q:
        clean_states = [e for e in estados if e != trap]
        estados_str = ', '.join('{' + ', '.join(sorted(e)) + '}' 
                                for e in clean_states)
        f.write(f"Q: {estados_str}\n")

        # — Σ:
        alfabeto_str = ', '.join(sorted(alfabeto))
        f.write(f"∑: {alfabeto_str}\n")

        # — δ:
        f.write("δ:")
        for o, mapa in transicoes.items():
            if o == trap:
                continue
            for s, dests in mapa.items():
                for d in dests:
                    if d == trap:
                        continue
                    f.write(f"\n  {formatar_estado(o)}, {s} -> {formatar_estado(d)}")

        # — estados iniciais
        # detecta se veio um conjunto de estados ou só um estado
        if isinstance(estado_ini, (set, frozenset)) and \
           any(isinstance(x, (set, frozenset)) for x in estado_ini):
            # vários iniciais (AFN reverso)
            iniciais = sorted(estado_ini, key=lambda s: sorted(s))
            inic_str = ', '.join(formatar_estado(s) for s in iniciais)
            f.write(f"\nIniciais: {inic_str}\n")
        else:
            # um único inicial (DFA)
            f.write(f"\n{formatar_estado(estado_ini)}: inicial\n")

        # — Finais (sem trap)
        finals_clean = [e for e in estados_fin if e != trap]
        fin_str = ', '.join('{' + ', '.join(sorted(e)) + '}' 
                            for e in finals_clean)
        f.write(f"F: {fin_str}\n")

def aplicar_reverso_complemento_afd(caminho_afd, arquivo_comp, arquivo_rev, cadeia):
    estados, alfabeto, transicoes, inicial, finais = ler_afd(caminho_afd)
    print('--- AFD ORIGINAL ---')
    print('\nQ: ' + ', '.join(formatar_estado(q) for q in sorted(estados, key=lambda s: sorted(s))))
    print('\n∑: ' + ', '.join(sorted(alfabeto)))
    print('\nδ:')
    for o, mapa in transicoes.items():
        for s, dests in mapa.items():
            for d in dests:
                print(f"  {formatar_estado(o)} --{s}--> {formatar_estado(d)}")
    print('\nInicial: ' + formatar_estado(inicial))
    print('\nFinais: ' + ', '.join(formatar_estado(q) for q in sorted(finais, key=lambda s: sorted(s))))

    estados, alfabeto, transicoes_comp, inicial_comp, finais_comp = complemento_afd(estados, alfabeto, transicoes, inicial, finais)
    print('\n\n--- AFD COMPLEMENTO ---')
    print('Q: ' + ', '.join(formatar_estado(q) for q in sorted(estados, key=lambda s: sorted(s))))
    print('∑: ' + ', '.join(sorted(alfabeto)))
    print('δ:')
    for o, mapa in transicoes.items():
        for s, dests in mapa.items():
            for d in dests:
                print(f"  {formatar_estado(o)} --{s}--> {formatar_estado(d)}")
    print('Inicial: ' + formatar_estado(inicial))
    print('Finais: ' + ', '.join(formatar_estado(q) for q in sorted(finais, key=lambda s: sorted(s))))
    
    trans_rev, iniciais_rev, finais_rev = reverso_afn(transicoes, inicial, finais)
    print('\n\n--- AFND REVERSO ---')
    print('Q: ' + ', '.join(formatar_estado(q) for q in sorted(estados, key=lambda s: sorted(s))))
    print('∑: ' + ', '.join(sorted(alfabeto)))
    print('δ:')
    for o, mapa in transicoes.items():
        for s, dests in mapa.items():
            for d in dests:
                print(f"  {formatar_estado(o)}, s -> {formatar_estado(d)}")
    print('Iniciais: ' + ', '.join(
       formatar_estado(q)
       for q in sorted(iniciais_rev, key=lambda s: sorted(s))
    ))
    print('Finais: '  ', '.join(
       formatar_estado(q)
       for q in sorted(finais_rev, key=lambda s: sorted(s))
   ))
 
    print(f'\n\nCadeia: {cadeia}')
    res_comp = verificar_cadeia_afd(transicoes_comp, inicial_comp, finais_comp, cadeia)
    print("-> Complemento:")
    print("ACEITA" if res_comp else "REJEITA")
    print("-> Reverso:")
    resp_rev = verificar_cadeia_afn(cadeia, alfabeto, trans_rev, iniciais_rev, finais_rev)
    print("ACEITA" if resp_rev else "REJEITA")

    caminho_comp = f"./arquivos/saida/{arquivo_comp}"
    caminho_rev = f"./arquivos/saida/{arquivo_rev}"
    salvar_automato_arquivo(estados, alfabeto, transicoes, inicial_comp, finais_comp, caminho_comp)
    salvar_automato_arquivo(estados, alfabeto, transicoes, iniciais_rev, finais_rev, caminho_rev)
    print(f"\nArquivos salvos em {caminho_comp} e {caminho_rev}")

