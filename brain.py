import pickle
import pandas as pd
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

    # Threshold raised back to 0.60 because the upgraded model is more precise
    def get_answer(self, user_query, threshold=0.60):
        math_result = self.evaluate_math(user_query)
        if math_result:
            return math_result

        if self.embeddings is None or len(self.knowledge_base) == 0:
            return "My database is completely empty. I have nothing to search!"
            
        try:
            query_embedding = self.model.encode(user_query, convert_to_tensor=True)
            hits = util.semantic_search(query_embedding, self.embeddings, top_k=1)
            
            if not hits or not hits[0]:
                return None
                
            best_hit = hits[0][0]
            matched_q = self.knowledge_base[best_hit['corpus_id']]['question']
            print(f"Intent Match: '{matched_q}' | Confidence Score: {best_hit['score']:.2f}")
            
            if best_hit['score'] >= threshold:
                return self.knowledge_base[best_hit['corpus_id']]['answer']
            return None
        except Exception as e:
            return f"[Brain Error]: {str(e)}"