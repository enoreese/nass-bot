import modal
import vecstore

VECTOR_DIR = vecstore.VECTOR_DIR
vector_storage = modal.SharedVolume().persist("vector-vol")


def pretty_log(str):
    print(f"{START}🥞: {str}{END}")


# Terminal codes for pretty-printing.
START, END = "\033[1;38;5;214m", "\033[0m"
