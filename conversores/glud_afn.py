import re
from collections import defaultdict

def extrair_glud_arquivo(caminho_arquivo):
    """
    Função que lê arquivo da gramática de entrada no formato:
    # Gramática: G = ({conjunto_nao_terminais}, {conjunto_terminais}, P, estado_inicial)

    D -> aA
    A -> bD
    D -> ε

    Extrai o cabeçalho (primeira linha) e as produções (demais linhas)
    
    Processa o cabeçalho e produções do arquivo e retorna os elementos
    da gramática (estado inicial, símbolos terminais, símb. não terminais e producoes)
    
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

    # Regex para extrair estado inicial, símbolos terminais e símbolos não terminais do cabeçalho
    regex = re.compile(
        r"""
        Gramática      
        \s*:\s*        
        G              
        \s*=\s*\(      
            \{\s*([^}]*)\s*\}         # grupo(1) = não-terminais entre chaves
            \s*,\s*\{\s*([^}]*)\s*\}  # grupo(2) = terminais entre chaves
            \s*,\s*P\s*,\s*           # descarta o “P”
            ([^\s\)]+)                # grupo(3) = símbolo/estado inicial
        \s*\)

        """,
        re.VERBOSE
    )

    cabecalho_regex = regex.search(cabecalho_arquivo)

    # Separar o cabeçalho com regex aplicado para extrair elementos da gramática
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
    Função que extrai as transições a partir das produções no formato

    D -> aA
    A -> bD
    D -> ε

    Por ser GLUD só aceita produções do tipo:
    A -> ε 
    A -> a 
    A -> aB 

    E retorna as transicoes
    """

    # Uso de defaultdict para economizar espaço e acessar mais facilmente elementos
    producoes = defaultdict(lambda: defaultdict(set))

    for producao in producoes_arquivo:
        esquerda, direita = producao.split('->', 1)
        esquerda = esquerda.strip()  
        direita    = direita.strip()  

        # Produção tipo A -> ε
        if direita == 'ε':
            producoes[esquerda]['ε'].add(None)
        
        # Producao tipo produção A -> a  
        elif len(direita) == 1:
            producoes[esquerda][direita].add(None)

        # Producao tipo A -> aB
        elif len(direita) == 2:
            simb, nao_term = direita[0], direita[1]
            producoes[esquerda][simb].add(nao_term)

    return producoes


def converter_glud_afn(estado_ini, nao_terminais, producoes):
    """
    Função que cria os estados a partir das produções 
    """

    # Todos os estados do AFN incluem os não-terminais + estado de aceitação único
    estados = set(nao_terminais) | {'qf'}
    estado_fin = 'qf'
    transicoes = defaultdict(lambda: defaultdict(set))

    for esq, mapa_simbolos in producoes.items():
        for simbolo, destinos in mapa_simbolos.items():
            for dest in destinos:
                if dest is None:  # Produções A->a ou A->ε
                    if simbolo == 'ε':
                        transicoes[esq][simbolo].add(estado_fin)
                else:  # Produções A->aB
                   transicoes[esq][simbolo].add(dest)
                    
    print("AFN:", {st: dict(sym_map) for st, sym_map in transicoes.items()})

    return estados, transicoes, estado_ini, estado_fin

def salvar_afn_arquivo(estados, alfabeto, transicoes, estado_ini, estado_fin, caminho_afn = './arquivos/afn.txt'):
    """
    Função para armazenar o AFN em um arquivo txt no formato:
    # AFN Original
    Q: {conjunto_estados}
    ∑: {conjunto_alfabeto}
    δ: {dicionario_transicoes}
    {estado_inicial}: inicial
    F: {estado_final}
    """
    with open(caminho_afn, 'w', encoding='utf-8') as f:
        f.write("# AFN Original\n")
        f.write(f"Q: {', '.join(estados)}\n")
        f.write(f"∑: {', '.join(alfabeto)}\n")
        f.write("δ:\n")
        for esq, mapa in transicoes.items():
            for simbolo, destinos in mapa.items():
                for dest in destinos:
                    f.write(f"{esq}, {simbolo} -> {dest}")
                    print(f"{esq}, {simbolo} -> {dest}")
        f.write(f"{estado_ini}: inicial\n")
        f.write(f"F: {estado_fin}\n")

def converter_glud(caminho_arquivo):
    estado_ini, nao_terminais, alfabeto, producoes = extrair_glud_arquivo(caminho_arquivo)
    transicoes = extrair_producoes(producoes)
    estados, transicoes, estado_ini, estado_fin = converter_glud_afn(estado_ini, nao_terminais, transicoes)
    salvar_afn_arquivo(estados, alfabeto, transicoes, estado_ini, estado_fin)