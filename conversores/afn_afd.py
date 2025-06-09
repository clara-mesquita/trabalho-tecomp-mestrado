
from collections import defaultdict

def extrair_afn_arquivo(caminho_arquivo):
    """
    Extrai informações do arquivo com AFND no formato:
    `# AFN Original 
    Q: {conjunto de estados}
    Σ: {conjunto com alfabeto}
    δ: {transições de estados depois de conversão de produções}
    {estado inicial}: inicial
    F: {estado final}`
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

        if linha.startswith(('Σ:', '∑:', 'P:')):
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

    return estados, alfabeto, estado_inicial, estados_finais, afn_epslon

def calcular_afn_fecho(estados, afn_epslon, alfabeto): 
    """
    Função para calcular o fecho(ε) dos estados 
    e adicionar ao AFND para que o ε possa ser removido

    fecho[q] é o conjunto de todos os estados alcançáveis a partir de q usando apenas transições ε (incluindo q)
    """       

    # Percorre todos os estados
    for estado in estados:
        fecho = {estado}
        changed = True

        # EEncontrarmos novos estados via ε
        while changed:
            changed = False
            # Itera sobre a cópia dos estados já no fecho
            for q in list(fecho):
                # Para cada destino alcançável por ε a partir de q
                for r in afn_epslon[q].get("ε", []):
                    if r not in fecho:
                        fecho.add(r)
                        changed = True

        afn_epslon[estado]["fecho"] = fecho               
    
    alfabeto.discard("ε") # Agora as operações com alfabeto não vão considerar mais o ε
    return afn_epslon, alfabeto

def remover_transicao_vazia(estados, alfabeto_sem_epslon, estado_inicial, afn_epslon):
    """
    Essa função remove as transições ε de um AFND.
    """

    # Capturar fechos(ε) pré-computados
    fechamento = {q: set(afn_epslon[q].get("fecho", [q])) for q in estados}

    afn = defaultdict(lambda: defaultdict(set))

    for p in estados:
        # Para cada símbolo a do alfabeto sem ε:
        for a in alfabeto_sem_epslon:
            # Junta todos os destinos que podem ser alcançados de cada estado r em fechamento[q], via uma transição r —a→ s,
            # seguido de todas as transições-ε a partir de s.
            dest_uni = frozenset()  # Utilizando frozenset pois é um set que mantem a mesma ordem e é hashable
            for r in fechamento[p]:
                for s in afn_epslon.get(r, {}).get(a, []):
                    dest_uni |= fechamento[s]
            if dest_uni:
                afn[p][a] = dest_uni
            else:
                afn[p][a] = afn_epslon[p][a]

    inicio_afd = frozenset(afn_epslon[estado_inicial].get("fecho", {estado_inicial}))
    return afn, inicio_afd

def converter_afn_afd(alfabeto, inicio_afd, estados_finais, afn):
    """
    Essa função faz a conversão do NFA sem transições vazias no DFA 
    """

    # O estado inicial do AFD é o conjunto dos subconjuntos iniciais do AFN (ou seja, o fecho(estado_inicial))
    estados_afd = [inicio_afd]      
    transicoes_afd = defaultdict(lambda: defaultdict(set))
    finais_afd = set()

    print(f"\n>> Estado inicial do AFD: {set(inicio_afd)}\n")

    idx = 0
    # Para cada estado do AFD 
    while idx < len(estados_afd):
        estado_atual = estados_afd[idx]

        # Mantem o mesmo final do AFND
        if any(q in estados_finais for q in estado_atual):
            finais_afd.add(estado_atual)

        # Para cada símbolo do alfabeto, calcula o destino
        for a in alfabeto:
            target = set()
            # Une todos os destinos de cada q ∈ estado_atual via a
            for q in estado_atual:
                target |= afn.get(q, {}).get(a, set())
            target = frozenset(target)

            transicoes_afd[estado_atual][a] = target
            print(f"  δ({set(estado_atual)}, '{a}') = {set(target)}")

            # Se for um subconjunto novo, adiciona à lista
            if target:
                transicoes_afd[estado_atual][a] = target
                if target not in estados_afd:
                    estados_afd.append(target)

        print("") 
        idx += 1  

    return estados_afd, inicio_afd, finais_afd, transicoes_afd

def salvar_afd_arquivo(estados, alfabeto, transicoes, estado_ini, estados_fin, caminho_afd):
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

def converter_afn(caminho_arquivo, nome_arquivo):
    # afn epslon (original) -> afn fecho -> afn -> afd
    estados, alfabeto, estado_inicial, estados_finais, afn_epslon = extrair_afn_arquivo(caminho_arquivo)
    print("\n--- AFND-ε ORIGINAL ---")
    print("Q:", estados)
    print("Σ:", alfabeto)
    print("Estado inicial:", estado_inicial)
    print("Estados finais:", estados_finais)
    print("Transições AFND-ε:")
    for origem, destinos in afn_epslon.items():
        print(f"  {origem} -> {dict(destinos)}")
    
      
    afn_fecho, alfabeto = calcular_afn_fecho(estados, afn_epslon, alfabeto)
    print("\n--- AFND FECHO (ε) ---")
    simbolos = sorted({s for mapa in afn_epslon.values() for s in mapa.keys() if s != 'fecho'})
    header = ['Estado'] + simbolos + ['fecho']
    print('\t'.join(f"{h:^12}" for h in header))
    for estado in sorted(estados):
        row = [f"{estado:^12}"]
        mapa = afn_epslon.get(estado, {})
        for simb in simbolos:
            dest = mapa.get(simb, set())
            row.append(f"{{{', '.join(sorted(dest))}}}".center(12))
        fecho = mapa.get('fecho', set())
        row.append(f"{{{', '.join(sorted(fecho))}}}".center(12))
        print('\t'.join(row))

    afn, inicio_afd = remover_transicao_vazia(estados, alfabeto, estado_inicial, afn_fecho)
    print("\n--- AFND SEM TRANSIÇÕES-ε ---")
    simbolos = sorted({s for mapa in afn.values() for s in mapa.keys() if s != 'fecho'})
    header = ['Estado'] + simbolos 
    print('\t'.join(f"{h:^12}" for h in header))
    for estado in sorted(estados):
        row = [f"{estado:^12}"]
        mapa = afn.get(estado, {})
        for simb in simbolos:
            dest = mapa.get(simb, set())
            row.append(f"{{{', '.join(sorted(dest))}}}".center(12))
        print('\t'.join(row))

    estados_afd, inicio_afd, finais_afd, transicoes_afd = converter_afn_afd(alfabeto, inicio_afd, estados_finais, afn)
    print("\n--- AFD SEM TRANSIÇÕES-ε ---")
    simbolos = sorted({s for mapa in afn.values() for s in mapa.keys() if s != 'fecho'})
    header = ['Estado'] + simbolos 
    print('\t'.join(f"{h:^12}" for h in header))
    for estado in sorted(estados_afd, key=lambda fs: sorted(fs)):
        estado_str = '{' + ', '.join(sorted(estado)) + '}'
        row = [f"{estado_str:^12}"]

        mapa = transicoes_afd.get(estado, {})
        for simb in simbolos:
            dest = mapa.get(simb, set())
            dest_str = '{' + ', '.join(sorted(dest)) + '}'
            row.append(f"{dest_str:^12}")
        print('\t'.join(row))

    caminho_saida = f'./arquivos/saida/{nome_arquivo}'
    salvar_afd_arquivo(estados_afd, alfabeto, transicoes_afd, inicio_afd, finais_afd, caminho_saida)
    print(f"\nArquivo salvo em {caminho_saida}")
