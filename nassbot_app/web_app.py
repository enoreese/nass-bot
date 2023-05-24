"""Builds a CLI, Webhook, and Gradio app for Q&A on the FSDL corpus.

For details on corpus construction, see the accompanying notebook."""
import modal

from nassbot_app.utils import vecstore
from nassbot_app.utils.utils import pretty_log
from nassbot_app.utils.modal_utils import stub, image

from chains.qanda_langchain import qanda_langchain

VECTOR_DIR = vecstore.VECTOR_DIR
vector_storage = modal.SharedVolume().persist("vector-vol")


@stub.function(
    image=image,
    shared_volumes={
        str(VECTOR_DIR): vector_storage,
    },
)
@modal.web_endpoint(method="GET", label="ask-fsdl-hook")
def web(query: str, request_id=None):
    """Exposes our Q&A chain for queries via a web endpoint."""
    pretty_log(
        f"handling request with client-provided id: {request_id}"
    ) if request_id else None
    answer = qanda_langchain(query, request_id=request_id, with_logging=True)
    return {
        "answer": answer,
    }
