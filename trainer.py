import pandas as pd
import os

class Trainer:
    def __init__(self, brain_instance, learner_file='data/learned_knowledge.csv'):
        self.brain = brain_instance
        self.learner_file = learner_file
        self._ensure_learner_file_exists()

    def _ensure_learner_file_exists(self):
        if not os.path.exists(self.learner_file):
            columns = ['category', 'question', 'answer', 'difficulty', 'grade_level', 'source', 'keyword_tag']
            df = pd.DataFrame(columns=columns)
            df.to_csv(self.learner_file, index=False)

    def add_knowledge(self, category, question, answer, base_data_frames):
        new_data = pd.DataFrame({
            'category': [category],
            'question': [question],
            'answer': [answer],
            'difficulty': ['Custom'],
            'grade_level': ['Any'],
            'source': ['Manual Training'],
            'keyword_tag': ['']
        })
        
        new_data.to_csv(self.learner_file, mode='a', header=False, index=False)
        
        df_learned = pd.read_csv(self.learner_file)
        all_data = base_data_frames + [df_learned]
        
        self.brain.load_and_train(all_data)
        return True