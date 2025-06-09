import sys
from conversores.glud_afn import converter_glud
from conversores.afn_afd import converter_afn
from conversores.fecho import aplicar_reverso_complemento_afd

def main():
    if len(sys.argv) < 4:
        print("Erro: algum dos 3 argumentos não foi fornecido: <operacao> <arquivo_entrada.txt> <cadeia>")
        sys.exit(1)

    operacao = sys.argv[1] 
    arquivo_entrada = sys.argv[2]

    if (operacao == 'glud'):
        converter_glud(arquivo_entrada)
    

    if (operacao == 'afn'):
        converter_afn(arquivo_entrada)

    if (operacao == 'afd'):
        cadeia = sys.argv[3]
        aplicar_reverso_complemento_afd(arquivo_entrada, cadeia)
        
if __name__ == "__main__":
    main()