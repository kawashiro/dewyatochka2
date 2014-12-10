# -*- coding: UTF-8

"""
Plugins back ported from version 1.0
"""

__all__ = ['mail_ru_question']

from dewyatochka.core import plugin, http
import json
import random

# Cached questions list
_mail_ru_questions_cache = []


@plugin.chat_entry
def mail_ru_question(message: dict, **kwargs) -> str:
    """
    Perl code:
        sub MrQuestion
        {
            if (!@questions) {
                # TODO: Move questions category to the config
                my $json = get 'http://otvet.mail.ru/api/v2/questlist?n=100&state=A&cat=adult';
                my @question_refs = @{${decode_json $json}{qst}};
                foreach my $question_ref (@question_refs) {
                    push(@questions, ${$question_ref}{qtext});
                }
            }
            if (@questions) {
                &say(shift @questions);
            }
        }
    :param message: dict
    :param kwargs: dict
    :return: str
    """
    if kwargs['conference'].member == message['from'].resource:
        return None

    if not message['body'].startswith('!talk'):
        return None

    if not _mail_ru_questions_cache:
        response = http.Client('otvet.mail.ru').get('/api/v2/questlist?n=100&state=A&cat=adult')
        questions = [question['qtext'] for question in json.loads(response).get('qst', [])]
        if questions:
            _mail_ru_questions_cache.extend(questions)
        else:
            return None

    return _mail_ru_questions_cache.pop(random.randint(0, len(_mail_ru_questions_cache) - 1))
