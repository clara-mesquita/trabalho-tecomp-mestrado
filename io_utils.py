import re 

def parser_gramatica(caminho):
    with open(caminho, 'r', encoding='utf-8') as f:
        primeira_linha = f.readline().strip()

        # Exemplo de primeira_linha: "G = ({D, A}, {a, b}, P, D)"
        # A expressão abaixo captura o texto depois da última vírgula antes de ")".
        padrao = re.compile(r'\(\s*\{[^}]*\}\s*,\s*\{[^}]*\}\s*,\s*[^,]*\s*,\s*([^)\s]+)\s*\)')
        match = padrao.search(primeira_linha)
        if not match:
            raise ValueError(f"Formato inesperado na linha: {primeira_linha!r}")

        estado_inicial = match.group(1)
        linhas = [linha.strip() for linha in f if linha.strip() and not linha.startswith('#')]
    
    producoes = []
    nao_terminais = set()
    terminais = set()

    for linha in linhas:
        esq, right = linha.split('->')
        esq = esq.strip()
        right = right.strip()
        nao_terminais.add(esq)

        if right == 'ε':
            producoes.append((esq, 'ε', None))
        elif len(right) == 1:
            terminais.add(right)
            producoes.append((esq, right, None))
        elif len(right) == 2:
            terminais.add(right[0])
            producoes.append((esq, right[0], right[1]))
        else:
            raise ValueError("Formato de produção inválido na linha " + linha)

    return estado_inicial, producoes, nao_terminais, terminais

def save_afn_to_file(states, terminals, transitions, initial_state, final_state, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# AFN Original\n")
        f.write(f"Q: {', '.join(states)}\n")
        f.write(f"∑: {', '.join(terminals)}\n")
        f.write("δ:\n")
        for from_state, symbol, to_state in transitions:
            f.write(f"{from_state}, {symbol} -> {to_state}\n")
        f.write(f"{initial_state}: inicial\n")
        f.write(f"F: {final_state}\n")