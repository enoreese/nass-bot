# National Assembly Question and Answer System (Nass-Bot)

Welcome to the GitHub repository for the National Assembly Question and Answer System. This repository contains all the code and resources related to the blog post series on leveraging language models to build a powerful question and answer system for the Nigerian National Assembly Corpus. [Blog post](https://medium.com/@osas.usen/leveraging-language-models-part-2-building-a-powerful-question-and-answer-system-for-nigerian-fd6386640fbd)

We use the materials from the
[Nigerian National Assembly website](https://nass.gov.ng/)
as our document corpus,
so the resulting application is great at answering questions like

- What is the Climate Change and Green House Emissions Reduction Bill?
- Are there any bills related to sustainable energy development in Nigeria?
- What bills were sponsored by Sen. Ibrahim Abdullahi Gobir?
- Explain the Donkey slaughter regulation and Export Certification Bill ?

You can try it out via the Discord bot frontend by adding 
[AI Dev's Discord](https://discord.gg/BdRwUmKw).

## Overview

This repository is organized into two parts:

1. **Part 1**: Data Collection and Preprocessing (etl/)
   - This section focuses on the collection and preprocessing of data from the National Assembly Corpus. It covers the steps involved in gathering the necessary data and performing initial data processing tasks.

2. **Part 2**: Chunking, Embedding, and System Implementation (nassbot_app/)
   - This section delves into the essential steps involved in processing the collected data to construct the question and answer system. It covers techniques such as chunking and embedding, the development of a web endpoint and Discord server, and the implementation of the question and answer system itself.

## Installation

To use the code in this repository, please follow these steps:

1. Clone the repository to your local machine using the following command:
   ```
   git clone https://github.com/enoreese/nass-bot.git
   ```

2. Install the necessary dependencies by running the following command:
   ```
   pip install -r requirements.txt
   ```

3. Once the dependencies are installed, you can explore the code in the respective directories for Part 1 and Part 2.

## Usage

To use the question and answer system and interact with the National Assembly Corpus, follow these steps:

1. Set up the necessary configuration parameters in the `.env` file. Make sure to specify the appropriate paths, endpoints, and credentials required for the system. If you haven't already, create a `.env` file and include the following variables:

```plaintext
MODAL_TOKEN_ID=<your_modal_token_id>
MODAL_TOKEN_SECRET=<your_modal_token_secret>
DISCORD_AUTH=<your_discord_auth>
MONGODB_URI=<your_mongodb_uri>
MONGODB_PASSWORD=<your_mongodb_password>
```

2. Run the desired make target based on your intended functionality. For example:

- To run the Discord bot server locally, execute the following command:
  ```bash
  make discord_bot
  ```

- To deploy the Q&A backend on Modal, use the following command:
  ```bash
  make backend
  ```

- To run a query via a CLI interface, run the following command, replacing `${QUERY}` with your desired query:
  ```bash
  make cli_query QUERY="${QUERY}"
  ```

- For other functionalities like setting up the FAISS vector index, updating the MongoDB document store, or downloading PDFs to the document store, you can use the corresponding make targets:
  ```bash
  make vector_index
  make document_store
  make pdf_store
  ```

- For debugging purposes, you can start a debugger running in the container accessible via the terminal:
  ```bash
  make debugger
  ```

3. Access the question and answer system through the provided endpoints or by interacting with the deployed Discord bot, depending on the target you ran.

Note: Please ensure that you have the required environment set up by running the following command before executing any make target:
```bash
make environment
```

If you are working on development or generating the document corpus, you can use the `dev_environment` make target instead:
```bash
make dev_environment
```

For a comprehensive list of available make targets and their descriptions, run:
```bash
make help
```

Remember to refer to the respective sections in the `Makefile` for specific requirements and assumptions related to each make target.

## Contributing

We welcome contributions from the community to enhance the functionality and performance of the National Assembly Question and Answer System. If you would like to contribute, please follow these guidelines:

1. Fork the repository and create a new branch for your contributions.

2. Make your changes and ensure that the code follows the project's coding style and guidelines.

3. Write tests to cover your changes and ensure that the existing tests pass successfully.

4. Submit a pull request, providing a detailed description of the changes you have made.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgements

We would like to express our gratitude to FDSL (Full Stack Deep Learning) for their recent [LLM bootcamp](https://fullstackdeeplearning.com/llm-bootcamp/) and [repository](https://github.com/the-full-stack/ask-fsdl), which provided valuable insights and resources that enabled the development of this system.

## Contact

If you have any questions, suggestions, or feedback, please feel free to contact us at [email protected]

---

Thank you for visiting the repository and considering the National Assembly Question and Answer System. We encourage you to explore the code, try out the system, and contribute to its further development.