# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import pdfkit
import configs

from io import BytesIO
from loguru import logger
from ratelimit import sleep_and_retry, limits

from analysis.analyzer import AppAnalyzer

from analysis.knowledge_gpt.core.parsing import PdfFile
from analysis.knowledge_gpt.core.chunking import chunk_file
from analysis.knowledge_gpt.core.embedding import embed_files
from analysis.knowledge_gpt.core.qa import query_folder
from analysis.knowledge_gpt.core.utils import get_llm

class GPTAnalyzer(AppAnalyzer):
	def name(self):
		return f"OpenAI {configs.main.analysis.gpt.model}"

	@sleep_and_retry
	@limits(calls=1, period=5)
	def analyze_app(self, app):
		if not app.privacy_policy_url:
			raise ValueError("app has no privacy_policy_url")

		EMBEDDING = "openai"
		VECTOR_STORE = "faiss"

		# Use wkhtmltopdf to fetch and convert privacy policy
		pdf = BytesIO(pdfkit.from_url(app.privacy_policy_url, verbose=configs.main.server.debug))
		pdf.name = app.privacy_policy_url
		file = PdfFile.from_bytes(pdf)

		# with open(f"output_{app.id}.pdf", "wb") as f:
		#	 f.write(pdf.getbuffer())

		model = configs.main.analysis.gpt.model
		embedding_model = configs.main.analysis.gpt.embedding_model
		api_key = configs.secrets.api.openai

		# Chunk file before analysis
		chunked_file = chunk_file(file, chunk_size=300, chunk_overlap=0, model_name=model)

		# Index and create embeddings
		folder_index = embed_files(
			files=[chunked_file],
			embedding=EMBEDDING if model != "debug" else "debug",
			vector_store=VECTOR_STORE if model != "debug" else "debug",
			openai_api_key=api_key,
			model=embedding_model
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

		llm = get_llm(model=model, openai_api_key=api_key, temperature=0)
		result = query_folder(
			folder_index=folder_index,
			query=query,
			return_all=1,
			llm=llm,
		)

		# This is a test string used to check the behavior of the O'Loughlin framework.
		# Uncomment this and and replace the res below and the calls to llm above to test it. Refer to the paper by O'Loughling et al. for details.
		# res = ["pid [Y]", "pid [N]", "pid [N]", "pid [N]", "pid [Y]", "pid [Y]", "pid [Y]"]

		res = str.splitlines(result.answer)

		if configs.main.server.debug:
			logger.info(f"Response from GPT: {result.answer}")

		# Check if personally identifiable information is collected.
		if res[0][len(res[0]) - 2] == 'Y':
			# Check remaining parameters.
			if res[1][len(res[1]) - 2] == 'N' or res[2][len(res[2]) - 2] == 'N' or res[3][len(res[3]) - 2] == 'N':
				return 1
			elif res[4][len(res[4]) - 2] == 'N' or res[5][len(res[5]) - 2] == 'N' or res[6][len(res[6]) - 2] == 'N':
				return 0.5
			elif True:
				return 0
		# If no personally identifiable information is collected:
		else:
			for line in res[1:-1]:
				if(line[len(line) - 2] == 'N'):
					return 0.5

		return 0
