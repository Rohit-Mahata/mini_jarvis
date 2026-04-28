import pickle
import pandas as pd
import requests
from sentence_transformers import SentenceTransformer, util
import re

class UnifiedBrain:
    # Upgraded model for much higher accuracy
    def __init__(self, model_name='all-mpnet-base-v2'):
        self.model = SentenceTransformer(model_name)
        self.knowledge_base = []
        self.embeddings = None

    def load_and_train(self, data_frames):
        clean_dfs = []
        for df in data_frames:
            if 'category.1' in df.columns:
                df = df.rename(columns={'category.1': 'question'})
            if 's_no' in df.columns:
                df = df.drop(columns=['s_no'])
            clean_dfs.append(df)

        combined_df = pd.concat(clean_dfs, ignore_index=True)
        self.knowledge_base = combined_df.to_dict('records')
        
        questions = combined_df['question'].astype(str).tolist()
        self.embeddings = self.model.encode(questions, convert_to_tensor=True)
        
        with open('model/embeddings.pkl', 'wb') as f:
            pickle.dump((self.knowledge_base, self.embeddings), f)

    def load_existing_brain(self):
        with open('model/embeddings.pkl', 'rb') as f:
            self.knowledge_base, self.embeddings = pickle.load(f)

    def evaluate_math(self, query):
        cleaned_query = re.sub(r'[^0-9+\-*/(). ]', '', query)
        if any(char.isdigit() for char in cleaned_query) and any(op in cleaned_query for op in '+-*/'):
            try:
                result = eval(cleaned_query)
                return f"The calculated result is {result}"
            except:
                return None
        return None

    def ask_ollama(self, query):
        """Fallback to Ollama Mistral when CSV has no match."""
        for attempt in range(2):
            try:
                response = requests.post(
                    'http://localhost:11434/api/generate',
                    json={
                        "model": "mistral:7b",
                        "prompt": query,
                        "stream": False
                    },
                    timeout=120
                )
                data = response.json()
                result = data.get('response', '').strip()
                if result:
                    return result
            except requests.exceptions.Timeout:
                print(f"[Brain] Ollama timeout (attempt {attempt + 1}/2)")
                continue
            except Exception as e:
                print(f"[Brain] Ollama error: {e}")
                break
        return "I'm having trouble connecting to my brain right now."

    # Threshold raised back to 0.60 because the upgraded model is more precise
    def get_answer(self, user_query, threshold=0.60):
        # 1. Check math first
        math_result = self.evaluate_math(user_query)
        if math_result:
            return math_result

        # 2. Check CSV knowledge base
        if self.embeddings is not None and len(self.knowledge_base) > 0:
            try:
                query_embedding = self.model.encode(user_query, convert_to_tensor=True)
                hits = util.semantic_search(query_embedding, self.embeddings, top_k=1)
                
                if hits and hits[0]:
                    best_hit = hits[0][0]
                    matched_q = self.knowledge_base[best_hit['corpus_id']]['question']
                    print(f"Intent Match: '{matched_q}' | Confidence Score: {best_hit['score']:.2f}")
                    
                    if best_hit['score'] >= threshold:
                        return self.knowledge_base[best_hit['corpus_id']]['answer']
            except Exception as e:
                print(f"[Brain CSV Error]: {str(e)}")

        # 3. Fall back to Ollama Mistral
        return self.ask_ollama(user_query)