import csv
import analysis.config as cfg
import analysis.feedback.fb_source as fb

def bulk_to_file(filename: str) -> None:
    fb_client = fb.get_firestore_db_client()
    docRef_feedbacks = fb_client.collection(cfg.get_config().datasources.feedbacks.collection).stream()
    with open(filename, 'w') as f:
        writer = csv.DictWriter(f, fb.FlattenVoteFieldsList, quoting=csv.QUOTE_NONNUMERIC)
        writer.writeheader()
        for docRef in docRef_feedbacks:
            all_feedbacks = fb.flatten_feedback_dict(docRef.to_dict())
            writer.writerows(all_feedbacks)
        
if __name__ == '__main__':
    bulk_to_file('./all_feedbacks.csv')
