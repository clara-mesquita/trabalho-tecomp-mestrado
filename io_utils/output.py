def salvar_afn(states, terminals, transitions, initial_state, final_state, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# AFN Original\n")
        f.write(f"Q: {', '.join(states)}\n")
        f.write(f"∑: {', '.join(terminals)}\n")
        f.write("δ:\n")
        for from_state, symbol, to_state in transitions:
            f.write(f"{from_state}, {symbol} -> {to_state}\n")
        f.write(f"{initial_state}: inicial\n")
        f.write(f"F: {final_state}\n")