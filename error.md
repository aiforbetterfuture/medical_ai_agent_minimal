?ㅽ뻾 ?쒖옉: 2025-12-13 19:27:47.37
濡쒓렇 ?꾩튂: runs\2025-12-13_primary_v1\

2025-12-13 19:28:00,557 - __main__ - INFO - Starting experiment: 2025-12-13_primary_v1
2025-12-13 19:28:00,564 - __main__ - INFO - Patients: 80, Max turns: 5
2025-12-13 19:28:00,763 - __main__ - INFO - Processing patient: SYN_0001
2025-12-13 19:28:00,776 - __main__ - INFO -   Mode: llm
2025-12-13 19:28:00,777 - __main__ - INFO -     Turn 1
2025-12-13 19:28:10,510 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:28:10,520 - __main__ - INFO -       Completed in 9738ms
2025-12-13 19:28:10,520 - __main__ - INFO -     Turn 2
2025-12-13 19:28:20,772 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:28:20,781 - __main__ - INFO -       Completed in 10257ms
2025-12-13 19:28:20,782 - __main__ - INFO -     Turn 3
2025-12-13 19:28:29,868 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:28:29,872 - __main__ - INFO -       Completed in 9089ms
2025-12-13 19:28:29,873 - __main__ - INFO -     Turn 4
2025-12-13 19:28:38,763 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:28:38,771 - __main__ - INFO -       Completed in 8896ms
2025-12-13 19:28:38,772 - __main__ - INFO -     Turn 5
2025-12-13 19:28:51,363 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:28:51,375 - __main__ - INFO -       Completed in 12601ms
2025-12-13 19:28:51,377 - __main__ - INFO -   Mode: agent
2025-12-13 19:28:51,377 - __main__ - INFO -     Turn 1
2025-12-13 19:28:51,554 - sentence_transformers.SentenceTransformer - INFO - Use pytorch device_name: cpu
2025-12-13 19:28:51,554 - sentence_transformers.SentenceTransformer - INFO - Load pretrained SentenceTransformer: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
[Node] check_similarity
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00,  3.33it/s]
2025-12-13 19:28:56,512 - medcat.cat - INFO - Found an existing unzipped model pack at: C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\medcat2\mc_modelpack_snomed_int_16_mar_2022_25be3857ba34bdd5, the provided zip will not be touched.
2025-12-13 19:28:56,512 - medcat.cat - INFO - Attempting to load model from file: C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\medcat2\mc_modelpack_snomed_int_16_mar_2022_25be3857ba34bdd5
2025-12-13 19:28:56,530 - medcat.cat - WARNING - Doing legacy conversion on CAT (at 'C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\medcat2\mc_modelpack_snomed_int_16_mar_2022_25be3857ba34bdd5'). Set the environment variable MEDCAT_AVOID_LECACY_CONVERSION to `True` to avoid this.
2025-12-13 19:29:12,622 - medcat.utils.legacy.convert_cdb - INFO - A total of 354448 CUIs identified
2025-12-13 19:29:16,197 - medcat.utils.legacy.convert_cdb - INFO - Deleting 'cui2original_names' in addl_info - it was used in CUIInfo already
2025-12-13 19:29:17,386 - medcat.utils.legacy.convert_cdb - INFO - A total of 2049216 names found
2025-12-13 19:29:17,387 - medcat.utils.legacy.convert_cdb - INFO - Adding names from cui2names
2025-12-13 19:29:17,748 - medcat.utils.legacy.convert_cdb - INFO - A total of 2049216 names found after adding from cui2names
2025-12-13 19:29:26,161 - medcat.utils.legacy.convert_cdb - INFO - Loading old style CDB with config included.
2025-12-13 19:29:27,601 - medcat.utils.legacy.convert_config - INFO - Setting Config.cdb_maker to dict
2025-12-13 19:29:27,601 - medcat.utils.legacy.convert_config - INFO - Setting Config.preprocessing to dict
2025-12-13 19:29:27,601 - medcat.utils.legacy.convert_config - INFO - Setting general while removing 4
2025-12-13 19:29:27,601 - medcat.utils.legacy.convert_config - WARNING - Trying to set 'cdb_source_name' for 'General' but no such attribute
2025-12-13 19:29:27,601 - medcat.utils.legacy.convert_config - INFO - Setting annotation_output while removing 1
2025-12-13 19:29:27,601 - medcat.utils.legacy.convert_config - INFO - Relocating from linking to components.linking (dict)
2025-12-13 19:29:27,603 - medcat.utils.legacy.convert_config - WARNING - Trying to set 'checkpoint' for 'Linking' but no such attribute
2025-12-13 19:29:27,603 - medcat.utils.legacy.convert_config - WARNING - Trying to set 'weighted_average_function' for 'Linking' but no such attribute
2025-12-13 19:29:27,603 - medcat.utils.legacy.convert_config - WARNING - Trying to set 'output_dir' for 'Linking' but no such attribute
2025-12-13 19:29:27,603 - medcat.utils.legacy.convert_config - WARNING - Trying to set 'save_steps' for 'Linking' but no such attribute
2025-12-13 19:29:27,603 - medcat.utils.legacy.convert_config - INFO - Relocating from ner to components.ner (dict)
2025-12-13 19:29:27,603 - medcat.utils.legacy.convert_config - INFO - Relocating from version.description to meta.description (str)
2025-12-13 19:29:27,603 - medcat.utils.legacy.convert_config - INFO - Relocating from version.id to meta.hash (str)
2025-12-13 19:29:27,604 - medcat.utils.legacy.convert_config - INFO - Relocating from version.ontology to meta.ontology (str)
2025-12-13 19:29:27,604 - medcat.utils.legacy.convert_config - INFO - Relocating from general.spacy_model to general.nlp.modelname (str)
2025-12-13 19:29:27,604 - medcat.utils.legacy.convert_config - INFO - Relocating from general.spacy_disabled_components to general.nlp.disabled_components (list)
2025-12-13 19:29:27,604 - medcat.utils.legacy.convert_config - INFO - Fixing spacy model. Moving from 'spacy_model' to 'en_core_web_md'!
2025-12-13 19:29:32,185 - medcat.components.addons.meta_cat.meta_cat - INFO - LSTM model used for classification
2025-12-13 19:29:32,279 - medcat.components.addons.meta_cat.meta_cat - INFO - LSTM model used for classification
2025-12-13 19:29:32,725 - medcat.pipeline.pipeline - INFO - Running component tagging:tag-and-skip-tagger for 110 of text (1788061947888)
2025-12-13 19:29:32,728 - medcat.pipeline.pipeline - INFO - Running component token_normalizing:token_normalizer for 110 of text (1788061947888)
2025-12-13 19:29:32,730 - medcat.pipeline.pipeline - INFO - Running component ner:cat_ner for 110 of text (1788061947888)
2025-12-13 19:29:32,732 - medcat.cdb.cdb - INFO - Resetting subnames
2025-12-13 19:29:34,003 - medcat.pipeline.pipeline - INFO - Running component linking:medcat2_linker for 110 of text (1788061947888)
2025-12-13 19:29:34,077 - medcat.cat - INFO - Automatically finding ontologies to map to: ['icd10']
2025-12-13 19:29:35,314 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
Traceback (most recent call last):
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\retrieval\faiss_index.py", line 94, in search
    scores, indices = self.index.search(query_vec, k)
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\.venv\lib\site-packages\faiss\class_wrappers.py", line 383, in replacement_search
    assert d == self.d
AssertionError
2025-12-13 19:29:53,798 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:29:57,372 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
[Cache Miss] No similar question found in cache
[Node] classify_intent
[ERROR] classify_intent_node failed: 'NoneType' object has no attribute 'classify'
[Node] extract_slots
Conditions False True IN {'51120815', '9090192', '46506674', '14654508', '8067332', '70426313', '40357424', '9593000', '31685163', '31601201', '43857361', '21114934', '28695783', '81102976', '33782986', '66203715', '18854038', '37785117', '82417248', '45958968', '91187746', '2680757', '29422548', '27603525', '30703196', '90170645', '7882689', '47503797', '87776218', '55540447', '25624495', '33797723', '3242456', '64755083', '337250', '40584095', '91776366', '37552161', '51885115', '78096516', '20410104', '67667581', '99220404', '46922199', '75168589', '28321150', '92873870', '43039974', '17030977', '39041339', '13371933', '49144999', '95475658', '43744943', '16939031', '32816260', '66527446', '3061879'}
Got TypeID2name for 58 TypeIDs out of 58
[MedCAT2] 모델 로드 완료: C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\medcat2\mc_modelpack_snomed_int_16_mar_2022_25be3857ba34bdd5.zip
[Node] store_memory
[Node] assemble_context
[Node] retrieve
[BM25] 코퍼스 로드 완료: 15021개 문서
[FAISS] 인덱스 로드 완료: ./data/index/train_source/train_source_data.index.faiss
[FAISS] 메타데이터 로드 완료: 15021개 문서
[ERROR] FAISS 검색 실패:
[Node] assemble_context
[Node] generate_answer
[Node] refine (Strategy-based)
[Refine] 전략 선택: corrective_rag
[CORRECTIVE_RAG] Refine 수행 중...
[CORRECTIVE_RAG] 품질 점수: 0.50 (Iteration: 1)
[Node] quality_check (Strategy-based)
[Quality Check] 종료 (전략: corrective_rag, 점수: 0.50)
[Node] store_response
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00,  4.65it/s]
2025-12-13 19:29:58,032 - __main__ - INFO -       Completed in 66648ms
2025-12-13 19:29:58,032 - __main__ - INFO -     Turn 2
[Cache Store] Response cached. Cache size: 1
[Node] check_similarity
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 13.92it/s]
2025-12-13 19:29:58,133 - extraction.multilingual_medcat - INFO - [MultilingualMedCAT] 초기화 완료
2025-12-13 19:29:58,139 - extraction.multilingual_medcat - INFO - [MultilingualMedCAT] 사전 기반 번역기 초기화
2025-12-13 19:29:58,143 - extraction.neural_translator - INFO - [NeuralTranslator] 초기화 완료 (device=cpu, lazy_load=True)
2025-12-13 19:29:58,143 - extraction.multilingual_medcat - INFO - [MultilingualMedCAT] 신경망 번역기 초기화
2025-12-13 19:29:58,143 - extraction.neural_translator - INFO - [NeuralTranslator] transformers 4.57.3 사용 가능
2025-12-13 19:29:58,395 - extraction.neural_translator - INFO - [NeuralTranslator] 한영 번역 모델 로딩: Helsinki-NLP/opus-mt-ko-en
C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\.venv\lib\site-packages\transformers\models\marian\tokenization_marian.py:175: UserWarning: Recommended: pip install sacremoses.
  warnings.warn("Recommended: pip install sacremoses.")
Device set to use cpu
2025-12-13 19:30:01,510 - extraction.neural_translator - INFO - [NeuralTranslator] 한영 번역 모델 로드 완료
2025-12-13 19:30:01,510 - extraction.neural_translator - INFO - [NeuralTranslator] 영한 번역 모델 로딩: Helsinki-NLP/opus-mt-en-ko
2025-12-13 19:30:01,729 - extraction.neural_translator - ERROR - [NeuralTranslator] 번역 모델 로드 실패: Helsinki-NLP/opus-mt-en-ko is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth login` or by passing `token=<your_token>`
2025-12-13 19:30:01,757 - extraction.neural_translator - WARNING - [NeuralTranslator] 한영 번역기 로드 실패, 원본 반환
2025-12-13 19:30:01,772 - medcat.pipeline.pipeline - INFO - Running component tagging:tag-and-skip-tagger for 57 of text (1788036021872)
2025-12-13 19:30:01,773 - medcat.pipeline.pipeline - INFO - Running component token_normalizing:token_normalizer for 57 of text (1788036021872)
2025-12-13 19:30:01,774 - medcat.pipeline.pipeline - INFO - Running component ner:cat_ner for 57 of text (1788036021872)
2025-12-13 19:30:01,774 - medcat.pipeline.pipeline - INFO - Running component linking:medcat2_linker for 57 of text (1788036021872)
2025-12-13 19:30:02,155 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
Traceback (most recent call last):
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\retrieval\faiss_index.py", line 94, in search
    scores, indices = self.index.search(query_vec, k)
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\.venv\lib\site-packages\faiss\class_wrappers.py", line 383, in replacement_search
    assert d == self.d
AssertionError
2025-12-13 19:30:10,492 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:30:13,868 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
[Cache Miss] No similar question found in cache
[Node] classify_intent
[ERROR] classify_intent_node failed: 'NoneType' object has no attribute 'classify'
[Node] extract_slots
[Node] store_memory
[Node] assemble_context
[Node] retrieve
[BM25] 코퍼스 로드 완료: 12272개 문서
[FAISS] 인덱스 로드 완료: ./data/index/train_qa/train_questions.index.faiss
[FAISS] 메타데이터 로드 완료: 12272개 문서
[ERROR] FAISS 검색 실패:
[Node] assemble_context
[Node] generate_answer
[Node] refine (Strategy-based)
[Refine] 전략 선택: corrective_rag
[CORRECTIVE_RAG] Refine 수행 중...
[CORRECTIVE_RAG] 품질 점수: 0.50 (Iteration: 1)
[Node] quality_check (Strategy-based)
[Quality Check] 종료 (전략: corrective_rag, 점수: 0.50)
[Node] store_response
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 16.08it/s]
2025-12-13 19:30:14,040 - __main__ - INFO -       Completed in 16005ms
2025-12-13 19:30:14,041 - __main__ - INFO -     Turn 3
[Cache Store] Response cached. Cache size: 2
[Node] check_similarity
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 17.05it/s]
2025-12-13 19:30:14,124 - extraction.neural_translator - INFO - [NeuralTranslator] 한영 번역 모델 로딩: Helsinki-NLP/opus-mt-ko-en
Device set to use cpu
2025-12-13 19:30:16,969 - extraction.neural_translator - INFO - [NeuralTranslator] 한영 번역 모델 로드 완료
2025-12-13 19:30:16,970 - extraction.neural_translator - INFO - [NeuralTranslator] 영한 번역 모델 로딩: Helsinki-NLP/opus-mt-en-ko
2025-12-13 19:30:17,171 - extraction.neural_translator - ERROR - [NeuralTranslator] 번역 모델 로드 실패: Helsinki-NLP/opus-mt-en-ko is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth login` or by passing `token=<your_token>`
2025-12-13 19:30:17,190 - extraction.neural_translator - WARNING - [NeuralTranslator] 한영 번역기 로드 실패, 원본 반환
2025-12-13 19:30:17,202 - medcat.pipeline.pipeline - INFO - Running component tagging:tag-and-skip-tagger for 52 of text (1788036021872)
2025-12-13 19:30:17,202 - medcat.pipeline.pipeline - INFO - Running component token_normalizing:token_normalizer for 52 of text (1788036021872)
2025-12-13 19:30:17,203 - medcat.pipeline.pipeline - INFO - Running component ner:cat_ner for 52 of text (1788036021872)
2025-12-13 19:30:17,203 - medcat.pipeline.pipeline - INFO - Running component linking:medcat2_linker for 52 of text (1788036021872)
2025-12-13 19:30:17,565 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
Traceback (most recent call last):
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\retrieval\faiss_index.py", line 94, in search
    scores, indices = self.index.search(query_vec, k)
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\.venv\lib\site-packages\faiss\class_wrappers.py", line 383, in replacement_search
    assert d == self.d
AssertionError
2025-12-13 19:30:32,693 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:30:36,695 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
[Cache Miss] No similar question found in cache
[Node] classify_intent
[ERROR] classify_intent_node failed: 'NoneType' object has no attribute 'classify'
[Node] extract_slots
[Node] store_memory
[Node] assemble_context
[Node] retrieve
[BM25] 코퍼스 로드 완료: 12272개 문서
[FAISS] 인덱스 로드 완료: ./data/index/train_qa/train_questions.index.faiss
[FAISS] 메타데이터 로드 완료: 12272개 문서
[ERROR] FAISS 검색 실패:
[Node] assemble_context
[Node] generate_answer
[Node] refine (Strategy-based)
[Refine] 전략 선택: corrective_rag
[CORRECTIVE_RAG] Refine 수행 중...
[CORRECTIVE_RAG] 품질 점수: 0.50 (Iteration: 1)
[Node] quality_check (Strategy-based)
[Quality Check] 종료 (전략: corrective_rag, 점수: 0.50)
[Node] store_response
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 25.70it/s]
2025-12-13 19:30:36,830 - __main__ - INFO -       Completed in 22786ms
2025-12-13 19:30:36,830 - __main__ - INFO -     Turn 4
[Cache Store] Response cached. Cache size: 3
[Node] check_similarity
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 13.76it/s]
2025-12-13 19:30:36,923 - extraction.neural_translator - INFO - [NeuralTranslator] 한영 번역 모델 로딩: Helsinki-NLP/opus-mt-ko-en
Device set to use cpu
2025-12-13 19:30:42,423 - extraction.neural_translator - INFO - [NeuralTranslator] 한영 번역 모델 로드 완료
2025-12-13 19:30:42,423 - extraction.neural_translator - INFO - [NeuralTranslator] 영한 번역 모델 로딩: Helsinki-NLP/opus-mt-en-ko
2025-12-13 19:30:42,635 - extraction.neural_translator - ERROR - [NeuralTranslator] 번역 모델 로드 실패: Helsinki-NLP/opus-mt-en-ko is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth login` or by passing `token=<your_token>`
2025-12-13 19:30:42,651 - extraction.neural_translator - WARNING - [NeuralTranslator] 한영 번역기 로드 실패, 원본 반환
2025-12-13 19:30:42,659 - medcat.pipeline.pipeline - INFO - Running component tagging:tag-and-skip-tagger for 46 of text (1794233005696)
2025-12-13 19:30:42,660 - medcat.pipeline.pipeline - INFO - Running component token_normalizing:token_normalizer for 46 of text (1794233005696)
2025-12-13 19:30:42,661 - medcat.pipeline.pipeline - INFO - Running component ner:cat_ner for 46 of text (1794233005696)
2025-12-13 19:30:42,661 - medcat.pipeline.pipeline - INFO - Running component linking:medcat2_linker for 46 of text (1794233005696)
2025-12-13 19:30:43,044 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
Traceback (most recent call last):
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\retrieval\faiss_index.py", line 94, in search
    scores, indices = self.index.search(query_vec, k)
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\.venv\lib\site-packages\faiss\class_wrappers.py", line 383, in replacement_search
    assert d == self.d
AssertionError
2025-12-13 19:31:15,366 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:31:19,351 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
[Cache Miss] No similar question found in cache
[Node] classify_intent
[ERROR] classify_intent_node failed: 'NoneType' object has no attribute 'classify'
[Node] extract_slots
[Node] store_memory
[Node] assemble_context
[Node] retrieve
[BM25] 코퍼스 로드 완료: 15021개 문서
[FAISS] 인덱스 로드 완료: ./data/index/train_source/train_source_data.index.faiss
[FAISS] 메타데이터 로드 완료: 15021개 문서
[ERROR] FAISS 검색 실패:
[Node] assemble_context
[Node] generate_answer
[Node] refine (Strategy-based)
[Refine] 전략 선택: corrective_rag
[CORRECTIVE_RAG] Refine 수행 중...
[CORRECTIVE_RAG] 품질 점수: 0.78 (Iteration: 1)
[Node] quality_check (Strategy-based)
[Quality Check] 종료 (전략: corrective_rag, 점수: 0.78)
[Node] store_response
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00,  6.31it/s]
2025-12-13 19:31:19,973 - __main__ - INFO -       Completed in 43138ms
2025-12-13 19:31:19,973 - __main__ - INFO -     Turn 5
[Cache Store] Response cached. Cache size: 4
[Node] check_similarity
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00,  9.40it/s]
2025-12-13 19:31:20,109 - extraction.neural_translator - INFO - [NeuralTranslator] 한영 번역 모델 로딩: Helsinki-NLP/opus-mt-ko-en
Device set to use cpu
2025-12-13 19:31:24,789 - extraction.neural_translator - INFO - [NeuralTranslator] 한영 번역 모델 로드 완료
2025-12-13 19:31:24,789 - extraction.neural_translator - INFO - [NeuralTranslator] 영한 번역 모델 로딩: Helsinki-NLP/opus-mt-en-ko
2025-12-13 19:31:24,995 - extraction.neural_translator - ERROR - [NeuralTranslator] 번역 모델 로드 실패: Helsinki-NLP/opus-mt-en-ko is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth login` or by passing `token=<your_token>`
2025-12-13 19:31:25,016 - extraction.neural_translator - WARNING - [NeuralTranslator] 한영 번역기 로드 실패, 원본 반환
2025-12-13 19:31:25,082 - medcat.pipeline.pipeline - INFO - Running component tagging:tag-and-skip-tagger for 66 of text (1789645097664)
2025-12-13 19:31:25,084 - medcat.pipeline.pipeline - INFO - Running component token_normalizing:token_normalizer for 66 of text (1789645097664)
2025-12-13 19:31:25,084 - medcat.pipeline.pipeline - INFO - Running component ner:cat_ner for 66 of text (1789645097664)
2025-12-13 19:31:25,085 - medcat.pipeline.pipeline - INFO - Running component linking:medcat2_linker for 66 of text (1789645097664)
2025-12-13 19:31:25,576 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
Traceback (most recent call last):
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\retrieval\faiss_index.py", line 94, in search
    scores, indices = self.index.search(query_vec, k)
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\.venv\lib\site-packages\faiss\class_wrappers.py", line 383, in replacement_search
    assert d == self.d
AssertionError
2025-12-13 19:31:39,532 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:31:42,521 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
[Cache Miss] No similar question found in cache
[Node] classify_intent
[ERROR] classify_intent_node failed: 'NoneType' object has no attribute 'classify'
[Node] extract_slots
[Node] store_memory
[Node] assemble_context
[Node] retrieve
[BM25] 코퍼스 로드 완료: 12272개 문서
[FAISS] 인덱스 로드 완료: ./data/index/train_qa/train_questions.index.faiss
[FAISS] 메타데이터 로드 완료: 12272개 문서
[ERROR] FAISS 검색 실패:
[Node] assemble_context
[Node] generate_answer
[Node] refine (Strategy-based)
[Refine] 전략 선택: corrective_rag
[CORRECTIVE_RAG] Refine 수행 중...
[CORRECTIVE_RAG] 품질 점수: 0.78 (Iteration: 1)
[Node] quality_check (Strategy-based)
[Quality Check] 종료 (전략: corrective_rag, 점수: 0.78)
[Node] store_response
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 20.87it/s]
2025-12-13 19:31:42,671 - __main__ - INFO -       Completed in 22695ms
2025-12-13 19:31:42,671 - __main__ - INFO - Processing patient: SYN_0002
2025-12-13 19:31:42,676 - __main__ - INFO -   Mode: llm
2025-12-13 19:31:42,676 - __main__ - INFO -     Turn 1
2025-12-13 19:31:51,595 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:31:51,599 - __main__ - INFO -       Completed in 8919ms
2025-12-13 19:31:51,600 - __main__ - INFO -     Turn 2
2025-12-13 19:31:56,260 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:31:56,265 - __main__ - INFO -       Completed in 4664ms
2025-12-13 19:31:56,267 - __main__ - INFO -     Turn 3
2025-12-13 19:32:03,431 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:32:03,437 - __main__ - INFO -       Completed in 7168ms
2025-12-13 19:32:03,437 - __main__ - INFO -     Turn 4
2025-12-13 19:32:13,139 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:32:13,180 - __main__ - INFO -       Completed in 9740ms
2025-12-13 19:32:13,180 - __main__ - INFO -     Turn 5
2025-12-13 19:32:24,799 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:32:24,811 - __main__ - INFO -       Completed in 11623ms
2025-12-13 19:32:24,812 - __main__ - INFO -   Mode: agent
2025-12-13 19:32:24,813 - __main__ - INFO -     Turn 1
[Cache Store] Response cached. Cache size: 5
[Node] check_similarity
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00,  7.38it/s]
2025-12-13 19:32:25,033 - medcat.pipeline.pipeline - INFO - Running component tagging:tag-and-skip-tagger for 108 of text (1788039979072)
2025-12-13 19:32:25,033 - medcat.pipeline.pipeline - INFO - Running component token_normalizing:token_normalizer for 108 of text (1788039979072)
2025-12-13 19:32:25,037 - medcat.pipeline.pipeline - INFO - Running component ner:cat_ner for 108 of text (1788039979072)
2025-12-13 19:32:25,039 - medcat.pipeline.pipeline - INFO - Running component linking:medcat2_linker for 108 of text (1788039979072)
2025-12-13 19:32:25,760 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
Traceback (most recent call last):
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\retrieval\faiss_index.py", line 94, in search
    scores, indices = self.index.search(query_vec, k)
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\.venv\lib\site-packages\faiss\class_wrappers.py", line 383, in replacement_search
    assert d == self.d
AssertionError
2025-12-13 19:32:43,871 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:32:48,304 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:32:50,111 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:32:51,358 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
Traceback (most recent call last):
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\retrieval\faiss_index.py", line 94, in search
    scores, indices = self.index.search(query_vec, k)
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\.venv\lib\site-packages\faiss\class_wrappers.py", line 383, in replacement_search
    assert d == self.d
AssertionError
2025-12-13 19:33:11,194 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:33:17,574 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:33:19,330 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
[Cache Miss] No similar question found in cache
[Node] classify_intent
[ERROR] classify_intent_node failed: 'NoneType' object has no attribute 'classify'
[Node] extract_slots
[Node] store_memory
[Node] assemble_context
[Node] retrieve
[BM25] 코퍼스 로드 완료: 15021개 문서
[FAISS] 인덱스 로드 완료: ./data/index/train_source/train_source_data.index.faiss
[FAISS] 메타데이터 로드 완료: 15021개 문서
[ERROR] FAISS 검색 실패:
[Node] assemble_context
[Node] generate_answer
[Node] refine (Strategy-based)
[Refine] 전략 선택: corrective_rag
[CORRECTIVE_RAG] Refine 수행 중...
[CORRECTIVE_RAG] 품질 점수: 0.40 (Iteration: 1)
[CORRECTIVE_RAG] 질의 재작성: 64세 여성, 'Risk activity involvement' 병력과 아세트아미노펜 복용 중인 환자가 3일간 가슴 답답함을 경험했습니다. 이 증상의 원인 분석, 아세트아미노펜의 ...
[Node] quality_check (Strategy-based)
[Quality Check] 재검색 수행 (전략: corrective_rag, 점수: 0.40, iteration: 1)
[Node] retrieve
[BM25] 코퍼스 로드 완료: 15021개 문서
[FAISS] 인덱스 로드 완료: ./data/index/train_source/train_source_data.index.faiss
[FAISS] 메타데이터 로드 완료: 15021개 문서
[ERROR] FAISS 검색 실패:
[Node] assemble_context
[Node] generate_answer
[Node] refine (Strategy-based)
[Refine] 전략 선택: corrective_rag
[CORRECTIVE_RAG] Refine 수행 중...
[CORRECTIVE_RAG] 품질 점수: 0.40 (Iteration: 2)
[CORRECTIVE_RAG] 질의 재작성: 64세 여성, Risk activity involvement 병력, Acetaminophen 복용 중. 최근 3일간 가슴 답답함을 겪고 있습니다. 현재 건강 상태, Acetamin...
[Node] quality_check (Strategy-based)
[CORRECTIVE_RAG] 품질 개선 없음: 조기 종료
[Quality Check] 종료 (전략: corrective_rag, 점수: 0.40)
[Node] store_response
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 18.70it/s]
2025-12-13 19:33:20,255 - __main__ - INFO -       Completed in 55437ms
2025-12-13 19:33:20,255 - __main__ - INFO -     Turn 2
[Cache Store] Response cached. Cache size: 6
[Node] check_similarity
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 15.13it/s]
2025-12-13 19:33:20,349 - extraction.neural_translator - INFO - [NeuralTranslator] 한영 번역 모델 로딩: Helsinki-NLP/opus-mt-ko-en
Device set to use cpu
2025-12-13 19:33:23,222 - extraction.neural_translator - INFO - [NeuralTranslator] 한영 번역 모델 로드 완료
2025-12-13 19:33:23,223 - extraction.neural_translator - INFO - [NeuralTranslator] 영한 번역 모델 로딩: Helsinki-NLP/opus-mt-en-ko
2025-12-13 19:33:23,430 - extraction.neural_translator - ERROR - [NeuralTranslator] 번역 모델 로드 실패: Helsinki-NLP/opus-mt-en-ko is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth login` or by passing `token=<your_token>`
2025-12-13 19:33:23,453 - extraction.neural_translator - WARNING - [NeuralTranslator] 한영 번역기 로드 실패, 원본 반환
2025-12-13 19:33:23,490 - medcat.pipeline.pipeline - INFO - Running component tagging:tag-and-skip-tagger for 46 of text (1789066131600)
2025-12-13 19:33:23,491 - medcat.pipeline.pipeline - INFO - Running component token_normalizing:token_normalizer for 46 of text (1789066131600)
2025-12-13 19:33:23,491 - medcat.pipeline.pipeline - INFO - Running component ner:cat_ner for 46 of text (1789066131600)
2025-12-13 19:33:23,491 - medcat.pipeline.pipeline - INFO - Running component linking:medcat2_linker for 46 of text (1789066131600)
2025-12-13 19:33:23,983 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
Traceback (most recent call last):
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\retrieval\faiss_index.py", line 94, in search
    scores, indices = self.index.search(query_vec, k)
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\.venv\lib\site-packages\faiss\class_wrappers.py", line 383, in replacement_search
    assert d == self.d
AssertionError
2025-12-13 19:33:46,551 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:33:49,354 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
[Cache Miss] No similar question found in cache
[Node] classify_intent
[ERROR] classify_intent_node failed: 'NoneType' object has no attribute 'classify'
[Node] extract_slots
[Node] store_memory
[Node] assemble_context
[Node] retrieve
[BM25] 코퍼스 로드 완료: 12272개 문서
[FAISS] 인덱스 로드 완료: ./data/index/train_qa/train_questions.index.faiss
[FAISS] 메타데이터 로드 완료: 12272개 문서
[ERROR] FAISS 검색 실패:
[Node] assemble_context
[Node] generate_answer
[Node] refine (Strategy-based)
[Refine] 전략 선택: corrective_rag
[CORRECTIVE_RAG] Refine 수행 중...
[CORRECTIVE_RAG] 품질 점수: 0.82 (Iteration: 1)
[Node] quality_check (Strategy-based)
[Quality Check] 종료 (전략: corrective_rag, 점수: 0.82)
[Node] store_response
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 27.62it/s]
2025-12-13 19:33:49,485 - __main__ - INFO -       Completed in 29226ms
2025-12-13 19:33:49,485 - __main__ - INFO -     Turn 3
[Cache Store] Response cached. Cache size: 7
[Node] check_similarity
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 11.56it/s]
2025-12-13 19:33:49,601 - extraction.neural_translator - INFO - [NeuralTranslator] 한영 번역 모델 로딩: Helsinki-NLP/opus-mt-ko-en
Device set to use cpu
2025-12-13 19:33:52,299 - extraction.neural_translator - INFO - [NeuralTranslator] 한영 번역 모델 로드 완료
2025-12-13 19:33:52,299 - extraction.neural_translator - INFO - [NeuralTranslator] 영한 번역 모델 로딩: Helsinki-NLP/opus-mt-en-ko
2025-12-13 19:33:52,517 - extraction.neural_translator - ERROR - [NeuralTranslator] 번역 모델 로드 실패: Helsinki-NLP/opus-mt-en-ko is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth login` or by passing `token=<your_token>`
2025-12-13 19:33:52,539 - extraction.neural_translator - WARNING - [NeuralTranslator] 한영 번역기 로드 실패, 원본 반환
2025-12-13 19:33:52,587 - medcat.pipeline.pipeline - INFO - Running component tagging:tag-and-skip-tagger for 73 of text (1789655332464)
2025-12-13 19:33:52,588 - medcat.pipeline.pipeline - INFO - Running component token_normalizing:token_normalizer for 73 of text (1789655332464)
2025-12-13 19:33:52,589 - medcat.pipeline.pipeline - INFO - Running component ner:cat_ner for 73 of text (1789655332464)
2025-12-13 19:33:52,589 - medcat.pipeline.pipeline - INFO - Running component linking:medcat2_linker for 73 of text (1789655332464)
2025-12-13 19:33:53,143 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
Traceback (most recent call last):
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\retrieval\faiss_index.py", line 94, in search
    scores, indices = self.index.search(query_vec, k)
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\.venv\lib\site-packages\faiss\class_wrappers.py", line 383, in replacement_search
    assert d == self.d
AssertionError
2025-12-13 19:34:01,478 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:34:04,426 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:34:05,537 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:34:05,918 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
Traceback (most recent call last):
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\retrieval\faiss_index.py", line 94, in search
    scores, indices = self.index.search(query_vec, k)
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\.venv\lib\site-packages\faiss\class_wrappers.py", line 383, in replacement_search
    assert d == self.d
AssertionError
2025-12-13 19:34:14,429 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:34:17,714 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
[Cache Miss] No similar question found in cache
[Node] classify_intent
[ERROR] classify_intent_node failed: 'NoneType' object has no attribute 'classify'
[Node] extract_slots
[Node] store_memory
[Node] assemble_context
[Node] retrieve
[BM25] 코퍼스 로드 완료: 12272개 문서
[FAISS] 인덱스 로드 완료: ./data/index/train_qa/train_questions.index.faiss
[FAISS] 메타데이터 로드 완료: 12272개 문서
[ERROR] FAISS 검색 실패:
[Node] assemble_context
[Node] generate_answer
[Node] refine (Strategy-based)
[Refine] 전략 선택: corrective_rag
[CORRECTIVE_RAG] Refine 수행 중...
[CORRECTIVE_RAG] 품질 점수: 0.44 (Iteration: 1)
[CORRECTIVE_RAG] 질의 재작성: 64세 여성 환자의 최근 수치와 증상에 대한 구체적인 정보를 포함하여, 가능한 원인 가설 3가지를 제시해 주세요....
[Node] quality_check (Strategy-based)
[Quality Check] 재검색 수행 (전략: corrective_rag, 점수: 0.44, iteration: 1)
[Node] retrieve
[BM25] 코퍼스 로드 완료: 12272개 문서
[FAISS] 인덱스 로드 완료: ./data/index/train_qa/train_questions.index.faiss
[FAISS] 메타데이터 로드 완료: 12272개 문서
[ERROR] FAISS 검색 실패:
[Node] assemble_context
[Node] generate_answer
[Node] refine (Strategy-based)
[Refine] 전략 선택: corrective_rag
[CORRECTIVE_RAG] Refine 수행 중...
[CORRECTIVE_RAG] 품질 점수: 0.68 (Iteration: 2)
[Node] quality_check (Strategy-based)
[Quality Check] 종료 (전략: corrective_rag, 점수: 0.68)
[Node] store_response
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 24.71it/s]
2025-12-13 19:34:17,950 - __main__ - INFO -       Completed in 28460ms
2025-12-13 19:34:17,951 - __main__ - INFO -     Turn 4
[Cache Store] Response cached. Cache size: 8
[Node] check_similarity
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 13.97it/s]
2025-12-13 19:34:18,132 - medcat.pipeline.pipeline - INFO - Running component tagging:tag-and-skip-tagger for 76 of text (1789041568832)
2025-12-13 19:34:18,132 - medcat.pipeline.pipeline - INFO - Running component token_normalizing:token_normalizer for 76 of text (1789041568832)
2025-12-13 19:34:18,135 - medcat.pipeline.pipeline - INFO - Running component ner:cat_ner for 76 of text (1789041568832)
2025-12-13 19:34:18,139 - medcat.pipeline.pipeline - INFO - Running component linking:medcat2_linker for 76 of text (1789041568832)
2025-12-13 19:34:19,448 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
Traceback (most recent call last):
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\retrieval\faiss_index.py", line 94, in search
    scores, indices = self.index.search(query_vec, k)
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\.venv\lib\site-packages\faiss\class_wrappers.py", line 383, in replacement_search
    assert d == self.d
AssertionError
2025-12-13 19:34:38,163 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:34:40,916 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
[Cache Miss] No similar question found in cache
[Node] classify_intent
[ERROR] classify_intent_node failed: 'NoneType' object has no attribute 'classify'
[Node] extract_slots
[Node] store_memory
[Node] assemble_context
[Node] retrieve
[BM25] 코퍼스 로드 완료: 15021개 문서
[FAISS] 인덱스 로드 완료: ./data/index/train_source/train_source_data.index.faiss
[FAISS] 메타데이터 로드 완료: 15021개 문서
[ERROR] FAISS 검색 실패:
[Node] assemble_context
[Node] generate_answer
[Node] refine (Strategy-based)
[Refine] 전략 선택: corrective_rag
[CORRECTIVE_RAG] Refine 수행 중...
[CORRECTIVE_RAG] 품질 점수: 0.78 (Iteration: 1)
[Node] quality_check (Strategy-based)
[Quality Check] 종료 (전략: corrective_rag, 점수: 0.78)
[Node] store_response
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 24.55it/s]
2025-12-13 19:34:41,277 - __main__ - INFO -       Completed in 23323ms
2025-12-13 19:34:41,278 - __main__ - INFO -     Turn 5
[Cache Store] Response cached. Cache size: 9
[Node] check_similarity
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 10.33it/s]
2025-12-13 19:34:41,403 - extraction.neural_translator - INFO - [NeuralTranslator] 한영 번역 모델 로딩: Helsinki-NLP/opus-mt-ko-en
Device set to use cpu
2025-12-13 19:34:44,088 - extraction.neural_translator - INFO - [NeuralTranslator] 한영 번역 모델 로드 완료
2025-12-13 19:34:44,089 - extraction.neural_translator - INFO - [NeuralTranslator] 영한 번역 모델 로딩: Helsinki-NLP/opus-mt-en-ko
2025-12-13 19:34:44,292 - extraction.neural_translator - ERROR - [NeuralTranslator] 번역 모델 로드 실패: Helsinki-NLP/opus-mt-en-ko is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth login` or by passing `token=<your_token>`
2025-12-13 19:34:44,309 - extraction.neural_translator - WARNING - [NeuralTranslator] 한영 번역기 로드 실패, 원본 반환
2025-12-13 19:34:44,371 - medcat.pipeline.pipeline - INFO - Running component tagging:tag-and-skip-tagger for 80 of text (1789041568832)
2025-12-13 19:34:44,372 - medcat.pipeline.pipeline - INFO - Running component token_normalizing:token_normalizer for 80 of text (1789041568832)
2025-12-13 19:34:44,372 - medcat.pipeline.pipeline - INFO - Running component ner:cat_ner for 80 of text (1789041568832)
2025-12-13 19:34:44,375 - medcat.pipeline.pipeline - INFO - Running component linking:medcat2_linker for 80 of text (1789041568832)
2025-12-13 19:34:44,999 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
Traceback (most recent call last):
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\retrieval\faiss_index.py", line 94, in search
    scores, indices = self.index.search(query_vec, k)
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\.venv\lib\site-packages\faiss\class_wrappers.py", line 383, in replacement_search
    assert d == self.d
AssertionError
2025-12-13 19:34:59,979 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:35:02,994 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
[Cache Miss] No similar question found in cache
[Node] classify_intent
[ERROR] classify_intent_node failed: 'NoneType' object has no attribute 'classify'
[Node] extract_slots
[Node] store_memory
[Node] assemble_context
[Node] retrieve
[BM25] 코퍼스 로드 완료: 12272개 문서
[FAISS] 인덱스 로드 완료: ./data/index/train_qa/train_questions.index.faiss
[FAISS] 메타데이터 로드 완료: 12272개 문서
[ERROR] FAISS 검색 실패:
[Node] assemble_context
[Node] generate_answer
[Node] refine (Strategy-based)
[Refine] 전략 선택: corrective_rag
[CORRECTIVE_RAG] Refine 수행 중...
[CORRECTIVE_RAG] 품질 점수: 0.86 (Iteration: 1)
[Node] quality_check (Strategy-based)
[Quality Check] 종료 (전략: corrective_rag, 점수: 0.86)
[Node] store_response
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 14.68it/s]
2025-12-13 19:35:03,166 - __main__ - INFO -       Completed in 21886ms
2025-12-13 19:35:03,167 - __main__ - INFO - Processing patient: SYN_0003
2025-12-13 19:35:03,174 - __main__ - INFO -   Mode: llm
2025-12-13 19:35:03,175 - __main__ - INFO -     Turn 1
2025-12-13 19:35:11,415 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:35:11,420 - __main__ - INFO -       Completed in 8242ms
2025-12-13 19:35:11,420 - __main__ - INFO -     Turn 2
2025-12-13 19:35:19,760 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:35:19,769 - __main__ - INFO -       Completed in 8347ms
2025-12-13 19:35:19,769 - __main__ - INFO -     Turn 3
2025-12-13 19:35:25,510 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:35:25,515 - __main__ - INFO -       Completed in 5742ms
2025-12-13 19:35:25,518 - __main__ - INFO -     Turn 4
2025-12-13 19:35:33,321 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:35:33,327 - __main__ - INFO -       Completed in 7804ms
2025-12-13 19:35:33,327 - __main__ - INFO -     Turn 5
2025-12-13 19:35:40,332 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:35:40,351 - __main__ - INFO -       Completed in 7022ms
2025-12-13 19:35:40,352 - __main__ - INFO -   Mode: agent
2025-12-13 19:35:40,352 - __main__ - INFO -     Turn 1
[Cache Store] Response cached. Cache size: 10
[Node] check_similarity
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 19.75it/s]
2025-12-13 19:35:40,496 - medcat.pipeline.pipeline - INFO - Running component tagging:tag-and-skip-tagger for 88 of text (1789038456880)
2025-12-13 19:35:40,496 - medcat.pipeline.pipeline - INFO - Running component token_normalizing:token_normalizer for 88 of text (1789038456880)
2025-12-13 19:35:40,498 - medcat.pipeline.pipeline - INFO - Running component ner:cat_ner for 88 of text (1789038456880)
2025-12-13 19:35:40,504 - medcat.pipeline.pipeline - INFO - Running component linking:medcat2_linker for 88 of text (1789038456880)
2025-12-13 19:35:41,654 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
Traceback (most recent call last):
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\retrieval\faiss_index.py", line 94, in search
    scores, indices = self.index.search(query_vec, k)
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\.venv\lib\site-packages\faiss\class_wrappers.py", line 383, in replacement_search
    assert d == self.d
AssertionError
2025-12-13 19:35:56,098 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:35:58,910 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
[Cache Miss] No similar question found in cache
[Node] classify_intent
[ERROR] classify_intent_node failed: 'NoneType' object has no attribute 'classify'
[Node] extract_slots
[Node] store_memory
[Node] assemble_context
[Node] retrieve
[BM25] 코퍼스 로드 완료: 15021개 문서
[FAISS] 인덱스 로드 완료: ./data/index/train_source/train_source_data.index.faiss
[FAISS] 메타데이터 로드 완료: 15021개 문서
[ERROR] FAISS 검색 실패:
[Node] assemble_context
[Node] generate_answer
[Node] refine (Strategy-based)
[Refine] 전략 선택: corrective_rag
[CORRECTIVE_RAG] Refine 수행 중...
[CORRECTIVE_RAG] 품질 점수: 0.78 (Iteration: 1)
[Node] quality_check (Strategy-based)
[Quality Check] 종료 (전략: corrective_rag, 점수: 0.78)
[Node] store_response
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 46.62it/s]
2025-12-13 19:35:59,162 - __main__ - INFO -       Completed in 18809ms
2025-12-13 19:35:59,163 - __main__ - INFO -     Turn 2
[Cache Store] Response cached. Cache size: 11
[Node] check_similarity
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 44.38it/s]
2025-12-13 19:35:59,202 - extraction.neural_translator - INFO - [NeuralTranslator] 한영 번역 모델 로딩: Helsinki-NLP/opus-mt-ko-en
Device set to use cpu
2025-12-13 19:36:01,329 - extraction.neural_translator - INFO - [NeuralTranslator] 한영 번역 모델 로드 완료
2025-12-13 19:36:01,334 - extraction.neural_translator - INFO - [NeuralTranslator] 영한 번역 모델 로딩: Helsinki-NLP/opus-mt-en-ko
2025-12-13 19:36:01,570 - extraction.neural_translator - ERROR - [NeuralTranslator] 번역 모델 로드 실패: Helsinki-NLP/opus-mt-en-ko is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth login` or by passing `token=<your_token>`
2025-12-13 19:36:01,575 - extraction.neural_translator - WARNING - [NeuralTranslator] 한영 번역기 로드 실패, 원본 반환
2025-12-13 19:36:01,596 - medcat.pipeline.pipeline - INFO - Running component tagging:tag-and-skip-tagger for 55 of text (1794344186864)
2025-12-13 19:36:01,596 - medcat.pipeline.pipeline - INFO - Running component token_normalizing:token_normalizer for 55 of text (1794344186864)
2025-12-13 19:36:01,596 - medcat.pipeline.pipeline - INFO - Running component ner:cat_ner for 55 of text (1794344186864)
2025-12-13 19:36:01,597 - medcat.pipeline.pipeline - INFO - Running component linking:medcat2_linker for 55 of text (1794344186864)
2025-12-13 19:36:01,953 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
Traceback (most recent call last):
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\retrieval\faiss_index.py", line 94, in search
    scores, indices = self.index.search(query_vec, k)
  File "C:\Users\KHIDI\Downloads\medical_ai_agent_minimal\.venv\lib\site-packages\faiss\class_wrappers.py", line 383, in replacement_search
    assert d == self.d
AssertionError
2025-12-13 19:36:13,904 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-13 19:36:17,117 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
[Cache Miss] No similar question found in cache
[Node] classify_intent
[ERROR] classify_intent_node failed: 'NoneType' object has no attribute 'classify'
[Node] extract_slots
[Node] store_memory
[Node] assemble_context
[Node] retrieve
[BM25] 코퍼스 로드 완료: 12272개 문서
[FAISS] 인덱스 로드 완료: ./data/index/train_qa/train_questions.index.faiss
[FAISS] 메타데이터 로드 완료: 12272개 문서
[ERROR] FAISS 검색 실패:
[Node] assemble_context
[Node] generate_answer
[Node] refine (Strategy-based)
[Refine] 전략 선택: corrective_rag
[CORRECTIVE_RAG] Refine 수행 중...
[CORRECTIVE_RAG] 품질 점수: 0.78 (Iteration: 1)
[Node] quality_check (Strategy-based)
[Quality Check] 종료 (전략: corrective_rag, 점수: 0.78)
[Node] store_response
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 60.52it/s]
2025-12-13 19:36:17,194 - __main__ - INFO -       Completed in 18024ms
2025-12-13 19:36:17,194 - __main__ - INFO -     Turn 3
[Cache Store] Response cached. Cache size: 12
[Node] check_similarity
Batches: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 36.90it/s]
2025-12-13 19:36:17,239 - extraction.neural_translator - INFO - [NeuralTranslator] 한영 번역 모델 로딩: Helsinki-NLP/opus-mt-ko-en
Device set to use cpu