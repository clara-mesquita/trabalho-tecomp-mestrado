
from collections import defaultdict

def extrair_afn_arquivo(caminho_arquivo):
    """
    Essa função extrai informações do arquivo no formato:
    # AFN Original 
    Q: {conjunto_estados}
    ∑: {conjunto_alfabeto}
    δ: {transicoes}
    {estado_inicial}: inicial
    F: {conjunto_estados_finais}
    """

    linhas_arquivo = []
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        for raw in f:
            conteudo = raw.strip()
            if conteudo.startswith('#'):
                continue

            linhas_arquivo.append(conteudo)

    afn_epslon = defaultdict(lambda: defaultdict(set))
    estados = set()
    alfabeto = set()
    estado_inicial = None
    estados_finais = set()

    # Tratando arquivo com AFN linha por linha
    lendo_transicoes = True
    for linha in linhas_arquivo:
        if linha.startswith("Q:"):
            estados = {s.strip() for s in linha.split(":", 1)[1].split(",")}
            continue

        if linha.startswith(('Σ:', '∑:', 'S:')):
            alfabeto = {s.strip() for s in linha.split(":", 1)[1].split(",")}
            continue

        if linha.startswith("δ:"):
            lendo_transicoes = True
            continue

        if lendo_transicoes and "->" in linha:
            esquerda, direita = linha.split("->")
            esquerda = esquerda.strip()
            direita = direita.strip()
            estado, simb = (s.strip() for s in esquerda.split(","))
            dest_estado = direita
            afn_epslon[estado][simb].add(dest_estado)
            continue

        if ": inicial" in linha:
            estado_inicial = linha.split(":", 1)[0].strip()
            continue

        if linha.startswith("F:"):
            estados_finais = {s.strip() for s in linha.split(":", 1)[1].split(",")}
            continue

    print("\n--- AFN COM EPSILON ORIGINAL ---")
    print("Estados:", estados)
    print("Alfabeto:", alfabeto)
    print("Estado inicial:", estado_inicial)
    print("Estados finais:", estados_finais)
    print("Transições AFN ε:")
    for origem, destinos in afn_epslon.items():
        print(f"  {origem} -> {dict(destinos)}")

    return estados, alfabeto, estado_inicial, estados_finais, afn_epslon

def calcular_afn_fecho(estados, afn_epslon):    
    for estado in estados:
        fecho = {estado}
        changed = True

        while changed:
            changed = False
            for q in list(fecho):
                for r in afn_epslon[q].get("ε", []):
                    if r not in fecho:
                        fecho.add(r)
                        changed = True

        afn_epslon[estado]["fecho"] = fecho

    print("\n--- AFN COM FECHO-ε CALCULADO ---")

    for origem, mapa in afn_epslon.items():
            origem_str = '{' + ', '.join(sorted(origem)) + '}'
            for simbolo, destino in mapa.items():
                destino_str = '{' + ', '.join(sorted(destino)) + '}'
                print(f"{origem_str}, {simbolo} -> {destino_str}")
               
    
    return afn_epslon

def remover_transicao_vazia(estados, alfabeto, afn_epslon):
    """
    Essa função remove as transições ε de um AFND.

    O returno é um novo dict afn sem qualquer transição ε, mas que aceita 
    exatamente a mesma linguagem, porque toda a lógica  dos saltos vazios 
    foi incorporada nas transições sobre símbolos concretos.
    """

    # Capturar fechos(ε) pré-computados
    # fechos[q] é o conjunto de todos os estados alcançáveis a partir de q usando apenas transições ε (incluindo q)
    fechos = {q: set(afn_epslon[q].get("fecho", [q])) for q in estados}

    """
    Para cada símbolo a do alfabeto (exceto ε):
    - Junta, em um conjunto auxiliar `estados_unificados`, todos os destinos 
        que podem ser alcançados assim:
        a) de cada estado r em fechos[q],
        b) via uma transição r —a→ s,
        c) seguido de todas as transições-ε a partir de s (ou seja, fechos[s]).
    - Isso equivale a “pulverizar” a transitividade do ε:
        q —ε*→ r —a→ s —ε*→ t  torna-se  q —a→ t diretamente.
        Se `estados_unificados` não estiver vazio, adiciona essa transição 
    consolidada em `afn[ q ][ a ] = estados_unificados`.
    """
    afn = defaultdict(lambda: defaultdict(set))
    for p in estados:
        for a in alfabeto:
            dest_uni = set()
            for r in fechos[p]:
                for s in afn_epslon.get(r, {}).get(a, []):
                    dest_uni |= fechos[s]
            if dest_uni:
                afn[p][a] = dest_uni
            else:
                afn[p][a] = afn_epslon[p][a]

    print("\n--- AFN APÓS REMOÇÃO DE ε  ---")
    for origem, mapa in afn.items():
            origem_str = '{' + ', '.join(sorted(origem)) + '}'
            for simbolo, destino in mapa.items():
                destino_str = '{' + ', '.join(sorted(destino)) + '}'
                print(f"{origem_str}, {simbolo} -> {destino_str}")

    return afn

def converter_afn_afd(alfabeto, inicio_afd, estados_finais, afn):
    """
    Essa função faz a conversão do NFA sem transições vazias no DFA com construção de subconjuntos
    """

    # O estado inicial do AFD é o conjunto dos subconjuntos iniciais do AFN (ou seja, o fecho(estado_inicial))
    # Utilizando frozenset pois é um set que mantem a mesma ordem
    estados_afd = [inicio_afd]      
    transicoes_afd = defaultdict(lambda: defaultdict(set))
    finais_afd = set()

    idx = 0
    while idx < len(estados_afd):
        estado_atual = estados_afd[idx]

        # Marcar como final se qualquer q ∈ estado_atual for final no NFA
        if any(q in estados_finais for q in estado_atual):
            finais_afd.add(estado_atual)

        # Para cada símbolo, calcular o subconjunto destino
        for a in alfabeto:
            target = set()
            for q in estado_atual:
                target |= afn.get(q, {}).get(a, set())
            target = frozenset(target)

            transicoes_afd[estado_atual][a] = target

            # Se for um subconjunto novo, adiciona à lista
            if target:
                transicoes_afd[estado_atual][a] = target
                if target not in estados_afd:
                    estados_afd.append(target)

        idx += 1  # passa para o próximo subconjunto na lista

    print("\n--- AFD DETERMINIZADO ---")
    print("Estados AFD:", estados_afd)
    print("Estado inicial AFD:", inicio_afd)
    print("Estados finais AFD:", finais_afd)
    print("Transições AFD:")
    for origem, mapa in transicoes_afd.items():
            origem_str = '{' + ', '.join(sorted(origem)) + '}'
            for simbolo, destino in mapa.items():
                destino_str = '{' + ', '.join(sorted(destino)) + '}'
                print(f"{origem_str}, {simbolo} -> {destino_str}")

    return estados_afd, inicio_afd, finais_afd, transicoes_afd

def salvar_afd_arquivo(estados, alfabeto, transicoes, estado_ini, estados_fin, caminho_afd='./arquivos/afd.txt'):
    """
    Salva o AFD corretamente formatado no arquivo.
    """
    with open(caminho_afd, 'w', encoding='utf-8') as f:
        f.write("# AFD Determinizado\n")

        estados_str = ', '.join(['{' + ', '.join(sorted(e)) + '}' for e in estados])
        f.write(f"Q: {estados_str}\n")

        alfabeto_str = ', '.join(sorted(alfabeto))
        f.write(f"∑: {alfabeto_str}\n")

        f.write("δ:\n")
        for origem, mapa in transicoes.items():
            origem_str = '{' + ', '.join(sorted(origem)) + '}'
            for simbolo, destino in mapa.items():
                destino_str = '{' + ', '.join(sorted(destino)) + '}'
                f.write(f"{origem_str}, {simbolo} -> {destino_str}\n")

        estado_ini_str = '{' + ', '.join(sorted(estado_ini)) + '}'
        f.write(f"{estado_ini_str}: inicial\n")


        estados_fin_str = ', '.join(['{' + ', '.join(sorted(e)) + '}' for e in estados_fin])
        f.write(f"F: {estados_fin_str}\n")


def converter_afn(caminho_arquivo):
    # nfa epslon -> nfa fecho -> nfa -> dfa
    estados, alfabeto, estado_inicial, estados_finais, afn_epslon = extrair_afn_arquivo(caminho_arquivo)
    print("alfabeto")
    print(alfabeto)
    alfabeto.discard("ε")
    afn_fecho = calcular_afn_fecho(estados, afn_epslon)
    afn = remover_transicao_vazia(estados, alfabeto, afn_fecho)

    inicio_afd = frozenset(afn_epslon[estado_inicial].get("fecho", {estado_inicial}))
    estados_afd, inicio_afd, finais_afd, transicoes_afd = converter_afn_afd(alfabeto, inicio_afd, estados_finais, afn)

    salvar_afd_arquivo(estados_afd, alfabeto, transicoes_afd, inicio_afd, finais_afd)

