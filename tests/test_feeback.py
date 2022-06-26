import datetime

from analysis.feedback.fb_source import flatten_feedback_dict

VOTE_TO_TEST = {
    'subjectId': 'Programación',
    'duration': 2,
    'date': datetime.datetime(2022, 4, 26, 23, 54, 38, 506642),
    'room': '3104',
    'votingTuple': [
        {'reasonsString': 'Con hambre o sed',
         'score': 1,
         'reasonsList': ['Con hambre o sed'],
         'category': 'Estado físico'},
        {'reasonsString': 'Motivado/a',
         'score': 5,
         'reasonsList': ['Motivado/a'],
         'category': 'Estado anímico'},
        {'reasonsString': 'Poco práctico',
         'score': 3,
         'reasonsList': ['Poco práctico'],
         'category': 'Temario'},
        {'reasonsString': 'Poco dinamismo',
         'score': 1,
         'reasonsList': ['Poco dinamismo'],
         'category': 'Docente'},
        {'reasonsString': 'Demasiado ruido',
         'score': 1,
         'reasonsList': ['Demasiado ruido'],
         'category': 'Ambiente'}
    ]
}


def test_spawn_generator_feedback_keyvalue_from_dict():
    res = list(flatten_feedback_dict(VOTE_TO_TEST))

    assert len(res) == len(VOTE_TO_TEST['votingTuple'])
    assert res[0].get('room', None) == VOTE_TO_TEST['room']
    assert res[0].get('category', None) in list(map(lambda e: e.get('category'), VOTE_TO_TEST['votingTuple']))

