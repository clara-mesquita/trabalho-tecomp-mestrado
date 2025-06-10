import re
from collections import defaultdict

def expandir_producoes_glud(linhas):
    """
    Recebe uma lista de strings no formato 'A -> x | yB | ε'
    e retorna outra lista com cada alternativa isolada: ['A -> x', 'A -> yB', 'A -> ε']
    """
    expandidas = []
    for linha in linhas:
        # separa lado esquerdo e direito
        if '->' not in linha:
            continue
        esq, dir_raw = linha.split('->', 1)
        esq = esq.strip()
        # para cada alternativa separada por '|'
        for alt in dir_raw.split('|'):
            alt = alt.strip()
            if alt:
                expandidas.append(f"{esq} -> {alt}")
    return expandidas


def extrair_glud_arquivo(caminho_arquivo):
    """
    Lê arquivo da gramática de entrada no formato:
    `# Gramática: G = ({conjunto_nao_terminais}, {conjunto_terminais}, P, estado_inicial)

    D -> aA
    A -> bD
    D -> ε`

    Extrai o cabeçalho (primeira linha) e as produções (demais linhas)
    
    Processa o cabeçalho e produções do arquivo e retorna os elementos
    da gramática (estado inicial, símbolos terminais, símb. não terminais e produções)
    
    """
    cabecalho_arquivo = None
    producoes_arquivo = []

    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        for entrada in f:
            conteudo = entrada.strip()
            if not conteudo: 
                continue
            
            if cabecalho_arquivo is None and conteudo.startswith('#'):
                cabecalho_arquivo = conteudo
                continue

            producoes_arquivo.append(conteudo)

    # Regex para tratar aquivo e extrair elementos
    regex = re.compile(
        r"""
        Gramática      
        \s*:\s*        
        G              
        \s*=\s*\(      
            \{\s*([^}]*)\s*\}         # grupo(1) = não-terminais entre chaves
            \s*,\s*\{\s*([^}]*)\s*\}  # grupo(2) = terminais entre chaves
            \s*,\s*P\s*,\s*           # ignora o “P”
            ([^\s\)]+)                # grupo(3) = símbolo/estado inicial
        \s*\)

        """,
        re.VERBOSE
    )

    cabecalho_regex = regex.search(cabecalho_arquivo)

    nao_terminais = set()
    terminais = set()

    for x in cabecalho_regex.group(1).split(','):
        simb = x.strip()
        if simb:
            nao_terminais.add(simb)

    for x in cabecalho_regex.group(2).split(','):
        simb = x.strip()
        if simb:
            terminais.add(simb)

    estado_inicial = cabecalho_regex.group(3)

    return estado_inicial, nao_terminais, terminais, producoes_arquivo

def extrair_producoes(producoes_arquivo):
    """
    Extrai as produções a partir das produções do arquivo no formato:
    `D -> aA
    A -> bD
    D -> ε`
    """

    # Auto-inicializa dicionário interno e conjunto de destinos ao acessar chaves
    producoes = defaultdict(lambda: defaultdict(set))

    # Por ser Gramática Linear a Direita, só aceita produções do tipo:
    # 1. A -> ε 
    # 2. A -> a 
    # 3. A -> aB 
    for producao in producoes_arquivo:
        esquerda, direita = producao.split('->', 1)
        esquerda = esquerda.strip()  
        direita    = direita.strip()  

        if direita == 'ε':
            producoes[esquerda]['ε'].add(None)
        
        elif len(direita) == 1:
            producoes[esquerda][direita].add(None)

        elif len(direita) == 2:
            simb, nao_term = direita[0], direita[1]
            producoes[esquerda][simb].add(nao_term)

    return producoes


def converter_glud_afn(estado_ini, nao_terminais, producoes):
    """
    Converte a GLUD em um AFND, criando um estado final, mantendo o inicial
    e transformando as produções em transições
    """

    # Estados do AFN é o conjunto dos não-terminais + estado final criado
    estados = set(nao_terminais) | {'qf'}
    estado_fin = 'qf'
    transicoes = defaultdict(lambda: defaultdict(set))

    print("--- PRODUÇÕES => TRANSIÇÕES ---")
    for esq, mapa_simbolos in producoes.items():
        for simbolo, destinos in mapa_simbolos.items():
            for dest in destinos:
                if dest is None:  # Produções A->a ou A->ε
                    if simbolo == 'ε':
                        transicoes[esq][simbolo].add(estado_fin)
                        print(f"{esq} → ε    =>    δ({esq}, ε) = {{ {estado_fin} }}")
                    else:
                        print(f"{esq} → {simbolo}    =>    δ({esq}, '{simbolo}') = {{ {estado_fin} }}")
                else:  # Produções A->aB
                   transicoes[esq][simbolo].add(dest)
                   print(f"{esq} → {simbolo}{dest}    =>    δ({esq}, '{simbolo}') = {{ {dest} }}")
                    
    print("AFN:", {st: dict(sym_map) for st, sym_map in transicoes.items()})

    return estados, transicoes, estado_ini, estado_fin

def salvar_afn_arquivo(estados, alfabeto, transicoes, estado_ini, estado_fin, caminho_afn):
    """
    Função para armazenar o AFN em um arquivo txt no formato:
    `# AFN Original
    Q: {conjunto de estados}
    Σ: {conjunto com alfabeto}
    δ: {transições de estados depois de conversão de produções}
    {estado inicial}: inicial
    F: {estado final}`
    """

    with open(caminho_afn, 'w', encoding='utf-8') as f:
        f.write("# AFN Original\n")
        f.write(f"Q: {', '.join(estados)}\n")
        f.write(f"Σ: {', '.join(alfabeto)}\n")
        f.write("δ:\n")
        for esq, mapa in transicoes.items():
            for simbolo, destinos in mapa.items():
                for dest in destinos:
                    f.write(f" {esq}, {simbolo} -> {dest}\n")
        f.write(f"{estado_ini}: inicial\n")
        f.write(f"F: {estado_fin}\n")

def converter_glud(caminho_arquivo, nome_arquivo):
    estado_ini, nao_terminais, alfabeto, producoes_arquivo = extrair_glud_arquivo(caminho_arquivo)

    producoes_arquivo = expandir_producoes_glud(producoes_arquivo)
    producoes = extrair_producoes(producoes_arquivo)

    producoes = extrair_producoes(producoes_arquivo)
    print("\n--- GLUD ---")
    print(f"N: {', '.join(nao_terminais)}")
    print(f"Σ: {', '.join(alfabeto)}")
    print("P:")
    for linha in producoes_arquivo:
        print(f" {linha}")
    print(f"S: {estado_ini}\n")

    estados, transicoes, estado_ini, estado_fin = converter_glud_afn(estado_ini, nao_terminais, producoes)
    print("\n--- AFND GERADO ---")
    print(f"Q: {', '.join(estados)}")
    print(f"Σ: {', '.join(alfabeto)}")
    print("δ:")
    for esq, mapa in transicoes.items():
        for simbolo, destinos in mapa.items():
            for dest in destinos:
                print(f" {esq}, {simbolo} -> {dest}")
    print(f"{estado_ini}: inicial")
    print(f"F: {estado_fin}")
    
    caminho_saida = f'./arquivos/saida/{nome_arquivo}'
    salvar_afn_arquivo(estados, alfabeto, transicoes, estado_ini, estado_fin, caminho_saida)
    print(f"\nArquivo salvo em {caminho_saida}")