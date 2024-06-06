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

from langchain_community.callbacks import get_openai_callback

question_personal_data = "Does the document state that personally identifiable information such as e-mail address, real names, phone number or location are collected?"
question_encryption = "Does the document mention that user information is encrypted?"
question_data_storage = "Does the document describe if and how user data may be stored and shared?"
question_delete_data = "Does the document state that users can delete their information?"
question_edit_data = "Does the document state that users can edit their information?"
question_needs_identification = "Does the document state that users can use the app WITHOUT entering identifiable information?"

question_epilogue = "Reply with YES or NO followed by a single sentence justifying the answer."

total_tokens = 0
total_cost = 0.0

class GPTAnalyzer(AppAnalyzer):
	def name(self):
		return f"OpenAI {configs.main.analysis.gpt.model}"

	# Ask question to GPT and parse Y/N response
	# If GPT returns an unexpected result, an exception is thrown
	@sleep_and_retry
	@limits(calls=1, period=5)
	def ask(self, model, index, query):
		result = query_folder(
			folder_index=index,
			query=f"{query} {question_epilogue}",
			return_all=1,
			llm=model,
		)

		if configs.main.server.debug:
			logger.info(f"Query to {configs.main.analysis.gpt.model}: {query} {question_epilogue}")
			logger.info(f"Answer from {configs.main.analysis.gpt.model}: {result.answer}")

		answer = result.answer.lower()
		if answer.startswith("yes"):
			return True
		elif answer.startswith("no"):
			return False

		raise ValueError("GPT returned unexpected response")

	def analyze_app(self, app):
		global total_tokens
		global total_cost

		if not configs.secrets.api.openai:
			raise ValueError("configs.secrets.api.openai not set")

		if not app.privacy_policy_url:
			raise ValueError("app has no privacy_policy_url")

		EMBEDDING = "openai"
		VECTOR_STORE = "faiss"

		# Use pdfkit to fetch and convert privacy policy
		# TODO: wkhtmltopdf hangs with DDG privacy policy
		pdf = BytesIO(pdfkit.from_url(app.privacy_policy_url, verbose=configs.main.server.debug))
		pdf.name = app.privacy_policy_url
		file = PdfFile.from_bytes(pdf)

		if configs.main.analysis.gpt.save_pdf_output:
			with open(f"output_{app.id}.pdf", "wb") as f:
				f.write(pdf.getbuffer())

		model = configs.main.analysis.gpt.model
		embedding_model = configs.main.analysis.gpt.embedding_model
		api_key = configs.secrets.api.openai

		with get_openai_callback() as cb:
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

			llm = get_llm(model=model, openai_api_key=api_key, temperature=0)
			score = 0

			# Run the O'Loughlin type query
			if not self.ask(llm, folder_index, question_encryption):
				score = 1
			elif not self.ask(llm, folder_index, question_data_storage):
				score = 1
			elif not self.ask(llm, folder_index, question_delete_data):
				score = 0.5
			elif not self.ask(llm, folder_index, question_edit_data):
				score = 0.5
			elif not self.ask(llm, folder_index, question_needs_identification):
				score = 0.5

		total_tokens += cb.total_tokens
		total_cost += cb.total_cost

		logger.info(f"Used {cb.total_tokens} {model} tokens for query (in: {cb.prompt_tokens}, out: {cb.completion_tokens}, cost: {round(cb.total_cost, 2)} USD)")
		logger.info(f"Total this session: {total_tokens} tokens, {round(total_cost, 2)} USD")

		return score
