import argparse
import readline

import language
import sentence2vec

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import GoogleCredentials
from termcolor import colored


PROJECT_ID = "reddit-1239"

TABLE_NAME = "%s:reddit_subset.posts_with_responses_sc_cnt_norm" % PROJECT_ID

FIELD_NAMES = ["question", "answer", "count", "score"]

MAX_RESULTS_PER_QUESTION = 30


def sql_contains_word(field_name, word):
    return ' ((%s CONTAINS "%s ") OR (%s CONTAINS " %s"))' % (field_name, word, field_name, word)


def generate_sql(table_name, question_words, only_question_answers):
    sql = ' '.join([
        'SELECT * FROM [%s] WHERE' % table_name,
        ' AND '.join([sql_contains_word('post_title_lower', word) for word in question_words]),
        'AND response_body_lower != "[deleted]"',
        'AND RIGHT(RTRIM(response_body_lower), 1) = "?"' if only_question_answers else '',
        'ORDER BY cnt LIMIT 10000;'
    ])
    return sql


def execute_query(bigquery, sql):
    try:
        query_data = { 'query': sql }
        query_request = bigquery.jobs()
        query_response = query_request.query(
            projectId=PROJECT_ID,
            body=query_data).execute()
    except HttpError as err:
        print('Error: {}'.format(err.content))
        raise err
    else:
        return query_response    


def retrieve_answers(bigquery, question, only_question_answers=False):
    words = language.filter_stopwords(language.sentence_to_words(question))
    sql = generate_sql(TABLE_NAME, words, only_question_answers)
    query_response = execute_query(bigquery, sql)
    results = []    
    if 'rows' not in query_response:
        return []
    for row in query_response['rows']:
        result = {
            "is_nasty": False
        }
        for (field_name, field) in zip(FIELD_NAMES, row['f']):
            value = language.clean(field['v'])
            result["is_nasty"] = language.is_nasty(value) or result["is_nasty"]
            result[field_name] = value
        result["question_match"] = sentence2vec.similarity(question, result["question"])
        if (not result["is_nasty"]) and result["question_match"] > -.4:
            results.append(result)
    return results


def sort_score(result):
    # TODO: adjust parameters
    return -(result["question_match"] + max(float(result["score"]) / 500.0, .2))


def print_results(question, results):
    for result in sorted(results, key=sort_score)[:MAX_RESULTS_PER_QUESTION]:
        answer = colored(result['answer'], 'yellow')
        question = result['question']
        question_match = colored("{0:.2f}".format(round(result['question_match'], 2)), 'green')
        score = colored(result['score'], 'red')
        print "".join(["=> ", answer, " (", question, ") ", question_match, ' ', score])


def interactive_loop(bigquery, only_question_answers):
    while True:
        try:
            question = raw_input('?> ')
            results = retrieve_answers(bigquery, question, only_question_answers)
        except KeyboardInterrupt:
            break
        else:
            print_results(question, results)
            print
    

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", help="only show follow-up questions", action="store_true")
    args = parser.parse_args()    
    credentials = GoogleCredentials.get_application_default()
    bigquery = build('bigquery', 'v2', credentials=credentials)
    interactive_loop(bigquery, only_question_answers=args.questions)


if __name__ == '__main__':
    main()
