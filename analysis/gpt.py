from analysis.core.parsing import read_file
from analysis.core.chunking import chunk_file
from analysis.core.embedding import embed_files
from analysis.core.qa import query_folder
from analysis.core.utils import get_llm

from io import BytesIO

# Just a debug function to check reachability.
def printathing():
	print("hello there")

# Function to analyse the contents of a privacy policy. API key and BytesIO object must be included in function call.
def ppcheck(openai_api_key):

	EMBEDDING = "openai"
	VECTOR_STORE = "faiss"
	MODEL_LIST = ["gpt-3.5-turbo", "gpt-4"]

	model = "gpt-4"

	# Right now the file is hardcoded like this but this will be removed eventually and documents dynamically provided in the call.
	uploaded_file = open('testdocu.pdf', "rb")

	try:
		file = read_file(uploaded_file)
	except Exception as e:
		print("FILE READ ERROR: ", e)

	# This should be removed along with the open call above once properly implemented.
	uploaded_file.close()

	# Chunk file before analysis.
	chunked_file = chunk_file(file, chunk_size=300, chunk_overlap=0)

	# Index and create embeddings.
	folder_index = embed_files(
			files=[chunked_file],
			embedding=EMBEDDING if model != "debug" else "debug",
			vector_store=VECTOR_STORE if model != "debug" else "debug",
			openai_api_key=openai_api_key,
			)

	# Testquery, remove once properly implemented.
	query = "Describe in two sentences what type of document this is. Then, fill in the list on the on this format with Y for yes or N for no in the place of X for the relevant question. \nDoes the company sell user data? [X] \nDoes the company collect any type of user data? [X] \nIs the company name Facebook? [X]"

	# Send query and get response.
	llm = get_llm(model=model, openai_api_key=openai_api_key, temperature=0)
	result = query_folder(
			folder_index=folder_index,
			query=query,
			return_all=1,
			llm=llm,
		)

	# Print the answer. This should instead be returned in final build on some predetermined format.
	print(result.answer)
