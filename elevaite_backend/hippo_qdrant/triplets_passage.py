import json
import pandas as pd
from typing import List, Dict, Any
from hippo_config import HippoRAGConfig
import logging

logger = logging.getLogger(__name__)

class TripletToPassageConverter:
    """Converts triplets to natural language passages"""
    
    def __init__(self, config: HippoRAGConfig):
        self.config = config
    
    def triplet_to_passage(self, subject: str, predicate: str, object_val: str) -> str:
        """Convert a single triplet to a natural language passage"""
        # Clean and format the triplet components
        subject = str(subject).strip()
        predicate = str(predicate).strip()
        object_val = str(object_val).strip()
        
        # Create a natural language sentence
        # Handle different predicate patterns --TODO
        if predicate.lower() in ['has', 'have']:
            passage = f"{subject} has {object_val}."
        elif predicate.lower() in ['is', 'are']:
            passage = f"{subject} is {object_val}."
        elif predicate.lower() in ['located_in', 'located in']:
            passage = f"{subject} is located in {object_val}."
        elif predicate.lower() in ['type_of', 'type of']:
            passage = f"{subject} is a type of {object_val}."
        elif predicate.lower() in ['belongs_to', 'belongs to']:
            passage = f"{subject} belongs to {object_val}."
        else:
            # Generic format for other predicates
            passage = f"{subject} {predicate} {object_val}."
        
        return passage
    
    def convert_triplets_to_passages(self, triplets_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert all triplets to passages with metadata"""
        passages = []
        
        for idx, row in triplets_df.iterrows():
            try:
                # Extract triplet components (adjust column names as needed)
                if 'subject' in row and 'predicate' in row and 'object' in row:
                    subject = row['subject']
                    predicate = row['predicate']
                    object_val = row['object']
                elif len(row) >= 3:
                    subject = row.iloc[0]
                    predicate = row.iloc[1]
                    object_val = row.iloc[2]
                else:
                    logger.warning(f"Row {idx} doesn't have enough columns for triplet")
                    continue
                
                # Convert to passage
                passage_text = self.triplet_to_passage(subject, predicate, object_val)
                
                # Create passage metadata
                passage_data = {
                    'id': f"passage_{idx}",
                    'text': passage_text,
                    'subject': subject,
                    'predicate': predicate,
                    'object': object_val,
                    'triplet_id': idx,
                    'entities': [subject, object_val],  
                    'facts': [f"{subject}_{predicate}_{object_val}"]
                }
                
                passages.append(passage_data)
                
            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
                continue
        
        logger.info(f"Converted {len(passages)} triplets to passages")
        return passages
    
    def save_passages(self, passages: List[Dict[str, Any]], filename: str = None):
        """Save passages to JSON file"""
        if filename is None:
            filename = self.config.PASSAGES_FILE
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(passages, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(passages)} passages to {filename}")
        except Exception as e:
            logger.error(f"Error saving passages: {e}")
            raise
    
    def load_passages(self, filename: str = None) -> List[Dict[str, Any]]:
        """Load passages from JSON file"""
        if filename is None:
            filename = self.config.PASSAGES_FILE
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                passages = json.load(f)
            logger.info(f"Loaded {len(passages)} passages from {filename}")
            return passages
        except Exception as e:
            logger.error(f"Error loading passages: {e}")
            raise

def main():
    """Main execution function"""
    # Initialize configuration
    config = HippoRAGConfig()
    converter = TripletToPassageConverter(config)
    
    # Load triplets
    triplets_df = config.load_triplets()
    
    # Convert triplets to passages
    passages = converter.convert_triplets_to_passages(triplets_df)
    
    # Save passages
    converter.save_passages(passages)
    
    return passages
