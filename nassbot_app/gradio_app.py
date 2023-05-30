from fastapi import FastAPI
from utils.modal_utils import stub, image
from utils.utils import vector_storage, VECTOR_DIR
from chains.qa_chain import qanda_langchain

import modal
import gradio as gr
from gradio.routes import mount_gradio_app

web_app = FastAPI()


@web_app.get("/")
async def root():
    return {"message": "Hello World"}


@stub.function(
    image=image,
    shared_volumes={
        str(VECTOR_DIR): vector_storage,
    },
)
@modal.asgi_app(label="ask-fsdl")
def fastapi_app():
    """A simple Gradio interface for debugging."""

    def chain_with_logging(*args, **kwargs):
        return qanda_langchain(*args, with_logging=True, **kwargs)

    interface = gr.Interface(
        fn=chain_with_logging,
        inputs="text",
        outputs="text",
        title="Ask Questions About Full Stack Deep Learning.",
        examples=[
            "What is zero-shot chain-of-thought prompting?",
            "Would you rather fight 100 LLaMA-sized GPT-4s or 1 GPT-4-sized LLaMA?",
            "What are the differences in capabilities between GPT-3 davinci and GPT-3.5 code-davinci-002?",
            # noqa: E501
            "What is PyTorch? How can I decide whether to choose it over TensorFlow?",
            "Is it cheaper to run experiments on cheap GPUs or expensive GPUs?",
            "How do I recruit an ML team?",
            "What is the best way to learn about ML?",
        ],
        allow_flagging="never",
    )

    return mount_gradio_app(app=web_app, blocks=interface, path="/gradio")
