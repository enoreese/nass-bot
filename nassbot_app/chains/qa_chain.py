from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.llms import OpenAI


def qanda_langchain(query: str, request_id=None, with_logging=False) -> str:
    """Runs sourced Q&A for a query using LangChain.

    Arguments:
        query: The query to run Q&A on.
        request_id: A unique identifier for the request.
        with_logging: If True, logs the interaction to Gantry.
    """
    import sys
    sys.path.insert(1, '.../utils/utils')
    from utils import utils
    from utils import vecstore

    vector_store = vecstore.FaissVectorStore()
    # embedding_engine = vecstore.lang_embedding_engine

    utils.pretty_log("connecting to vector storage")
    vector_index = vector_store.connect_to_vector_index()
    utils.pretty_log("connected to vector storage")

    utils.pretty_log(f"running on query: {query}")
    utils.pretty_log("selecting sources by similarity to query")
    sources = vector_index.similarity_search(query, k=2)

    for source in sources:
        source.metadata['source'] = source.metadata['download_url']

    if with_logging:
        utils.pretty_log("SOURCES")
        print(*[source.page_content for source in sources], sep="\n\n---\n\n")

    utils.pretty_log("running query against Q&A chain")

    llm = OpenAI(model_name="text-davinci-003", temperature=0)
    chain = load_qa_with_sources_chain(llm, chain_type="stuff")

    result = chain(
        {"input_documents": sources, "question": query}, return_only_outputs=True
    )
    answer = result["output_text"]

    if with_logging:
        print(answer)
        # utils.pretty_log("logging results to gantry")
        # record_key = utils.log_event(query, sources, answer, request_id=request_id)
        # utils.pretty_log(f"logged to gantry with key {record_key}")

    return answer
