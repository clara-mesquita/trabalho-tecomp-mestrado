#!/usr/bin/env python3
import sys
from conversores.glud_afn import converter_glud
from conversores.afn_afd import converter_afn
from conversores.rev_comp import aplicar_reverso_complemento_afd

USO = """
Uso:
  script.py glud <entrada> <saida>
  script.py afn  <entrada> <saida>
  script.py afd  <entrada> <saida_complemento> <saida_reverso> <cadeia>
"""

def main():
    args = sys.argv[1:]
    if not args:
        print(USO)
        sys.exit(1)

    operacao = args[0]

    # ex: python main.py glud arquivos/entrada/exemplo_apr.txt exemplo_apr_afn.txt
    if operacao == 'glud':
        _, entrada, saida = args
        converter_glud(entrada, saida)

    # ex: python main.py afn arquivos/saida/exemplo_apr_afn.txt exemplo_apr_afd.txt
    elif operacao == 'afn':
        _, entrada, saida = args
        converter_afn(entrada, saida)

    # ex: python main.py afd arquivos/saida/exemplo_apr_afd.txt exemplo_apr_comp.txt exemplo_apr_rev.txt aa
    elif operacao == 'afd':
        _, entrada, comp, rev, cadeia = args
        aplicar_reverso_complemento_afd(entrada, comp, rev, cadeia)

if __name__ == "__main__":
    main()
