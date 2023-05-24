from utils.modal_utils import stub, image
from utils.utils import pretty_log, vector_storage, VECTOR_DIR
from chains.qanda_langchain import qanda_langchain


@stub.function(
    image=image,
    shared_volumes={
        str(VECTOR_DIR): vector_storage,
    },
)
def cli(query: str):
    answer = qanda_langchain(query, with_logging=False)
    pretty_log("🦜 ANSWER 🦜")
    print(answer)
