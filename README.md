# Final Project Repository for Evaluation

![Python](https://img.shields.io/badge/python-3.12.2-blue)
![Django](https://img.shields.io/badge/django-5.1.4-green)

## Overview

This Django application includes an LLM-based chatbot and some features of a virtual charity website.  
The chatbot utilizes the OpenAI API and implements Retrieval-Augmented Generation (RAG).  
FAQ entry data is stored in Milvus Lite as the knowledge base, and text is vectorized using the Universal Sentence Encoder (USE).  
A Django custom management command is defined to download USE from Kaggle.

To run the application, the following environment variables must be set:

- `KAGGLE_USERNAME`
- `KAGGLE_KEY`
- `OPENAI_API_KEY`
- `CACHE_DIR` – specifies the directory for storing the USE model. If not set, it defaults to `~/.cache`.


## How to Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Download the USE model:

```bash
python charityproject/manage.py download_use_model
```

Populate the database:

This command populates both the relational and vector databases, including sample data such as FAQ entries. Since vector representations are generated during this process, the encoder must be available.

```bash
python charityproject/manage.py migrate
python charityproject/manage.py populate_data
```

Start the Redis server:

```bash
redis-server
```

Run the Django development server:

```bash
python charityproject/manage.py runserver
```


## Testing

To run the tests:
```bash
pytest charityproject
```

To check test coverage:
```bash
pytest charityproject --cov charityproject
```


## Chatbot Evaluation

The performance of the developed chatbot was evaluated using the RAGAS framework.  
The code used for the evaluation is provided in the `evaluation` folder.  
See the following notebook for details:  
[evaluation/ragas_evaluation_example.ipynb](evaluation/ragas_evaluation_example.ipynb)

This notebook demonstrates how RAGAS was applied to assess the system’s performance on a sample query.


## License

This project is submitted for academic evaluation only. No license has been applied at this stage.
