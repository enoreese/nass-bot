import os
import gantry


def log_event(query, sources, answer, request_id=None):
    """Logs the event to Gantry."""

    gantry.init(api_key=os.environ["GANTRY_API_KEY"], environment="modal")

    application = "ask-fsdl"
    join_key = str(request_id) if request_id else None

    inputs = {"question": query}
    inputs["docs"] = "\n\n---\n\n".join(source.page_content for source in sources)
    inputs["sources"] = "\n\n---\n\n".join(
        source.metadata["source"] for source in sources
    )
    outputs = {"answer_text": answer}

    record_key = gantry.log_record(
        application=application, inputs=inputs, outputs=outputs, join_key=join_key
    )

    return record_key
