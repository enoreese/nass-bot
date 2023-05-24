import modal

# definition of our container image for jobs on Modal
# Modal gets really powerful when you start using multiple images!
image = modal.Image.debian_slim(  # we start from a lightweight linux distro
    python_version="3.10"  # we add a recent Python version
).pip_install(  # and we install the following packages:
    "langchain~=0.0.145",
    # 🦜🔗: a framework for building apps with LLMs
    "openai~=0.26.3",
    # high-quality language models and cheap embeddings
    "tiktoken",
    # tokenizer for OpenAI models
    "faiss-cpu",
    # vector storage and similarity search
    "pymongo[srv]==3.11",
    # python client for MongoDB, our data persistence solution
    "gradio~=3.17",
    # simple web UIs in Python, from 🤗
    "gantry==0.5.6",
    # 🏗️: monitoring, observability, and continual improvement for ML systems
)

# we define a Stub to hold all the pieces of our app
# most of the rest of this file just adds features onto this Stub
stub = modal.Stub(
    name="ask-fsdl",
    image=image,
    secrets=[
        # this is where we add API keys, passwords, and URLs, which are stored on Modal
        modal.Secret.from_name("mongodb"),
        modal.Secret.from_name("openai-api-key-fsdl"),
        modal.Secret.from_name("gantry-api-key"),
    ],
    mounts=[
        # we make our local modules available to the container
        *modal.create_package_mounts(module_names=["utils/vecstore", "utils/docstore", "utils/utils"])
    ],
)
