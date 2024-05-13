import pdfkit
from ratelimit import sleep_and_retry, limits

from analysis.analyzer import AppAnalyzer

from analysis.core.parsing import read_file
from analysis.core.chunking import chunk_file
from analysis.core.embedding import embed_files
from analysis.core.qa import query_folder
from analysis.core.utils import get_llm

class GPTAnalyzer(AppAnalyzer):
	def __init__(self, api_key, model):
		super().__init__()

		self.api_key = api_key
		self.model = model

	def name(self):
		if "gpt-4" in self.model:
			return "GPT-4"
		elif "gpt-3.5-turbo" in self.model:
			return "GPT-3.5 Turbo"
		return self.model

	@sleep_and_retry
	@limits(calls=1, period=5)
	def analyze_app(self, app):
		if not app.privacy_policy_url:
			# TODO: Log/throw
			return 0.0

		EMBEDDING = "openai"
		VECTOR_STORE = "faiss"

		pdfkit.from_url(app.privacy_policy_url, 'outfile.pdf')
		uploaded_file = open('outfile.pdf', "rb")
		file = read_file(uploaded_file)

		# Chunk file before analysis.
		chunked_file = chunk_file(file, chunk_size=300, chunk_overlap=0)

		# Index and create embeddings.
		folder_index = embed_files(
			files=[chunked_file],
			embedding=EMBEDDING if self.model != "debug" else "debug",
			vector_store=VECTOR_STORE if self.model != "debug" else "debug",
			openai_api_key=self.api_key,
		)

		# This is the O'Loughlin type query.
		query = """Fill in the list on this format with Y for yes or N for no in the place of X for the relevant question.
			Does the company/application collect any personally identifiable information such as e-mail address, real names, phone number or location. [X]
			Does the document mention a login process using a pincode, password or similar safety measure to use the service? [X]
			Does the document mention that the information is stored encrypted or that it stays locally on the device? [X]
			Does the document mention the information storage and sharing procedures OR that information is stored locally? [X]
			Does the document mention that users can delete their information OR that information is stored locally? [X]
			Does the document mention that users can edit their information OR that information is stored locally? [X]
			Does the document state that users can use the service/application WITHOUT entering any personally identifiable information OR that information is stored locally? [X]"""

		# Send query and get response.
		llm = get_llm(model=self.model, openai_api_key=self.api_key, temperature=0)
		result = query_folder(
			folder_index=folder_index,
			query=query,
			return_all=1,
			llm=llm,
			)

		# This is a test string used to check the behavior of the O'Loughlin framework.
		# Uncomment this and and replace the res below and the calls to llm above to test it. Refer to the paper by O'Loughling et al. for details.
		#res = ["pid [Y]", "pid [N]", "pid [N]", "pid [N]", "pid [Y]", "pid [Y]", "pid [Y]"]

		res = str.splitlines(result.answer)

		# Check if personally identifiable information is collected.
		if(res[0][len(res[0]) - 2] == 'Y'):
			# Check remaining parameters.
			if(res[1][len(res[1]) - 2] == 'N' or res[2][len(res[2]) - 2] == 'N' or res[3][len(res[3]) - 2] == 'N'):
				#print("unacceptable!")
				return 1
			elif(res[4][len(res[1]) - 2] == 'N' or res[5][len(res[1]) - 2] == 'N' or res[6][len(res[1]) - 2] == 'N'):
				#print("questionable!")
				return 0.5
			elif(True):
				#print("acceptable!")
				return 0
		# If no personally identifiable information is collected:
		else:
			for line in res[1:-1]:
				if(line[len(line) - 2] == 'N'):
					#print("questionable!")
					return 0.5
		#print("acceptable!")
		return 0
